#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import datetime
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_statistics = config_loader.get_db_conn("Kvrocks_Stats")
config_loader = None

PIE_CHART_MAX_CARDINALITY = 8

def incr_module_timeout_statistic(module_name):
    curr_date = datetime.date.today()
    r_statistics.hincrby(curr_date.strftime("%Y%m%d"), 'paste_by_modules_timeout:{}'.format(module_name), 1)

def create_item_statistics(item_id, source, size):
    pass

def get_item_sources():
    return r_statistics.smembers('all_provider_set')

def get_nb_items_processed_by_day_and_source(date, source):
    nb_items = r_statistics.hget(f'{source}_num', date)
    if not nb_items:
        nb_items = 0
    return int(nb_items)

def get_items_total_size_by_day_and_source(date, source):
    total_size = r_statistics.hget(f'{source}_size', date)
    if not total_size:
        total_size = 0
    return float(total_size)

def get_items_av_size_by_day_and_source(date, source):
    av_size = r_statistics.hget(f'{source}_avg', date)
    if not av_size:
        av_size = 0
    return float(av_size)

def _create_item_stats_size_nb(date, source, num, size, avg):
    r_statistics.hset(f'{source}_num', date, num)
    r_statistics.hset(f'{source}_size', date, size)
    r_statistics.hset(f'{source}_avg', date, avg)

def get_item_stats_size_avg_by_date():
    return r_statistics.zrange(f'top_avg_size_set_{date}', 0, -1, withscores=True)

def get_item_stats_nb_by_date():
    return r_statistics.zrange(f'providers_set_{date}', 0, -1, withscores=True)

def _set_item_stats_nb_by_date(date, source):
    return r_statistics.zrange(f'providers_set_{date}', )

# # TODO: load ZSET IN CACHE => FAST UPDATE
def update_item_stats_size_nb(item_id, source, size, date):
    # Add/Update in Redis
    r_statistics.sadd('all_provider_set', source)

    nb_items = int(r_statistics.hincrby(f'{source}_num', date, 1))
    sum_size = float(r_statistics.hincrbyfloat(f'{source}_size', date, size))
    new_avg = sum_size / nb_items
    r_statistics.hset(f'{source}_avg', date, new_avg)

    # TOP Items Size
    if r_statistics.zcard(f'top_size_set_{date}') < PIE_CHART_MAX_CARDINALITY:
        r_statistics.zadd(f'top_avg_size_set_{date}', {source: new_avg})

    else:
        member_set = r_statistics.zrangebyscore(f'top_avg_size_set_{date}', '-inf', '+inf', withscores=True, start=0, num=1)
        # Member set is a list of (value, score) pairs
        if float(member_set[0][1]) < new_avg:
            # remove min from set and add the new one
            r_statistics.zrem(f'top_avg_size_set_{date}', member_set[0][0])
            r_statistics.zadd(f'top_avg_size_set_{date}', {source: new_avg})

    # TOP Nb Items
    if r_statistics.zcard(f'providers_set_{date}') < PIE_CHART_MAX_CARDINALITY or r_statistics.zscore(f'providers_set_{date}', source) != None:
        r_statistics.zadd(f'providers_set_{date}', {source: float(nb_items)})
    else: # zset at full capacity
        member_set = r_statistics.zrangebyscore(f'providers_set_{date}', '-inf', '+inf', withscores=True, start=0, num=1)
        # Member set is a list of (value, score) pairs
        if int(member_set[0][1]) < nb_items:
            # remove min from set and add the new one
            r_statistics.zrem(member_set[0][0])
            r_statistics.zadd(f'providers_set_{date}', {source: float(nb_items)})

# keyword  num

def _add_module_stats(module_name, total_sum, keyword, date):
    r_statistics.zadd(f'top_{module_name}_set_{date}', {keyword: float(total_sum)})

# # TODO: ONE HSET BY MODULE / CUSTOM STATS
def update_module_stats(module_name, num, keyword, date):

    # Add/Update in Redis
    r_statistics.hincrby(date, f'{module_name}-{keyword}', int(num)) # # TODO: RENAME ME !!!!!!!!!!!!!!!!!!!!!!!!!

    # Compute Most Posted
    # check if this keyword is eligible for progression
    keyword_total_sum = 0

    curr_value = r_statistics.hget(date, f'{module_name}-{keyword}')
    keyword_total_sum += int(curr_value) if curr_value is not None else 0

    if r_statistics.zcard(f'top_{module_name}_set_{date}') < PIE_CHART_MAX_CARDINALITY:
        r_statistics.zadd(f'top_{module_name}_set_{date}', {keyword: float(keyword_total_sum)})
    else:  # zset at full capacity
        member_set = r_statistics.zrangebyscore(f'top_{module_name}_set_{date}', '-inf', '+inf', withscores=True, start=0, num=1)
        # Member set is a list of (value, score) pairs
        if int(member_set[0][1]) < keyword_total_sum:
            # remove min from set and add the new one
            r_statistics.zrem(f'top_{module_name}_set_{date}', member_set[0][0])
            r_statistics.zadd(f'top_{module_name}_set_{date}', {keyword: float(keyword_total_sum)})

def get_module_tld_stats_by_tld_date(date, tld):
    nb_tld = r_statistics.hget(f'credential_by_tld:{date}', tld)
    if not nb_tld:
        nb_tld = 0
    return int(nb_tld)

def get_module_tld_stats_by_date(module, date):
    return r_statistics.hgetall(f'{module}_by_tld:{date}')

def add_module_tld_stats_by_date(module, date, tld, nb):
    r_statistics.hincrby(f'{module}_by_tld:{date}', tld, int(nb))

# r_stats.zincrby('module:Global:incomplete_file', 1, datetime.datetime.now().strftime('%Y%m%d'))
# r_stats.zincrby('module:Global:invalid_file', 1, datetime.datetime.now().strftime('%Y%m%d'))
