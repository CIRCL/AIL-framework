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

from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Curve'
    p = Process(config_section)

    # REDIS #
    r_serv1 = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB", "host"),
        port=p.config.get("Redis_Level_DB", "port"),
        db=p.config.get("Redis_Level_DB", "db"))

    # FUNCTIONS #
    publisher.info("Script Curve started")

    # FILE CURVE SECTION #
    csv_path = os.path.join(os.environ['AIL_HOME'],
                            p.config.get("Directories", "wordtrending_csv"))
    wordfile_path = os.path.join(os.environ['AIL_HOME'],
                                 p.config.get("Directories", "wordsfile"))

    message = p.get_from_set()
    prec_filename = None
    while True:
        if message is not None:
            generate_new_graph = True

            filename, word, score = message.split()
            temp = filename.split('/')
            date = temp[-4] + temp[-3] + temp[-2]

            low_word = word.lower()
            prev_score = r_serv1.hget(low_word, date)
            if prev_score is not None:
                r_serv1.hset(low_word, date, int(prev_score) + int(score))
            else:
                r_serv1.hset(low_word, date, score)

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
