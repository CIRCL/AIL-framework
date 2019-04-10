#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Tokenize Module
===================

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
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Tokenize'
    p = Process(config_section)

    # LOGGING #
    publisher.info("Tokeniser started")

    while True:
        message = p.get_from_set()
        print(message)
        if message is not None:
            paste = Paste.Paste(message)
            signal.alarm(5)
            try:
                for word, score in paste._get_top_words().items():
                    if len(word) >= 4:
                        msg = '{} {} {}'.format(paste.p_rel_path, word, score)
                        p.populate_set_out(msg)
            except TimeoutException:
                p.incr_module_timeout_statistic()
                print ("{0} processing timeout".format(paste.p_rel_path))
                continue
            else:
                signal.alarm(0)
        else:
            publisher.debug("Tokeniser is idling 10s")
            time.sleep(10)
            print("Sleeping")
