#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Pub_Global Module
=========================

This module is consuming the Redis-list created by the script ./Dir.py.
This module is as the same level of the ZMQ tree than the Module ZMQ_Feed

Whereas the ZMQ_Feed is poping the list created in redis by ZMQ_Feed_Q which is
listening a stream, ZMQ_Pub_Global is poping the list created in redis by
./Dir.py.

Thanks to this Module there is now two way to Feed the ZMQ tree:
*By a continuous stream ..seealso:: ZMQ_Feed Module
*Manually with this module and ./Dir.py script.

Requirements
------------

*Need running Redis instances. (Redis)

"""
import time
from pubsublogger import publisher

import Helper

if __name__ == "__main__":
    publisher.channel = "Global"

    config_section = 'PubSub_Global'
    config_channel = 'channel'
    subscriber_name = 'global'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # Publisher
    pub_config_section = 'PubSub_Global'
    pub_config_channel = 'channel'
    h.zmq_pub(pub_config_section, pub_config_channel)

    # LOGGING #
    publisher.info("Starting to publish.")

    while True:
        filename = h.redis_rpop()

        if filename is not None:
            h.zmq_pub_send(filename)
        else:
            time.sleep(10)
            publisher.debug("Nothing to publish")
