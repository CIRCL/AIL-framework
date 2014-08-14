#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Sub_Onion_Q Module
============================

This module subscribe to a Publisher stream and put the received messages
into a Redis-list waiting to be popped later by ZMQ_Sub_Onion.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them (here "tor")

Requirements
------------

*Running Redis instances.
*Should register to the Publisher "ZMQ_PubSub_Categ"

"""
import redis
import ConfigParser
from packages import ZMQ_PubSub
from pubsublogger import publisher

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
    sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Categ", "onion_categ", "tor")

    # FUNCTIONS #
    publisher.info("""Suscribed to channel {0}""".format("onion_categ"))

    while True:
        sub.get_and_lpush(r_serv)

        if r_serv.sismember("SHUTDOWN_FLAGS", "Onion_Q"):
            r_serv.srem("SHUTDOWN_FLAGS", "Onion_Q")
            print "Shutdown Flag Up: Terminating"
            publisher.warning("Shutdown Flag Up: Terminating.")
            break

if __name__ == "__main__":
    main()
