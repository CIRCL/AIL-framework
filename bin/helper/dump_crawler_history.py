#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import gzip
import datetime
import redis
import json
import time

import shutil

sys.path.append(os.environ['AIL_BIN'])
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
from HiddenServices import HiddenServices
from Helper import Process

def substract_date(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from # timedelta
    l_date = []
    for i in range(delta.days + 1):
        date = date_from + datetime.timedelta(i)
        l_date.append( date.strftime('%Y%m%d') )
    return l_date

config_section = 'Keys'
p = Process(config_section)

r_serv_onion = redis.StrictRedis(
    host=p.config.get("ARDB_Onion", "host"),
    port=p.config.getint("ARDB_Onion", "port"),
    db=p.config.getint("ARDB_Onion", "db"),
    decode_responses=True)

date_from = '20190614'
date_to = '20190615'
service_type = 'onion'
date_range = substract_date(date_from, date_to)

dir_path = os.path.join(os.environ['AIL_HOME'], 'temp')

for date in date_range:
    domains_up = list(r_serv_onion.smembers('{}_up:{}'.format(service_type, date)))
    if domains_up:
        save_path = os.path.join(dir_path, date[0:4], date[4:6], date[6:8])
        try:
            os.makedirs(save_path)
        except FileExistsError:
            pass
    for domain in domains_up:
        print(domain)
        h = HiddenServices(domain, 'onion')
        item_core = h.get_domain_crawled_core_item()
        l_pastes = h.get_last_crawled_pastes(item_root=item_core['root_item'])
        res = h.create_domain_basic_archive(l_pastes)
        filename = os.path.join(save_path, '{}'.format(domain))
        with open(filename, 'wb') as f:
            shutil.copyfileobj(res, f)
            print('done')
