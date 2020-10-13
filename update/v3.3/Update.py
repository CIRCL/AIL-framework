#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import argparse
import datetime
import configparser

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

new_version = 'v3.3'

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()
    r_serv_db = config_loader.get_redis_conn("ARDB_DB")
    config_loader = None

    #Set current ail version
    r_serv_db.set('ail:version', new_version)

    #Set current ail version
    r_serv_db.hset('ail:update_date', new_version, datetime.datetime.now().strftime("%Y%m%d"))
