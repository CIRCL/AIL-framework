#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import datetime

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()

    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'

    r_serv = config_loader.get_redis_conn("ARDB_DB")
    r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
    config_loader = None

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

    # Add background update
    r_serv.sadd('ail:to_update', 'v1.5')

    #Set current ail version
    r_serv.set('ail:version', 'v1.5')

    #Set current ail version
    r_serv.set('ail:update_date_v1.5', datetime.datetime.now().strftime("%Y%m%d"))

    print('Done in {} s'.format(end - start_deb))
