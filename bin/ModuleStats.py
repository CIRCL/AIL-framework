#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
    Template for new modules
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
max_set_cardinality = 7
num_day_to_look = 5

def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return date_list


def compute_most_posted(server, message, num_day):
    module, num, keyword, paste_date = message.split(';')

    redis_progression_name_set = 'top_'+ module +'_set'
    # Add/Update in Redis
    prev_score = server.hget(paste_date, module+'-'+keyword)
    if prev_score is not None:
        server.hset(paste_date, module+'-'+keyword, int(prev_score) + int(num))
    else:
        server.hset(paste_date, module+'-'+keyword, int(num))

    # Compute Most Posted
    date_range = get_date_range(num_day) 
    # check if this keyword is eligible for progression
    keyword_total_sum = 0 
    for date in date_range:
        curr_value = server.hget(date, module+'-'+keyword)
        keyword_total_sum += int(curr_value) if curr_value is not None else 0
        
    if keyword in server.smembers(redis_progression_name_set): # if it is already in the set
        return

    if (server.scard(redis_progression_name_set) < max_set_cardinality):
        server.sadd(redis_progression_name_set, keyword)

    else: #not in the set
        #Check value for all members
        member_set = []
        for keyw in server.smembers(redis_progression_name_set):
            keyw_value = server.hget(paste_date, module+'-'+keyw)
            if keyw_value is not None:
                member_set.append((keyw, int(keyw_value)))
        member_set.sort(key=lambda tup: tup[1])
        if member_set[0][1] < keyword_total_sum:
            #remove min from set and add the new one
            print module + ': adding ' +keyword+ '(' +str(keyword_total_sum)+') in set and removing '+member_set[0][0]+'('+str(member_set[0][1])+')'
            server.srem(redis_progression_name_set, member_set[0][0])
            server.sadd(redis_progression_name_set, keyword)


def compute_provider_info(server, path, num_day_to_look):
    
    redis_avg_size_name_set = 'top_size_set'
    redis_providers_name_set = 'providers_set'
    paste = Paste.Paste(path)
    
    paste_size = paste._get_p_size()
    paste_provider = paste.p_source
    paste_date = paste._get_p_date()
    new_avg = paste_size

    # Add/Update in Redis
    server.sadd(redis_providers_name_set, paste_provider)
    prev_num_paste = server.hget(paste_provider+'_num', paste_date)
    if prev_num_paste is not None:
        server.hset(paste_provider+'_num', paste_date, int(prev_num_paste)+1)
        prev_sum_size = server.hget(paste_provider+'_size', paste_date)
        
        if prev_sum_size is not None:
            server.hset(paste_provider+'_size', paste_date, paste_size)
            new_avg = (float(prev_sum_size)+paste_size) / (int(prev_num_paste)+1)
        else:
            server.hset(paste_provider+'_size', paste_date, paste_size)

    else:
        server.hset(paste_provider+'_num', paste_date, 1)

    # Compute Most Posted
    # check if this keyword is eligible for progression
        
    if paste_provider in server.smembers(redis_avg_size_name_set): # if it is already in the set
        return

    elif (server.scard(redis_avg_size_name_set) < max_set_cardinality):
        server.sadd(redis_avg_size_name_set, paste_provider)

    else: #set full capacity
        #Check value for all members
        member_set = []
        for provider in server.smembers(redis_avg_size_name_set):
            curr_avg = 0.0
            curr_size = server.hget(provider+'_size', paste_date)
            curr_num = server.hget(provider+'_num', paste_date)
            if (curr_size is not None) and (curr_num is not None):
                curr_avg += float(curr_size) / float(curr_num)
            member_set.append((provider, curr_avg))
        member_set.sort(key=lambda tup: tup[1])
        if member_set[0][1] < new_avg:
            #remove min from set and add the new one
            print 'Adding ' +paste_provider+ '(' +str(new_avg)+') in set and removing '+member_set[0][0]+'('+str(member_set[0][1])+')'
            server.srem(redis_avg_size_name_set, member_set[0][0])
            server.sadd(redis_avg_size_name_set, paste_provider)



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
        host=p.config.get("Redis_Level_DB_Trending", "host"),
        port=p.config.get("Redis_Level_DB_Trending", "port"),
        db=p.config.get("Redis_Level_DB_Trending", "db"))

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()

        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            print 'sleeping'
            time.sleep(20)
            continue

        else:
            # Do something with the message from the queue
            if len(message.split(';')) > 1:
                compute_most_posted(r_serv_trend, message, num_day_to_look)
            else:
                compute_provider_info(r_serv_trend, message, num_day_to_look)
