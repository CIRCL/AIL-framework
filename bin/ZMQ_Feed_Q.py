#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The ZMQ_Feed_Q Module
=====================

This module is the first of the ZMQ tree processing.
It's subscribe to a data stream and put the received messages
into a Redis-list waiting to be popped later by others scripts

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances.
*Messages from the stream should be formated as follow:
    "channel_name"+" "+/path/to/the/paste.gz+" "base64_data_encoded_paste"

"""

from pubsublogger import publisher

import Helper


if __name__ == "__main__":
    publisher.channel = "Queuing"

    config_section = 'Feed'
    config_channel = 'topicfilter'
    subscriber_name = 'feed'

    h = Helper.Redis_Queues(subscriber_name)
    h.zmq_sub(config_section)
    h.redis_queue_subscribe(publisher)
