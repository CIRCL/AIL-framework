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
import redis
import ConfigParser
from pubsublogger import publisher
from packages import ZMQ_PubSub

configfile = './packages/config.cfg'


def main():
    """Main Function"""

    # CONFIG #
    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    # REDIS #
    r_serv = redis.StrictRedis(
        host=cfg.get("Redis_Queues", "host"),
        port=cfg.getint("Redis_Queues", "port"),
        db=cfg.getint("Redis_Queues", "db"))

    # LOGGING #
    publisher.channel = "Queuing"

    # ZMQ #
    channel = cfg.get("Feed", "topicfilter")
    sub = ZMQ_PubSub.ZMQSub(configfile, "Feed", channel, "feed")

    # FUNCTIONS #
    publisher.info("""Suscribed to channel {0}""".format(channel))

    while True:
        sub.get_and_lpush(r_serv)

        if r_serv.sismember("SHUTDOWN_FLAGS", "Feed_Q"):
            r_serv.srem("SHUTDOWN_FLAGS", "Feed_Q")
            print "Shutdown Flag Up: Terminating"
            publisher.warning("Shutdown Flag Up: Terminating.")
            break

if __name__ == "__main__":
    main()
