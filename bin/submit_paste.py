#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import configparser
import os
import sys
import gzip
import io
import redis
import base64
import datetime

from Helper import Process

def add_tags(tags, tagsgalaxies, path):
    list_tag = tags.split(',')
    list_tag_galaxies = tagsgalaxies.split(',')

    if list_tag != ['']:
        for tag in list_tag:
            #add tag
            r_serv_metadata.sadd('tag:'+path, tag)
            r_serv_tags.sadd(tag, path)
            #add new tag in list of all used tags
            r_serv_tags.sadd('list_tags', tag)

    if list_tag_galaxies != ['']:
        for tag in list_tag_galaxies:
            #add tag
            r_serv_metadata.sadd('tag:'+path, tag)
            r_serv_tags.sadd(tag, path)
            #add new tag in list of all used tags
            r_serv_tags.sadd('list_tags', tag)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print('usage:', 'submit_paste.py', 'ltags', 'ltagsgalaxies', 'paste_content', 'paste_name', 'id')
        exit(1)

    try:
        ltags = sys.argv[1]
        ltagsgalaxies = sys.argv[2]
        paste_content = sys.argv[3]
        paste_name = sys.argv[4]
        id = sys.argv[5]
    except:
        print('unable to get elements')
        exit(1)

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    r_serv_log_submit = redis.StrictRedis(
        host=cfg.get("Redis_Log_submit", "host"),
        port=cfg.getint("Redis_Log_submit", "port"),
        db=cfg.getint("Redis_Log_submit", "db"),
        decode_responses=True)

    r_serv_tags = redis.StrictRedis(
        host=cfg.get("ARDB_Tags", "host"),
        port=cfg.getint("ARDB_Tags", "port"),
        db=cfg.getint("ARDB_Tags", "db"),
        decode_responses=True)

    r_serv_metadata = redis.StrictRedis(
        host=cfg.get("ARDB_Metadata", "host"),
        port=cfg.getint("ARDB_Metadata", "port"),
        db=cfg.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    # TODO put on config
    expire_time = 10200

    r_serv_log_submit.expire(id + ':end', expire_time)
    r_serv_log_submit.expire(id + ':nb_total', expire_time)
    r_serv_log_submit.expire(id + ':nb_end', expire_time)
    r_serv_log_submit.expire(id + ':error', expire_time)

    config_section = 'submit_paste'
    p = Process(config_section)

    now = datetime.datetime.now()
    save_path = 'submitted/' + now.strftime("%Y") + '/' + now.strftime("%m") + '/' + now.strftime("%d") + '/' + id + '.gz'

    full_path = filename = os.path.join(os.environ['AIL_HOME'],
                            p.config.get("Directories", "pastes"), save_path)

    if os.path.isfile(full_path):
        error = r_serv_log_submit.get(id + ':error')
        r_serv_log_submit.set(id + ':error', error + '<br></br>File: ' + save_path + ' already exist in submitted pastes')
        exit(1)


    gzipencoded = gzip.compress(paste_content.encode())
    gzip64encoded = base64.standard_b64encode(gzipencoded).decode()

    # send paste to Global module
    relay_message = "{0} {1}".format(save_path, gzip64encoded)
    p.populate_set_out(relay_message, 'Mixer')

    # add tags
    add_tags(ltags, ltagsgalaxies, full_path)

    r_serv_log_submit.incr(id + ':nb_end')


    if r_serv_log_submit.get(id + ':nb_end') == r_serv_log_submit.get(id + ':nb_total'):
        r_serv_log_submit.set(id + ':end', 1)

    exit(0)
