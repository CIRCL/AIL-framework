#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Sub_Curve Module
============================

This module is consuming the Redis-list created by the ZMQ_Sub_Curve_Q Module.

This modules update a .csv file used to draw curves representing selected
words and their occurency per day.

..note:: The channel will have the name of the file created.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.




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
from pubsublogger import publisher
from packages import lib_words
import os
import datetime
import calendar

from Helper import Process

# Config Variables
top_term_freq_max_set_cardinality = 20 # Max cardinality of the terms frequences set


def getValueOverRange(word, startDate, num_day):
    oneDay = 60*60*24
    to_return = 0
    for timestamp in range(startDate, startDate - num_day*oneDay, -oneDay):
        value = server_term.hget(timestamp, word)
        to_return += int(value) if value is not None else 0
    return to_return



if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Curve'
    p = Process(config_section)

    # REDIS #
    r_serv1 = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB_Curve", "host"),
        port=p.config.get("Redis_Level_DB_Curve", "port"),
        db=p.config.get("Redis_Level_DB_Curve", "db"))

    server_term = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB_TermFreq", "host"),
        port=p.config.get("Redis_Level_DB_TermFreq", "port"),
        db=p.config.get("Redis_Level_DB_TermFreq", "db"))

    # FUNCTIONS #
    publisher.info("Script Curve started")

    # FILE CURVE SECTION #
    csv_path = os.path.join(os.environ['AIL_HOME'],
                            p.config.get("Directories", "wordtrending_csv"))
    wordfile_path = os.path.join(os.environ['AIL_HOME'],
                                 p.config.get("Directories", "wordsfile"))

    message = p.get_from_set()
    prec_filename = None
    generate_new_graph = False

    # Term Frequency
    top_termFreq_setName_day = ["TopTermFreq_set_day", 1]
    top_termFreq_setName_week = ["TopTermFreq_set_week", 7]
    top_termFreq_setName_month = ["TopTermFreq_set_month", 31]
    top_termFreq_set_array = [top_termFreq_setName_day,top_termFreq_setName_week, top_termFreq_setName_month]

    while True:

        if message is not None:
            generate_new_graph = True

            filename, word, score = message.split()
            temp = filename.split('/')
            date = temp[-4] + temp[-3] + temp[-2]
            timestamp = calendar.timegm((int(temp[-4]), int(temp[-3]), int(temp[-2]), 0, 0, 0))

            # If set size is greater then the one authorized
            # suppress smaller elements
            for curr_set, curr_num_day in top_termFreq_set_array:
                diffCard = server_term.scard(curr_set) - top_term_freq_max_set_cardinality
                if diffCard > 0:
                    top_termFreq = server_term.smembers(curr_set)
                    sorted_top_termFreq_set = []
                    for word in top_termFreq:
                        word_value = getValueOverRange(word, timestamp, curr_num_day)
                        sorted_top_termFreq_set.append((word, word_value))

                    sorted_top_termFreq_set.sort(key=lambda tup: tup[1])
                    for i in range(0, diffCard):
                        print 'set oversized, dropping', sorted_top_termFreq_set[i][0]
                        server_term.srem(curr_set, sorted_top_termFreq_set[i][0])


            #timer = time.clock()
            low_word = word.lower()
            #print 'wordlower', time.clock() - timer
            r_serv1.hincrby(low_word, date, int(score))


            # Update redis
            curr_word_value = int(server_term.hincrby(timestamp, low_word, int(score)))
            
            # Manage Top set
            for curr_set, curr_num_day in top_termFreq_set_array:

                if server_term.scard(curr_set) < top_term_freq_max_set_cardinality:
                    server_term.sadd(curr_set, low_word)
                elif server_term.sismember(curr_set, low_word):
                    continue

                else:
                    #timer = time.clock()
                    curr_word_value = getValueOverRange(low_word, timestamp, curr_num_day)
                    #print 'curr_range', time.clock() - timer
                    top_termFreq = server_term.smembers(curr_set)
                    sorted_top_termFreq_set = []
                    #timer = time.clock()
                    for word in top_termFreq:
                        word_value = getValueOverRange(word, timestamp, curr_num_day)
                        sorted_top_termFreq_set.append((word, word_value))

                    sorted_top_termFreq_set.sort(key=lambda tup: tup[1])
                    #print 'whole_range', time.clock() - timer

                    if curr_word_value > int(sorted_top_termFreq_set[0][1]):
                        print str(curr_num_day)+':', low_word, curr_word_value, '\t', sorted_top_termFreq_set[0][0], sorted_top_termFreq_set[0][1], '\t', curr_word_value > sorted_top_termFreq_set[0][1]
                        server_term.srem(curr_set, sorted_top_termFreq_set[0][0])
                        server_term.sadd(curr_set, low_word)

        else:
            if generate_new_graph:
                generate_new_graph = False
                print 'Building graph'
                today = datetime.date.today()
                year = today.year
                month = today.month
                lib_words.create_curve_with_word_file(r_serv1, csv_path,
                                                      wordfile_path, year,
                                                      month)

            publisher.debug("Script Curve is Idling")
            print "sleeping"
            time.sleep(10)
        message = p.get_from_set()
