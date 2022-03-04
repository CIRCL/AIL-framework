#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Correlation

config_loader = ConfigLoader.ConfigLoader()
r_serv_crawler = config_loader.get_redis_conn("ARDB_Onion")
config_loader = None

correlation = Correlation.Correlation('username', ['telegram', 'twitter', 'jabber'])

def save_item_correlation(subtype, username, item_id, item_date):
    correlation.save_item_correlation(subtype, username, item_id, item_date)
