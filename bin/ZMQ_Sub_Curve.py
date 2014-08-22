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
from packages import Paste
from pubsublogger import publisher
from packages import lib_words
import os

import Helper

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'PubSub_Words'
    config_channel = 'channel_0'
    subscriber_name = "curve"

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # Subscriber
    h.zmq_sub(config_section)

    # REDIS #
    r_serv1 = redis.StrictRedis(
        host=h.config.get("Redis_Level_DB", "host"),
        port=h.config.get("Redis_Level_DB", "port"),
        db=h.config.get("Redis_Level_DB", "db"))

    # FUNCTIONS #
    publisher.info("Script Curve subscribed to {}".format(h.sub_channel))

    # FILE CURVE SECTION #
    csv_path = os.path.join(os.environ['AIL_HOME'],
                            h.config.get("Directories", "wordtrending_csv"))
    wordfile_path = os.path.join(os.environ['AIL_HOME'],
                                 h.config.get("Directories", "wordsfile"))

    message = h.redis_rpop()
    prec_filename = None
    while True:
        if message is not None:
            channel, filename, word, score = message.split()
            if prec_filename is None or filename != prec_filename:
                PST = Paste.Paste(filename)
                lib_words.create_curve_with_word_file(
                    r_serv1, csv_path, wordfile_path, int(PST.p_date.year),
                    int(PST.p_date.month))

            prec_filename = filename
            prev_score = r_serv1.hget(word.lower(), PST.p_date)
            print prev_score
            if prev_score is not None:
                r_serv1.hset(word.lower(), PST.p_date,
                             int(prev_score) + int(score))
            else:
                r_serv1.hset(word.lower(), PST.p_date, score)

        else:
            if h.redis_queue_shutdown():
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Script Curve is Idling")
            print "sleepin"
            time.sleep(1)

        message = h.redis_rpop()
