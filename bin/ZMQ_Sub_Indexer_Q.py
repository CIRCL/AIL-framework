#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Sub_Indexer_Q Module
============================

The ZMQ_Sub_Indexer_Q module subscribes to PubSub_Global ZMQ channel
and bufferizes the data in a Redis FIFO.

The FIFO will be then processed by the Indexer scripts (ZMQ_Sub_Indexer)
handling the indexing process of the files seen.

"""

from pubsublogger import publisher

import Helper


if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Queuing"

    config_section = 'PubSub_Global'
    config_channel = 'channel'
    subscriber_name = 'indexer'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)
    h.redis_queue_subscribe(publisher)
