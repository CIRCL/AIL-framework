#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Sub_Attributes_Q Module
============================

This module subscribe to a Publisher stream and put the received messages
into a Redis-list waiting to be popped later by others scripts.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Running Redis instances.
*Should register to the Publisher "ZMQ_Feed"

"""

from pubsublogger import publisher

import Helper


if __name__ == "__main__":
    publisher.channel = "Queuing"

    config_section = 'PubSub_Global'
    config_channel = 'channel'
    subscriber_name = 'attributes'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)
    h.zmq_sub(config_section)
    h.redis_queue_subscribe(publisher)
