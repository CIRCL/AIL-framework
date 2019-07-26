#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import uuid
import redis

import Flask_config

r_serv_db = Flask_config.r_serv_db
r_serv_log_submit = Flask_config.r_serv_log_submit

def is_valid_uuid_v4(UUID):
    UUID = UUID.replace('-', '')
    try:
        uuid_test = uuid.UUID(hex=UUID, version=4)
        return uuid_test.hex == UUID
    except:
        return False

def create_import_queue(tags, galaxy, paste_content, UUID,  password=None, isfile = False):

    # save temp value on disk
    for tag in tags:
        r_serv_db.sadd(UUID + ':ltags', tag)
    for tag in galaxy:
        r_serv_db.sadd(UUID + ':ltagsgalaxies', tag)

    r_serv_db.set(UUID + ':paste_content', paste_content)

    if password:
        r_serv_db.set(UUID + ':password', password)

    r_serv_db.set(UUID + ':isfile', isfile)

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
        return ({'status': 'error', 'reason': 'Invalid uuid'}, 400)

    processing = r_serv_log_submit.get(UUID + ':processing')
    if not processing:
        return ({'status': 'error', 'reason': 'Unknow uuid'}, 400)

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

    return (dict_import_status, 200)
