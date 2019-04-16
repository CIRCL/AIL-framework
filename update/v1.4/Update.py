#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import datetime
import configparser

if __name__ == '__main__':

    start_deb = time.time()

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "pastes")) + '/'

    r_serv = redis.StrictRedis(
        host=cfg.get("ARDB_DB", "host"),
        port=cfg.getint("ARDB_DB", "port"),
        db=cfg.getint("ARDB_DB", "db"),
        decode_responses=True)

    r_serv_onion = redis.StrictRedis(
        host=cfg.get("ARDB_Onion", "host"),
        port=cfg.getint("ARDB_Onion", "port"),
        db=cfg.getint("ARDB_Onion", "db"),
        decode_responses=True)

    print()
    print('Updating ARDB_Onion ...')
    index = 0
    start = time.time()

    # update crawler queue
    for elem in r_serv_onion.smembers('onion_crawler_queue'):
        if PASTES_FOLDER in elem:
            r_serv_onion.srem('onion_crawler_queue', elem)
            r_serv_onion.sadd('onion_crawler_queue', elem.replace(PASTES_FOLDER, '', 1))
            index = index +1
    for elem in r_serv_onion.smembers('onion_crawler_priority_queue'):
        if PASTES_FOLDER in elem:
            r_serv_onion.srem('onion_crawler_queue', elem)
            r_serv_onion.sadd('onion_crawler_queue', elem.replace(PASTES_FOLDER, '', 1))
            index = index +1

    end = time.time()
    print('Updating ARDB_Onion Done => {} paths: {} s'.format(index, end - start))
    print()

    #Set current ail version
    r_serv.set('ail:version', 'v1.5')

    #Set current update_in_progress
    r_serv.set('ail:update_in_progress', 'v1.5')
    r_serv.set('ail:current_background_update', 'v1.5')

    #Set current ail version
    r_serv.set('ail:update_date_v1.5', datetime.datetime.now().strftime("%Y%m%d"))

    print('Done in {} s'.format(end - start_deb))
