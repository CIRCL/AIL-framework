#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
Queue helper module
============================

This module subscribe to a Publisher stream and put the received messages
into a Redis-list waiting to be popped later by others scripts.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

"""
import redis
import ConfigParser
import os
import zmq


class Redis_Queues(object):

    def __init__(self, conf_section, conf_channel, subscriber_name):
        configfile = os.path.join(os.environ('AIL_BIN'), 'packages/config.cfg')
        if not os.path.exists(configfile):
            raise Exception('Unable to find the configuration file. \
                            Did you set environment variables? \
                            Or activate the virtualenv.')
        self.config = ConfigParser.ConfigParser()
        self.config.read(configfile)
        self.subscriber_name = subscriber_name

        self.sub_channel = self.config.get(conf_section, conf_channel)

        # Redis Queue
        config_section = "Redis_Queues"
        self.r_queues = redis.StrictRedis(
            host=self.config.get(config_section, "host"),
            port=self.config.getint(config_section, "port"),
            db=self.config.getint(config_section, "db"))

    def zmq_sub(self, conf_section):
        sub_address = self.config.get(conf_section, 'adress')
        context = zmq.Context()
        self.sub_socket = context.socket(zmq.SUB)
        self.sub_socket.connect(sub_address)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, self.sub_channel)

    def zmq_pub(self, config_section):
        context = zmq.Context()
        self.pub_socket = context.socket(zmq.PUB)
        self.pub_socket.bind(self.config.get(config_section, 'adress'))

    def redis_queue_shutdown(self, is_queue=False):
        if is_queue:
            flag = self.subscriber_name + '_Q'
        else:
            flag = self.subscriber_name
        # srem returns False if the element does not exists
        return self.r_queues.srem('SHUTDOWN_FLAGS', flag)

    def redis_queue_subscribe(self, publisher):
        self.redis_channel = self.sub_channel + self.subscriber_name
        publisher.info("Suscribed to channel {}".format(self.sub_channel))
        while True:
            msg = self.sub_socket.recv()
            p = self.r_queues.pipeline()
            p.sadd("queues", self.redis_channel)
            p.lpush(self.redis_channel, msg)
            p.execute()
            if self.redis_queue_shutdown(True):
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
