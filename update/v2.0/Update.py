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

    r_serv = config_loader.get_redis_conn("ARDB_DB")
    config_loader = None

    #Set current ail version
    r_serv.set('ail:version', 'v2.0')

    # use new update_date format
    date_tag_to_replace = ['v1.5', 'v1.7']
    for tag in date_tag_to_replace:
        if r_serv.exists('ail:update_date_{}'.format(tag)):
            date_tag = r_serv.get('ail:update_date_{}'.format(tag))
            r_serv.hset('ail:update_date', tag, date_tag)
            r_serv.delete('ail:update_date_{}'.format(tag))

    #Set current ail version
    r_serv.hset('ail:update_date', 'v2.0', datetime.datetime.now().strftime("%Y%m%d"))
