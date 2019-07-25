#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import redis

import Flask_config

r_serv_db = Flask_config.r_serv_db
r_serv_log = Flask_config.r_serv_log

def create_import_queue(ltags, ltagsgalaxies, paste_content, UUID,  password, isfile = False):

    # save temp value on disk
    r_serv_db.set(UUID + ':ltags', ltags)
    r_serv_db.set(UUID + ':ltagsgalaxies', ltagsgalaxies)
    r_serv_db.set(UUID + ':paste_content', paste_content)
    r_serv_db.set(UUID + ':password', password)
    r_serv_db.set(UUID + ':isfile', isfile)

    r_serv_log.set(UUID + ':end', 0)
    r_serv_log.set(UUID + ':processing', 0)
    r_serv_log.set(UUID + ':nb_total', -1)
    r_serv_log.set(UUID + ':nb_end', 0)
    r_serv_log.set(UUID + ':nb_sucess', 0)

    # save UUID on disk
    r_serv_db.sadd('submitted:uuid', UUID)
    return UUID

def import_text_item():
    res = r_serv_db.smembers('submitted:uuid')
    print(res)
    return res
