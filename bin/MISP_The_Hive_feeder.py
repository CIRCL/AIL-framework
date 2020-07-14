#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
module
====================

This module send tagged pastes to MISP or THE HIVE Project

"""
import os
import sys
import uuid
import redis
import time
import json

from pubsublogger import publisher
from Helper import Process
from packages import Paste
import ailleakObject

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Tag

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader
import item_basic

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



def create_the_hive_alert(source, item_id, tag):
    # # TODO: check items status (processed by all modules)
    # # TODO: add item metadata: decoded content, link to auto crawled content, pgp correlation, cryptocurrency correlation...
    # # # TODO: description, add AIL link:show items ?
    tags = list( r_serv_metadata.smembers('tag:{}'.format(item_id)) )

    artifacts = [
        AlertArtifact( dataType='uuid-ail', data=r_serv_db.get('ail:uuid') ),
        AlertArtifact( dataType='file', data=item_id, tags=tags )
    ]

    # Prepare the sample Alert
    sourceRef = str(uuid.uuid4())[0:6]
    alert = Alert(title='AIL Leak',
                  tlp=3,
                  tags=tags,
                  description='AIL Leak, triggered by {}'.format(tag),
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

def feeder(message, count=0):

    if flag_the_hive or flag_misp:
        tag, item_id = message.split(';')

        ## FIXME: remove it
        if not item_basic.exist_item(item_id):
            if count < 10:
                r_serv_db.zincrby('mess_not_saved_export', message, 1)
                return 0
            else:
                r_serv_db.zrem('mess_not_saved_export', message)
                print('Error: {} do not exist, tag= {}'.format(item_id, tag))
                return 0

        source = item_basic.get_source(item_id)

        if HiveApi != False:
            if int(r_serv_db.get('hive:auto-alerts')) == 1:
                if r_serv_db.sismember('whitelist_hive', tag):
                    create_the_hive_alert(source, item_id, tag)
            else:
                print('hive, auto alerts creation disable')
        if flag_misp:
            if int(r_serv_db.get('misp:auto-events')) == 1:
                if r_serv_db.sismember('whitelist_misp', tag):
                    misp_wrapper.pushToMISP(uuid_ail, item_id, tag)
            else:
                print('misp, auto events creation disable')


if __name__ == "__main__":

    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'MISP_The_hive_feeder'

    config_loader = ConfigLoader.ConfigLoader()

    r_serv_db = config_loader.get_redis_conn("ARDB_DB")
    r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")

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
            #try:
            misp_wrapper = ailleakObject.ObjectWrapper(pymisp)
            r_serv_db.set('ail:misp', True)
            print('Connected to MISP:', misp_url)
            #except Exception as e:
            #    flag_misp = False
            #    r_serv_db.set('ail:misp', False)
            #    print(e)
            #    print('Not connected to MISP')

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

    refresh_time = 3
    ## FIXME: remove it
    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes"))
    config_loader = None

    time_1 = time.time()

    while True:

        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:

            # handle not saved pastes
            if int(time.time() - time_1) > refresh_time:

                num_queu = r_serv_db.zcard('mess_not_saved_export')
                list_queu = r_serv_db.zrange('mess_not_saved_export', 0, -1,  withscores=True)

                if num_queu and list_queu:
                    for i in range(0, num_queu):
                        feeder(list_queu[i][0],list_queu[i][1])

                time_1 = time.time()
            else:
                publisher.debug("{} queue is empty, waiting 1s".format(config_section))
                time.sleep(1)
        else:
            feeder(message)
