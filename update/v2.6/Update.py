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

new_version = 'v2.6'

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()
    r_serv = config_loader.get_redis_conn("ARDB_DB")
    config_loader = None

    r_serv.sadd('ail:to_update', new_version)

    #Set current ail version
    r_serv.set('ail:version', new_version)

    #Set current ail version
    r_serv.hset('ail:update_date', new_version, datetime.datetime.now().strftime("%Y%m%d"))
