#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import datetime

sys.path.append(os.environ['AIL_BIN'])
from lib import ConfigLoader

new_version = 'v2.5'

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()
    r_serv = config_loader.get_redis_conn("ARDB_DB")
    config_loader = None

    r_serv.zadd('ail:all_role', {'user': 3})
    r_serv.zadd('ail:all_role', {'user_no_api': 4})
    r_serv.zadd('ail:all_role', {'read_only': 5})

    for user in r_serv.hkeys('user:all'):
        r_serv.sadd('user_role:user', user)
        r_serv.sadd('user_role:user_no_api', user)
        r_serv.sadd('user_role:read_only', user)

    # Set current ail version
    r_serv.set('ail:version', new_version)

    # Set current ail version
    r_serv.hset('ail:update_date', new_version, datetime.datetime.now().strftime("%Y%m%d"))
