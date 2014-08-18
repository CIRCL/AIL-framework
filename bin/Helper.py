#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
Queue helper module
============================

This module subscribe to a Publisher stream and put the received messages
into a Redis-list waiting to be popped later by others scripts.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Running Redis instances.
*Should register to the Publisher "ZMQ_PubSub_Line" channel 1

"""
import redis
import ConfigParser
import os
from packages import ZMQ_PubSub


class Queues(object):

    def __init__(self):
        configfile = os.join(os.environ('AIL_BIN'), 'packages/config.cfg')
        if not os.exists(configfile):
            raise Exception('Unable to find the configuration file. Did you set environment variables? Or activate the virtualenv.')
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.configfile)

    def _queue_init_redis(self):
        config_section = "Redis_Queues"
        self.r_queues = redis.StrictRedis(
            host=self.config.get(config_section, "host"),
            port=self.config.getint(config_section, "port"),
            db=self.config.getint(config_section, "db"))

    def _queue_shutdown(self):
        # FIXME: Why not just a key?
        if self.r_queues.sismember("SHUTDOWN_FLAGS", "Feed_Q"):
            self.r_queues.srem("SHUTDOWN_FLAGS", "Feed_Q")
            return True
        return False

    def queue_subscribe(self, publisher, config_section, channel,
                        subscriber_name):
        channel = self.config.get(config_section, channel)
        zmq_sub = ZMQ_PubSub.ZMQSub(self.config, config_section,
                                    channel, subscriber_name)
        publisher.info("""Suscribed to channel {}""".format(channel))
        self._queue_init_redis()
        while True:
            zmq_sub.get_and_lpush(self.r_queues)
            if self._queues_shutdown():
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
