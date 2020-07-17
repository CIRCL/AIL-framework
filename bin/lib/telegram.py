#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import Username

config_loader = ConfigLoader.ConfigLoader()
r_serv_crawler = config_loader.get_redis_conn("ARDB_Onion")
config_loader = None

def save_item_correlation(username, item_id, item_date):
    Username.save_item_correlation('telegram', username, item_id, item_date)

def save_telegram_invite_hash(invite_hash, item_id):
    r_serv_crawler.sadd('telegram:invite_code', '{};{}'.format(invite_hash, item_id))
