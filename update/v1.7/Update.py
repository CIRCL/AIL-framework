#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import datetime

sys.path.append(os.environ['AIL_BIN'])
from lib import ConfigLoader

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()

    r_serv = config_loader.get_redis_conn("ARDB_DB")
    config_loader = None

    # Set current ail version
    r_serv.set('ail:version', 'v1.7')

    # Set current ail version
    r_serv.set('ail:update_date_v1.7', datetime.datetime.now().strftime("%Y%m%d"))
