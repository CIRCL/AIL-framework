#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis
from uuid import uuid4

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader

## LOAD CONFIG ##
config_loader = ConfigLoader.ConfigLoader()
r_serv_cache = config_loader.get_redis_conn("Redis_Cache")
r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None
## -- ##

def get_ail_uuid():
    uuid_ail = r_serv_db.get('ail:uuid')
    if uuid_ail is None:
        uuid_ail = str(uuid4())
        r_serv_db.set('ail:uuid', uuid_ail)
    return uuid_ail

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

###########################################################
# # set default
# if r_serv_db.get('hive:auto-alerts') is None:
#     r_serv_db.set('hive:auto-alerts', 0)
#
# if r_serv_db.get('misp:auto-events') is None:
#     r_serv_db.set('misp:auto-events', 0)
