#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
from uuid import uuid4

sys.path.append(os.environ['AIL_BIN'])
from lib import ConfigLoader

sys.path.append('../../configs/keys')
try:
    from thehive4py.api import TheHiveApi
    import thehive4py.exceptions
    from theHiveKEYS import the_hive_url, the_hive_key, the_hive_verifycert
    if the_hive_url == '':
        is_hive_connected = False
    else:
        is_hive_connected = TheHiveApi(the_hive_url, the_hive_key, cert=the_hive_verifycert)
except:
    is_hive_connected = False
if is_hive_connected != False:
    try:
        is_hive_connected.get_alert(0)
        is_hive_connected = True
    except thehive4py.exceptions.AlertException:
        is_hive_connected = False

## LOAD CONFIG ##
config_loader = ConfigLoader.ConfigLoader()
r_serv_cache = config_loader.get_redis_conn("Redis_Cache")
r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None
## -- ##

def load_tags_to_export_in_cache():
    all_exports = ['misp', 'thehive']
    for export_target in all_exports:
        # save solo tags in cache
        all_tags_to_export = Tag.get_list_of_solo_tags_to_export_by_type()
        if len(all_tags_to_export) > 1:
            r_serv_cache.sadd('to_export:solo_tags:{}'.format(export_target), *all_tags_to_export)
        elif all_tags_to_export:
            r_serv_cache.sadd('to_export:solo_tags:{}'.format(export_target), all_tags_to_export[0])

        # save combinaison of tags in cache
        pass

def is_hive_connected(): # # TODO: REFRACTOR, put in cache (with retry)
    return is_hive_connected

def get_item_hive_cases(item_id):
    hive_case = r_serv_metadata.get('hive_cases:{}'.format(item_id))
    if hive_case:
        hive_case = the_hive_url + '/index.html#/case/{}/details'.format(hive_case)
    return hive_case


###########################################################
# # set default
# if r_serv_db.get('hive:auto-alerts') is None:
#     r_serv_db.set('hive:auto-alerts', 0)
#
# if r_serv_db.get('misp:auto-events') is None:
#     r_serv_db.set('misp:auto-events', 0)
