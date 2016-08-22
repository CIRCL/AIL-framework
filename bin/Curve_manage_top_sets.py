#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""



zrank for each day
week -> top zrank for each day


Requirements
------------

*Need running Redis instances. (Redis)
*Categories files of words in /files/ need to be created
*Need the ZMQ_PubSub_Tokenize_Q Module running to be able to work properly.

"""

import redis
import time
import copy
from pubsublogger import publisher
from packages import lib_words
import os
import datetime
import calendar

from Helper import Process

# Config Variables
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

    dico = {}

    # Retreive top data (2*max_card) from days sets
    for timestamp in range(startDate, startDate - top_termFreq_setName_month[1]*oneDay, -oneDay):
        curr_set = top_termFreq_setName_day[0] + str(timestamp)
        print top_termFreq_setName_day[0]
        array_top_day = server_term.zrangebyscore(curr_set, '-inf', '+inf', withscores=True, start=0, num=top_term_freq_max_set_cardinality*2)

        print array_top_day
        for word, value in array_top_day:
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

    print array_month
    print array_week

    # suppress every terms in top sets
    for curr_set, curr_num_day in top_termFreq_set_array[1:3]:
        for w in server_term.zrange(curr_set, 0, -1):
            server_term.zrem(curr_set, w)

    # Add top term from sorted array in their respective sorted sets
    for elem in array_week:
        server_term.zadd(top_termFreq_setName_week[0], float(elem[1]), elem[0])
  
    for elem in array_month:
        server_term.zadd(top_termFreq_setName_month[0], float(elem[1]), elem[0])




if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    config_section = 'CurveManageTopSets'
    p = Process(config_section)

    server_term = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB_TermFreq", "host"),
        port=p.config.get("Redis_Level_DB_TermFreq", "port"),
        db=p.config.get("Redis_Level_DB_TermFreq", "db"))

    # FUNCTIONS #
    publisher.info("Script Curve_manage_top_set started")

    # Sent to the logging a description of the module
    publisher.info("Manage the top sets with the data created by the module curve.")

    manage_top_set()

    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            print 'sleeping'
            time.sleep(60) # sleep a long time then manage the set
            manage_top_set()
            continue

        # Do something with the message from the queue
        #manage_top_set()

