#!/usr/bin/env python
# -*-coding:UTF-8 -*

"""
The ZMQ_Sub_Attribute Module
============================

This module is consuming the Redis-list created by the ZMQ_PubSub_Line_Q Module

It perform a sorting on the line's length and publish/forward them to
differents channels:

*Channel 1 if max length(line) < max
*Channel 2 if max length(line) > max

The collected informations about the processed pastes
(number of lines and maximum length line) are stored in Redis.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (LevelDB & Redis)
*Need the ZMQ_PubSub_Line_Q Module running to be able to work properly.

"""
import time
from packages import Paste
from pubsublogger import publisher

from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Attributes'

    p = Process(config_section)

    # FUNCTIONS #
    publisher.info("Attribute is Running")

    while True:
        try:
            message = p.get_from_set()

            if message is not None:
                PST = Paste.Paste(message)
            else:
                publisher.debug("Script Attribute is idling 1s")
                print 'sleeping'
                time.sleep(1)
                continue

            # FIXME do it directly in the class
            PST.save_attribute_redis("p_encoding", PST._get_p_encoding())
            #PST.save_attribute_redis("p_language", PST._get_p_language())
            # FIXME why not all saving everything there.
            PST.save_all_attributes_redis()
            # FIXME Not used.
            PST.store.sadd("Pastes_Objects", PST.p_path)
        except IOError:
            print "CRC Checksum Failed on :", PST.p_path
            publisher.error('Duplicate;{};{};{};CRC Checksum Failed'.format(
                PST.p_source, PST.p_date, PST.p_name))
