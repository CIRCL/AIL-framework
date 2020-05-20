#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import datetime
import os
import redis
import sys

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_statistics = config_loader.get_redis_conn("ARDB_Statistics")
config_loader = None

def incr_module_timeout_statistic(module_name):
    curr_date = datetime.date.today()
    r_serv_statistics.hincrby(curr_date.strftime("%Y%m%d"), 'paste_by_modules_timeout:{}'.format(module_name), 1)
