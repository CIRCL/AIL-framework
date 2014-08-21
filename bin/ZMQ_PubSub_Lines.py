#!/usr/bin/env python2
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

import Helper

if __name__ == "__main__":
    publisher.channel = "Script"

    config_section = 'PubSub_Global'
    config_channel = 'channel'
    subscriber_name = 'line'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # Publisher
    pub_config_section = 'PubSub_Longlines'
    h.zmq_pub(pub_config_section, None)

    # Subscriber
    h.zmq_sub(config_section)

    # SCRIPT PARSER #
    parser = argparse.ArgumentParser(
        description='''This script is a part of the Analysis Information \
                Leak framework.''')

    parser.add_argument(
        '-max', type=int, default=500,
        help='The limit between "short lines" and "long lines"',
        action='store')

    args = parser.parse_args()

    channel_0 = h.config.get("PubSub_Longlines", "channel_0")
    channel_1 = h.config.get("PubSub_Longlines", "channel_1")

    # FUNCTIONS #
    tmp_string = "Lines script Subscribed to channel {} and Start to publish \
            on channel {}, {}"
    publisher.info(tmp_string.format(h.sub_channel, channel_0, channel_1))

    while True:
        try:
            message = h.redis_rpop()
            if message is not None:
                PST = Paste.Paste(message.split(" ", -1)[-1])
            else:
                if h.redis_queue_shutdown():
                    print "Shutdown Flag Up: Terminating"
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                publisher.debug("Tokeniser is idling 10s")
                time.sleep(10)
                continue

            lines_infos = PST.get_lines_info()

            PST.save_attribute_redis("p_nb_lines", lines_infos[0])
            PST.save_attribute_redis("p_max_length_line", lines_infos[1])

            PST.store.sadd("Pastes_Objects", PST.p_path)
            if lines_infos[1] >= args.max:
                h.pub_channel = channel_0
            else:
                h.pub_channel = channel_1
            h.zmq_pub_send(PST.p_path)
        except IOError:
            print "CRC Checksum Error on : ", PST.p_path
