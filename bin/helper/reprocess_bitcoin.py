#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import gzip
import base64
import uuid
import datetime
import base64
import redis
import json
import time

sys.path.append(os.environ['AIL_BIN'])
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

config_section = 'Global'
p = Process(config_section)

r_tags = redis.StrictRedis(
    host=p.config.get("ARDB_Tags", "host"),
    port=p.config.getint("ARDB_Tags", "port"),
    db=p.config.getint("ARDB_Tags", "db"),
    decode_responses=True)

tag = 'infoleak:automatic-detection="bitcoin-address"'

# get tag first/last seen
first_seen = r_tags.hget('tag_metadata:{}'.format(tag), 'first_seen')
last_seen = r_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')

l_dates = substract_date(first_seen, last_seen)

# get all tagged items
for date in l_dates:
    daily_tagged_items = r_tags.smembers('{}:{}'.format(tag, date))

    for item in daily_tagged_items:
        p.populate_set_out(item)
