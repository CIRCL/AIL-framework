#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
module
====================

This module send tagged pastes to MISP or THE HIVE Project

"""

import redis
import sys
import os
import time
import json
import configparser

from pubsublogger import publisher
from Helper import Process
from packages import Paste
import ailleakObject

import uuid

from pymisp import PyMISP

sys.path.append('../configs/keys')

# import MISP KEYS
try:
    from mispKEYS import misp_url, misp_key, misp_verifycert
    flag_misp = True
except:
    print('Misp keys not present')
    flag_misp = False

# import The Hive Keys
try:
    from theHiveKEYS import the_hive_url, the_hive_key
    flag_the_hive = True
except:
    print('The HIVE keys not present')
    flag_the_hive = False

from thehive4py.api import TheHiveApi
from thehive4py.models import Alert, AlertArtifact
from thehive4py.models import Case, CaseTask, CustomFieldHelper



def create_the_hive_alert(source, path, content, tag):
    tags = list(r_serv_metadata.smembers('tag:'+path))

    artifacts = [
        AlertArtifact( dataType='uuid-ail', data=r_serv_db.get('ail:uuid') ),
        AlertArtifact( dataType='file', data=path, tags=tags )
    ]

    l_tags = tag.split(',')
    print(tag)

    # Prepare the sample Alert
    sourceRef = str(uuid.uuid4())[0:6]
    alert = Alert(title='AIL Leak',
                  tlp=3,
                  tags=l_tags,
                  description='infoleak',
                  type='ail',
                  source=source,
                  sourceRef=sourceRef,
                  artifacts=artifacts)

    # Create the Alert
    id = None
    response = HiveApi.create_alert(alert)
    if response.status_code == 201:
        #print(json.dumps(response.json(), indent=4, sort_keys=True))
        print('Alert Created')
        print('')
        id = response.json()['id']
    else:
        print('ko: {}/{}'.format(response.status_code, response.text))
        return 0


if __name__ == "__main__":

    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'misp_the_hive_feeder'

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    r_serv_db = redis.StrictRedis(
        host=cfg.get("ARDB_DB", "host"),
        port=cfg.getint("ARDB_DB", "port"),
        db=cfg.getint("ARDB_DB", "db"),
        decode_responses=True)

    r_serv_metadata = redis.StrictRedis(
        host=cfg.get("ARDB_Metadata", "host"),
        port=cfg.getint("ARDB_Metadata", "port"),
        db=cfg.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    uuid_ail = r_serv_db.get('ail:uuid')
    if uuid_ail is None:
        uuid_ail = r_serv_db.set('ail:uuid', uuid.uuid4() )

    config_section = 'misp_the_hive_feeder'

    p = Process(config_section)
    # create MISP connection
    if flag_misp:
        #try:
        pymisp = PyMISP(misp_url, misp_key, misp_verifycert)
        misp_wrapper = ailleakObject.ObjectWrapper(pymisp)
        r_serv_db.set('ail:misp', True)
        print('Connected to MISP:', misp_url)
        #except:
            #flag_misp = False
            #print('Not connected to MISP')

    # create The HIVE connection
    if flag_the_hive:
        try:
            HiveApi = TheHiveApi(the_hive_url, the_hive_key)
            r_serv_db.set('ail:thehive', True)
            print('Connected to The HIVE:', the_hive_url)
        except:
            HiveApi = False
            print('Not connected to The HIVE')

    while True:

        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting 1s".format(config_section))
            time.sleep(1)
            continue
        else:

            if HiveApi or flag_misp:
                tag, path = message.split(';')
                paste = Paste.Paste(path)
                source = '/'.join(paste.p_path.split('/')[-6:])

                full_path = os.path.join(os.environ['AIL_HOME'],
                                        p.config.get("Directories", "pastes"), path)

                if HiveApi != False:
                    create_the_hive_alert(source, path, full_path, tag)

                if flag_misp:
                    misp_wrapper.pushToMISP(uuid_ail, path, tag)
