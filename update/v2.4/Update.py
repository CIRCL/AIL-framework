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

new_version = 'v2.4'

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()
    r_serv = config_loader.get_redis_conn("ARDB_DB")
    r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
    config_loader = None

    r_serv_onion.sunionstore('domain_update_v2.4', 'full_onion_up', 'full_regular_up')
    r_serv.set('update:nb_elem_to_convert', r_serv_onion.scard('domain_update_v2.4'))
    r_serv.set('update:nb_elem_converted',0)

    # Add background update
    r_serv.sadd('ail:to_update', new_version)

    #Set current ail version
    r_serv.set('ail:version', new_version)

    #Set current ail version
    r_serv.hset('ail:update_date', new_version, datetime.datetime.now().strftime("%Y%m%d"))
