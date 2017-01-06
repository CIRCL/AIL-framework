#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""

This module manage top sets for terms frequency.
Every 'refresh_rate' update the weekly and monthly set


Requirements
------------

*Need running Redis instances. (Redis)
*Categories files of words in /files/ need to be created
*Need the ZMQ_PubSub_Tokenize_Q Module running to be able to work properly.

"""

import redis
import time
import datetime
import copy
from pubsublogger import publisher
from packages import lib_words
import datetime
import calendar
import os
import ConfigParser

# Config Variables
Refresh_rate = 60*5 #sec
BlackListTermsSet_Name = "BlackListSetTermSet"
TrackedTermsSet_Name = "TrackedSetTermSet"
top_term_freq_max_set_cardinality = 20 # Max cardinality of the terms frequences set
oneDay = 60*60*24
num_day_month = 31
num_day_week = 7

top_termFreq_setName_day = ["TopTermFreq_set_day_", 1]
top_termFreq_setName_week = ["TopTermFreq_set_week", 7]
top_termFreq_setName_month = ["TopTermFreq_set_month", 31]
top_termFreq_set_array = [top_termFreq_setName_day,top_termFreq_setName_week, top_termFreq_setName_month]


def manage_top_set():
    startDate = datetime.datetime.now()
    startDate = startDate.replace(hour=0, minute=0, second=0, microsecond=0)
    startDate = calendar.timegm(startDate.timetuple())
    blacklist_size = int(server_term.scard(BlackListTermsSet_Name))

    dico = {}

    # Retreive top data (max_card + blacklist_size) from days sets
    for timestamp in range(startDate, startDate - top_termFreq_setName_month[1]*oneDay, -oneDay):
        curr_set = top_termFreq_setName_day[0] + str(timestamp)
        array_top_day = server_term.zrevrangebyscore(curr_set, '+inf', '-inf', withscores=True, start=0, num=top_term_freq_max_set_cardinality+blacklist_size)

        for word, value in array_top_day:
            if word not in server_term.smembers(BlackListTermsSet_Name):
                if word in dico.keys():
                    dico[word] += value
                else:
                    dico[word] = value

        if timestamp == startDate - num_day_week*oneDay:
            dico_week = copy.deepcopy(dico)

    # convert dico into sorted array
    array_month = []
    for w, v in dico.iteritems():
        array_month.append((w, v))
    array_month.sort(key=lambda tup: -tup[1])
    array_month = array_month[0:20]

    array_week = []
    for w, v in dico_week.iteritems():
        array_week.append((w, v))
    array_week.sort(key=lambda tup: -tup[1])
    array_week = array_week[0:20]

    # suppress every terms in top sets
    for curr_set, curr_num_day in top_termFreq_set_array[1:3]:
        for w in server_term.zrange(curr_set, 0, -1):
            server_term.zrem(curr_set, w)

    # Add top term from sorted array in their respective sorted sets
    for elem in array_week:
        server_term.zadd(top_termFreq_setName_week[0], float(elem[1]), elem[0])
  
    for elem in array_month:
        server_term.zadd(top_termFreq_setName_month[0], float(elem[1]), elem[0])

    timestamp = int(time.mktime(datetime.datetime.now().timetuple()))
    value = str(timestamp) + ", " + "-"
    r_temp.set("MODULE_"+ "CurveManageTopSets" + "_" + str(os.getpid()), value)
    print "refreshed module"



if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    
    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)


    # For Module Manager
    r_temp = redis.StrictRedis(
        host=cfg.get('RedisPubSub', 'host'),
        port=cfg.getint('RedisPubSub', 'port'),
        db=cfg.getint('RedisPubSub', 'db'))

    timestamp = int(time.mktime(datetime.datetime.now().timetuple()))
    value = str(timestamp) + ", " + "-"
    r_temp.set("MODULE_"+ "CurveManageTopSets" + "_" + str(os.getpid()), value)
    r_temp.sadd("MODULE_TYPE_"+ "CurveManageTopSets" , str(os.getpid()))

    server_term = redis.StrictRedis(
        host=cfg.get("Redis_Level_DB_TermFreq", "host"),
        port=cfg.getint("Redis_Level_DB_TermFreq", "port"),
        db=cfg.getint("Redis_Level_DB_TermFreq", "db"))

    publisher.info("Script Curve_manage_top_set started")

    # Sent to the logging a description of the module
    publisher.info("Manage the top sets with the data created by the module curve.")

    manage_top_set()

    while True:
        # Get one message from the input queue (module only work if linked with a queue)
        time.sleep(Refresh_rate) # sleep a long time then manage the set
        manage_top_set()

