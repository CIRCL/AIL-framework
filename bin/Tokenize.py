#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_PubSub_Lines Module
============================

This module is consuming the Redis-list created by the ZMQ_PubSub_Tokenize_Q
Module.

It tokenize the content of the paste and publish the result in the following
format:
    channel_name+' '+/path/of/the/paste.gz+' '+tokenized_word+' '+scoring

    ..seealso:: Paste method (_get_top_words)

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (Redis)
*Need the ZMQ_PubSub_Tokenize_Q Module running to be able to work properly.

"""
import time
from packages import Paste
from pubsublogger import publisher

from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Tokenize'
    p = Process(config_section)

    # LOGGING #
    publisher.info("Tokeniser started")

    while True:
        message = p.get_from_set()
        print message
        if message is not None:
            paste = Paste.Paste(message)
            for word, score in paste._get_top_words().items():
                if len(word) >= 4:
                    msg = '{} {} {}'.format(paste.p_path, word, score)
                    p.populate_set_out(msg)
        else:
            publisher.debug("Tokeniser is idling 10s")
            time.sleep(10)
            print "sleepin"
