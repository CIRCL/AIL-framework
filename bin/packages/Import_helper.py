#!/usr/bin/env python3
# -*-coding:UTF-8 -*

##################################
# Import External packages
##################################
import os
import sys
import uuid

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader


config_loader = ConfigLoader.ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
r_serv_log_submit = config_loader.get_redis_conn("Redis_Log_submit")
config_loader = None


def is_valid_uuid_v4(UUID):
    UUID = UUID.replace('-', '')
    try:
        uuid_test = uuid.UUID(hex=UUID, version=4)
        return uuid_test.hex == UUID
    except:
        return False


def create_import_queue(tags, galaxy, paste_content, UUID, password=None, isfile=False, source=None):

    # save temp value on disk
    for tag in tags:
        r_serv_db.sadd(UUID + ':ltags', tag)
    for tag in galaxy:
        r_serv_db.sadd(UUID + ':ltagsgalaxies', tag)

    r_serv_db.set(UUID + ':paste_content', paste_content)

    if password:
        r_serv_db.set(UUID + ':password', password)
    
    if source:
        r_serv_db.set(UUID + ':source', source)

    r_serv_db.set(UUID + ':isfile', str(isfile))

    r_serv_log_submit.set(UUID + ':end', 0)
    r_serv_log_submit.set(UUID + ':processing', 0)
    r_serv_log_submit.set(UUID + ':nb_total', -1)
    r_serv_log_submit.set(UUID + ':nb_end', 0)
    r_serv_log_submit.set(UUID + ':nb_sucess', 0)

    # save UUID on disk
    r_serv_db.sadd('submitted:uuid', UUID)

    return UUID


def check_import_status(UUID):
    if not is_valid_uuid_v4(UUID):
        return {'status': 'error', 'reason': 'Invalid uuid'}, 400

    processing = r_serv_log_submit.get(UUID + ':processing')
    if not processing:
        return {'status': 'error', 'reason': 'Unknown uuid'}, 404

    # nb_total = r_serv_log_submit.get(UUID + ':nb_total')
    # nb_sucess = r_serv_log_submit.get(UUID + ':nb_sucess')
    # nb_end = r_serv_log_submit.get(UUID + ':nb_end')
    items_id = list(r_serv_log_submit.smembers(UUID + ':paste_submit_link'))
    error = r_serv_log_submit.get(UUID + ':error')
    end = r_serv_log_submit.get(UUID + ':end')

    dict_import_status = {}
    if items_id:
        dict_import_status['items'] = items_id
    if error:
        dict_import_status['error'] = error

    if processing == '0':
        status = 'in queue'
    else:
        if end == '0':
            status = 'in progress'
        else:
            status = 'imported'
    dict_import_status['status'] = status

    return dict_import_status, 200
