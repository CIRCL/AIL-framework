#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    This module makes statistics for some modules and providers

"""

import time
import datetime
import redis
import os
from packages import lib_words
from packages.Date import Date
from pubsublogger import publisher
from Helper import Process
from packages import Paste

# Config Var
max_set_cardinality = 8

def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return date_list


def compute_most_posted(server, message):
    module, num, keyword, paste_date = message.split(';')

    redis_progression_name_set = 'top_'+ module +'_set_' + paste_date

    # Add/Update in Redis
    server.hincrby(paste_date, module+'-'+keyword, int(num))

    # Compute Most Posted
    date = get_date_range(0)[0]
    # check if this keyword is eligible for progression
    keyword_total_sum = 0

    curr_value = server.hget(date, module+'-'+keyword)
    keyword_total_sum += int(curr_value) if curr_value is not None else 0

    if server.zcard(redis_progression_name_set) < max_set_cardinality:
        server.zadd(redis_progression_name_set, float(keyword_total_sum), keyword)

    else: # not in set
        member_set = server.zrangebyscore(redis_progression_name_set, '-inf', '+inf', withscores=True, start=0, num=1)
        # Member set is a list of (value, score) pairs
        if int(member_set[0][1]) < keyword_total_sum:
            #remove min from set and add the new one
            print(module + ': adding ' +keyword+ '(' +str(keyword_total_sum)+') in set and removing '+member_set[0][0]+'('+str(member_set[0][1])+')')
            server.zrem(redis_progression_name_set, member_set[0][0])
            server.zadd(redis_progression_name_set, float(keyword_total_sum), keyword)
            print(redis_progression_name_set)


def compute_provider_info(server_trend, server_pasteName, path):
    redis_all_provider = 'all_provider_set'

    paste = Paste.Paste(path)

    paste_baseName = paste.p_name.split('.')[0]
    paste_size = paste._get_p_size()
    paste_provider = paste.p_source
    paste_date = str(paste._get_p_date())
    redis_sum_size_set = 'top_size_set_' + paste_date
    redis_avg_size_name_set = 'top_avg_size_set_' + paste_date
    redis_providers_name_set = 'providers_set_' + paste_date

    # Add/Update in Redis
    server_pasteName.sadd(paste_baseName, path)
    server_trend.sadd(redis_all_provider, paste_provider)

    num_paste = int(server_trend.hincrby(paste_provider+'_num', paste_date, 1))
    sum_size = float(server_trend.hincrbyfloat(paste_provider+'_size', paste_date, paste_size))
    new_avg = float(sum_size) / float(num_paste)
    server_trend.hset(paste_provider +'_avg', paste_date, new_avg)


    #
    # Compute Most Posted
    #

    # Size
    if server_trend.zcard(redis_sum_size_set) < max_set_cardinality or server_trend.zscore(redis_sum_size_set, paste_provider) != "nil":
        server_trend.zadd(redis_sum_size_set, float(num_paste), paste_provider)
        server_trend.zadd(redis_avg_size_name_set, float(new_avg), paste_provider)
    else: #set full capacity
        member_set = server_trend.zrangebyscore(redis_sum_size_set, '-inf', '+inf', withscores=True, start=0, num=1)
        # Member set is a list of (value, score) pairs
        if float(member_set[0][1]) < new_avg:
            #remove min from set and add the new one
            print('Size - adding ' +paste_provider+ '(' +str(new_avg)+') in set and removing '+member_set[0][0]+'('+str(member_set[0][1])+')')
            server_trend.zrem(redis_sum_size_set, member_set[0][0])
            server_trend.zadd(redis_sum_size_set, float(sum_size), paste_provider)
            server_trend.zrem(redis_avg_size_name_set, member_set[0][0])
            server_trend.zadd(redis_avg_size_name_set, float(new_avg), paste_provider)


    # Num
    # if set not full or provider already present
    if server_trend.zcard(redis_providers_name_set) < max_set_cardinality or server_trend.zscore(redis_providers_name_set, paste_provider) != "nil":
        server_trend.zadd(redis_providers_name_set, float(num_paste), paste_provider)
    else: #set at full capacity
        member_set = server_trend.zrangebyscore(redis_providers_name_set, '-inf', '+inf', withscores=True, start=0, num=1)
        # Member set is a list of (value, score) pairs
        if int(member_set[0][1]) < num_paste:
            #remove min from set and add the new one
            print('Num - adding ' +paste_provider+ '(' +str(num_paste)+') in set and removing '+member_set[0][0]+'('+str(member_set[0][1])+')')
            server_trend.zrem(member_set[0][0])
            server_trend.zadd(redis_providers_name_set, float(num_paste), paste_provider)


if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'ModuleStats'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Makes statistics about valid URL")

    # REDIS #
    r_serv_trend = redis.StrictRedis(
        host=p.config.get("ARDB_Trending", "host"),
        port=p.config.get("ARDB_Trending", "port"),
        db=p.config.get("ARDB_Trending", "db"),
        decode_responses=True)

    r_serv_pasteName = redis.StrictRedis(
        host=p.config.get("Redis_Paste_Name", "host"),
        port=p.config.get("Redis_Paste_Name", "port"),
        db=p.config.get("Redis_Paste_Name", "db"),
        decode_responses=True)

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()

        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            print('sleeping')
            time.sleep(20)
            continue

        else:
            # Do something with the message from the queue
            if len(message.split(';')) > 1:
                compute_most_posted(r_serv_trend, message)
            else:
                compute_provider_info(r_serv_trend, r_serv_pasteName, message)
