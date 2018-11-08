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
    from theHiveKEYS import the_hive_url, the_hive_key, the_hive_verifycert
    if the_hive_url == '':
        flag_the_hive = False
    else:
        flag_the_hive = True
except:
    print('The HIVE keys not present')
    flag_the_hive = False
    HiveApi = False

from thehive4py.api import TheHiveApi
import thehive4py.exceptions
from thehive4py.models import Alert, AlertArtifact
from thehive4py.models import Case, CaseTask, CustomFieldHelper



def create_the_hive_alert(source, path, tag):
    tags = list(r_serv_metadata.smembers('tag:'+path))

    artifacts = [
        AlertArtifact( dataType='uuid-ail', data=r_serv_db.get('ail:uuid') ),
        AlertArtifact( dataType='file', data=path, tags=tags )
    ]

    l_tags = tag.split(',')

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
    try:
        response = HiveApi.create_alert(alert)
        if response.status_code == 201:
            #print(json.dumps(response.json(), indent=4, sort_keys=True))
            print('Alert Created')
            print('')
            id = response.json()['id']
        else:
            print('ko: {}/{}'.format(response.status_code, response.text))
            return 0
    except:
        print('hive connection error')

if __name__ == "__main__":

    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'MISP_The_hive_feeder'

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

    # set sensor uuid
    uuid_ail = r_serv_db.get('ail:uuid')
    if uuid_ail is None:
        uuid_ail = r_serv_db.set('ail:uuid', uuid.uuid4() )

    # set default
    if r_serv_db.get('hive:auto-alerts') is None:
        r_serv_db.set('hive:auto-alerts', 0)

    if r_serv_db.get('misp:auto-events') is None:
        r_serv_db.set('misp:auto-events', 0)

    p = Process(config_section)
    # create MISP connection
    if flag_misp:
        try:
            pymisp = PyMISP(misp_url, misp_key, misp_verifycert)
        except:
            flag_misp = False
            r_serv_db.set('ail:misp', False)
            print('Not connected to MISP')

        if flag_misp:
            try:
                misp_wrapper = ailleakObject.ObjectWrapper(pymisp)
                r_serv_db.set('ail:misp', True)
                print('Connected to MISP:', misp_url)
            except e:
                flag_misp = False
                r_serv_db.set('ail:misp', False)
                print(e)
                print('Not connected to MISP')

    # create The HIVE connection
    if flag_the_hive:
        try:
            HiveApi = TheHiveApi(the_hive_url, the_hive_key, cert = the_hive_verifycert)
        except:
            HiveApi = False
            flag_the_hive = False
            r_serv_db.set('ail:thehive', False)
            print('Not connected to The HIVE')
    else:
        HiveApi = False

    if HiveApi != False and flag_the_hive:
        try:
            HiveApi.get_alert(0)
            r_serv_db.set('ail:thehive', True)
            print('Connected to The HIVE:', the_hive_url)
        except thehive4py.exceptions.AlertException:
            HiveApi = False
            flag_the_hive = False
            r_serv_db.set('ail:thehive', False)
            print('Not connected to The HIVE')

    ## FIXME: remove it
    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "pastes"))

    while True:

        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting 1s".format(config_section))
            time.sleep(1)
            continue
        else:

            if flag_the_hive or flag_misp:
                tag, path = message.split(';')
                ## FIXME: remove it
                if PASTES_FOLDER not in path:
                    path = os.path.join(PASTES_FOLDER, path)
                paste = Paste.Paste(path)
                source = '/'.join(paste.p_path.split('/')[-6:])

                if HiveApi != False:
                    if int(r_serv_db.get('hive:auto-alerts')) == 1:
                        whitelist_hive = r_serv_db.scard('whitelist_hive')
                        if r_serv_db.sismember('whitelist_hive', tag):
                            create_the_hive_alert(source, path, tag)
                    else:
                        print('hive, auto alerts creation disable')
                if flag_misp:
                    if int(r_serv_db.get('misp:auto-events')) == 1:
                        if r_serv_db.sismember('whitelist_misp', tag):
                            misp_wrapper.pushToMISP(uuid_ail, path, tag)
                    else:
                        print('misp, auto events creation disable')
