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

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader
import statistics

## LOAD CONFIG ##
config_loader = ConfigLoader.ConfigLoader()
r_serv_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None
## -- ##

publisher.port = 6380
publisher.channel = "Script"

def generate_redis_cache_key(module_name):
    return '{}_extracted:{}'.format(module_name, str(uuid.uuid4()))

def _regex_findall(redis_key, regex, item_content, r_set):
    all_items = re.findall(regex, item_content)
    if r_set:
        if len(all_items) > 1:
            r_serv_cache.sadd(redis_key, *all_items)
            r_serv_cache.expire(redis_key, 360)
        elif all_items:
            r_serv_cache.sadd(redis_key, all_items[0])
            r_serv_cache.expire(redis_key, 360)
    else:
        if len(all_items) > 1:
            r_serv_cache.lpush(redis_key, *all_items)
            r_serv_cache.expire(redis_key, 360)
        elif all_items:
            r_serv_cache.lpush(redis_key, all_items[0])
            r_serv_cache.expire(redis_key, 360)

def regex_findall(module_name, redis_key, regex, item_content, max_time=30, r_set=True):

    proc = Proc(target=_regex_findall, args=(redis_key, regex, item_content, r_set, ))
    try:
        proc.start()
        proc.join(max_time)
        if proc.is_alive():
            proc.terminate()
            statistics.incr_module_timeout_statistic(module_name)
            err_mess = "{}: processing timeout: {}".format(module_name, item_id)
            print(err_mess)
            publisher.info(err_mess)
            return []
        else:
            if r_set:
                all_items = r_serv_cache.smembers(redis_key)
            else:
                all_items = r_serv_cache.lrange(redis_key, 0 ,-1)
            r_serv_cache.delete(redis_key)
            proc.terminate()
            return all_items
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating workers")
        proc.terminate()
        sys.exit(0)
