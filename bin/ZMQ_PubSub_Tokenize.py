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

import Helper

if __name__ == "__main__":
    publisher.channel = "Script"

    # Publisher
    pub_config_section = 'PubSub_Words'

    config_section = 'PubSub_Longlines'
    config_channel = 'channel_1'
    subscriber_name = 'tokenize'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    h.zmq_pub(pub_config_section)
    pub_channel = h.config.get(pub_config_section, "channel_0")

    # LOGGING #
    publisher.info("Tokeniser subscribed to channel {}".format(h.sub_channel))

    while True:
        message = h.r_queues.rpop(h.sub_channel + h.subscriber_name)
        print message
        if message is not None:
            paste = Paste.Paste(message.split(" ", -1)[-1])
            for word, score in paste._get_top_words().items():
                if len(word) >= 4:
                    h.pub_socket.send(
                        '{} {} {} {}'.format(pub_channel, paste.p_path,
                                             word, score))
        else:
            if h.redis_queue_shutdown():
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Tokeniser is idling 10s")
            time.sleep(10)
            print "sleepin"
