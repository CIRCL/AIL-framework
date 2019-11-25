#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import time
import redis
import datetime

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

new_version = 'v2.5'

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()
    r_serv = config_loader.get_redis_conn("ARDB_DB")
    config_loader = None

    r_serv.zadd('ail:all_role', 3, 'user')
    r_serv.zadd('ail:all_role', 4, 'user_no_api')
    r_serv.zadd('ail:all_role', 5, 'read_only')

    for user in r_serv.hkeys('user:all'):
        r_serv.sadd('user_role:user', user)
        r_serv.sadd('user_role:user_no_api', user)
        r_serv.sadd('user_role:read_only', user)

    #Set current ail version
    r_serv.set('ail:version', new_version)

    #Set current ail version
    r_serv.hset('ail:update_date', new_version, datetime.datetime.now().strftime("%Y%m%d"))
