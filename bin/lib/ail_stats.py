#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import datetime
import os
import sys
import time

# from datetime import datetime
from logging import lastResort

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects import ail_objects
from lib.crawlers import get_crawlers_stats
from lib import Tag
from lib import Tracker


# Config
config_loader = ConfigLoader()
r_stats = config_loader.get_db_conn("Kvrocks_Stats")
# r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None


def get_feeders():
    return r_stats.smembers(f'feeders:name')

def get_current_feeder_timestamp(timestamp):
    return int(timestamp - (timestamp % 30))

def get_next_feeder_timestamp(timestamp):
    return int(timestamp + 30 - (timestamp % 30))

def get_feeders_by_time(timestamp):  # TODO
    feeders = {}
    for row in r_stats.zrange(f'feeders:{timestamp}', 0, -1, withscores=True):
        feeders[row[0]] = int(row[1])
    return feeders

def get_feeders_dashboard_full():
    timestamp = get_current_feeder_timestamp(int(time.time()))
    # print(timestamp)
    f_dashboard = {}

    feeders = get_feeders()
    d_time = []
    for i in range(timestamp - 30*20, timestamp +30, 30):
        t_feeders = get_feeders_by_time(i)
        for feeder in feeders:
            if feeder not in f_dashboard:
                f_dashboard[feeder] = []
            if feeder in t_feeders:
                f_dashboard[feeder].append(t_feeders[feeder])
            else:
                f_dashboard[feeder].append(0)
        d_time.append(datetime.datetime.utcfromtimestamp(i).strftime('%H:%M:%S'))
    return {'data': f_dashboard, 'dates': d_time}

def get_feeders_dashboard():
    timestamp = get_current_feeder_timestamp(int(time.time()))
    print(timestamp)

    f_dashboard = {}
    t_feeders = get_feeders_by_time(timestamp)
    for feeder in get_feeders():
        if feeder in t_feeders:
            f_dashboard[feeder] = t_feeders[feeder]
        else:
            f_dashboard[feeder] = 0

    date = datetime.datetime.utcfromtimestamp(timestamp).strftime('%H:%M:%S')
    return {'data': f_dashboard, 'date': date}


def add_feeders(timestamp, feeders):
    if feeders:
        r = r_stats.zadd(f'feeders:{timestamp}', feeders)
        print(r)
        for feeder in feeders:
            r_stats.sadd(f'feeders:name', feeder)
        # cleanup keys
        r_stats.sadd(f'feeders:timestamps', timestamp)

def get_nb_objs_today():
    date = datetime.date.today().strftime("%Y%m%d")
    nb_objs = ail_objects.get_nb_objects_by_date(date)
    return nb_objs

def get_crawler_stats():
    return get_crawlers_stats()

def get_nb_objs_dashboard():
    date = datetime.date.today().strftime("%Y%m%d")
    return ail_objects.get_nb_objects_dashboard(date)

def get_tagged_objs_dashboard():
    tagged_objs = []
    for tagged_obj in Tag.get_tags_dashboard():
        timestamp, obj_gid = tagged_obj.split(':', 1)
        timestamp = datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%H:%M:%S')
        obj_meta = ail_objects.get_obj_basic_meta(ail_objects.get_obj_from_global_id(obj_gid), flask_context=True)
        obj_meta['date_tag'] = timestamp
        tagged_objs.append(obj_meta)
    return tagged_objs

def get_tracked_objs_dashboard(user_org, user_id):
    trackers = Tracker.get_trackers_dashboard(user_org, user_id)
    for t in trackers:
        t['obj'] = ail_objects.get_obj_basic_meta(ail_objects.get_obj_from_global_id(t['obj']))
    return trackers


