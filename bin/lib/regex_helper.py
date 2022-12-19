#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
Regex Helper
"""

import os
import re
import sys
import uuid

from multiprocessing import Process as Proc

sys.path.append(os.environ['AIL_BIN'])
from pubsublogger import publisher

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader
from lib import Statistics

## LOAD CONFIG ##
config_loader = ConfigLoader.ConfigLoader()
r_serv_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None
## -- ##

publisher.port = 6380
publisher.channel = "Script"

def generate_redis_cache_key(module_name):
    new_uuid = str(uuid.uuid4())
    return f'{module_name}_extracted:{new_uuid}'

def _regex_findall(redis_key, regex, item_content, r_set):
    all_items = re.findall(regex, item_content)
    if r_set:
        if len(all_items) > 1:
            for item in all_items:
                r_serv_cache.sadd(redis_key, str(item))
            r_serv_cache.expire(redis_key, 360)
        elif all_items:
            r_serv_cache.sadd(redis_key, str(all_items[0]))
            r_serv_cache.expire(redis_key, 360)
    else:
        if len(all_items) > 1:
            for item in all_items:
                r_serv_cache.lpush(redis_key, str(item))
            r_serv_cache.expire(redis_key, 360)
        elif all_items:
            r_serv_cache.lpush(redis_key, str(all_items[0]))
            r_serv_cache.expire(redis_key, 360)

def regex_findall(module_name, redis_key, regex, item_id, item_content, max_time=30, r_set=True):

    proc = Proc(target=_regex_findall, args=(redis_key, regex, item_content, r_set, ))
    try:
        proc.start()
        proc.join(max_time)
        if proc.is_alive():
            proc.terminate()
            Statistics.incr_module_timeout_statistic(module_name)
            err_mess = f"{module_name}: processing timeout: {item_id}"
            print(err_mess)
            publisher.info(err_mess)
            return []
        else:
            if r_set:
                all_items = r_serv_cache.smembers(redis_key)
            else:
                all_items = r_serv_cache.lrange(redis_key, 0, -1)
            r_serv_cache.delete(redis_key)
            proc.terminate()
            return all_items
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating workers")
        proc.terminate()
        sys.exit(0)

def _regex_finditer(r_key, regex, content):
    iterator = re.finditer(regex, content)
    for match in iterator:
        value = match.group()
        start = match.start()
        end = match.end()
        r_serv_cache.rpush(r_key, f'{start}:{end}:{value}')
    r_serv_cache.expire(r_key, 360)

def regex_finditer(r_key, regex, item_id, content, max_time=30):
    proc = Proc(target=_regex_finditer, args=(r_key, regex, content))
    try:
        proc.start()
        proc.join(max_time)
        if proc.is_alive():
            proc.terminate()
            Statistics.incr_module_timeout_statistic(r_key)
            err_mess = f"{r_key}: processing timeout: {item_id}"
            print(err_mess)
            publisher.info(err_mess)
            return []
        else:
            res = r_serv_cache.lrange(r_key, 0, -1)
            r_serv_cache.delete(r_key)
            proc.terminate()
            all_match = []
            for match in res:
                start, end, value = match.split(':', 2)
                all_match.append((int(start), int(end), value))
            return all_match
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating regex worker")
        proc.terminate()
        sys.exit(0)

def _regex_search(r_key, regex, content):
    if re.search(regex, content):
        r_serv_cache.set(r_key, 1)
        r_serv_cache.expire(r_key, 360)

def regex_search(r_key, regex, item_id, content, max_time=30):
    proc = Proc(target=_regex_search, args=(r_key, regex, content))
    try:
        proc.start()
        proc.join(max_time)
        if proc.is_alive():
            proc.terminate()
            Statistics.incr_module_timeout_statistic(r_key)
            err_mess = f"{r_key}: processing timeout: {item_id}"
            print(err_mess)
            publisher.info(err_mess)
            return False
        else:
            if r_serv_cache.exists(r_key):
                r_serv_cache.delete(r_key)
                return True
            else:
                r_serv_cache.delete(r_key)
                return False
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating regex worker")
        proc.terminate()
        sys.exit(0)
