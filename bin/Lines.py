#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The ZMQ_PubSub_Lines Module
============================

This module is consuming the Redis-list created by the ZMQ_PubSub_Line_Q
Module.

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
import argparse
import time
from packages import Paste
from pubsublogger import publisher

from Helper import Process

if __name__ == '__main__':
    publisher.port = 6380
    publisher.channel = 'Script'

    config_section = 'Lines'
    p = Process(config_section)

    # SCRIPT PARSER #
    parser = argparse.ArgumentParser(
        description='This script is a part of the Analysis Information \
                Leak framework.')

    parser.add_argument(
        '-max', type=int, default=500,
        help='The limit between "short lines" and "long lines"',
        action='store')

    args = parser.parse_args()

    # FUNCTIONS #
    tmp_string = "Lines script Subscribed to channel {} and Start to publish \
            on channel Longlines, Shortlines"
    publisher.info(tmp_string)

    while True:
        try:
            message = p.get_from_set()
            print(message)
            if message is not None:
                PST = Paste.Paste(message)
            else:
                publisher.debug("Tokeniser is idling 10s")
                time.sleep(10)
                continue

            # FIXME do it in the paste class
            lines_infos = PST.get_lines_info()
            PST.save_attribute_redis("p_nb_lines", lines_infos[0])
            PST.save_attribute_redis("p_max_length_line", lines_infos[1])

            # FIXME Not used.
            PST.store.sadd("Pastes_Objects", PST.p_rel_path)
            print(PST.p_rel_path)
            if lines_infos[1] < args.max:
                p.populate_set_out( PST.p_rel_path , 'LinesShort')
            else:
                p.populate_set_out( PST.p_rel_path , 'LinesLong')
        except IOError:
            print("CRC Checksum Error on : ", PST.p_rel_path)
