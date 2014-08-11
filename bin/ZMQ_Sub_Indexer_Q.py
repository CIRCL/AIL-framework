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

import redis, zmq, ConfigParser
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
        host = cfg.get("Redis_Queues", "host"),
        port = cfg.getint("Redis_Queues", "port"),
        db = cfg.getint("Redis_Queues", "db"))

    # LOGGING #
    publisher.channel = "Queuing"

    # ZMQ #
    channel = cfg.get("PubSub_Global", "channel")
    subscriber_name = "indexer"

    Sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Global", channel, subscriber_name)

    publisher.info("""Suscribed to channel {0}""".format(channel))

    # Until the service is requested to be shutdown, the service
    # will get the data from the global ZMQ queue and buffer it in Redis.

    while True:
        Sub.get_and_lpush(r_serv)

        if r_serv.sismember("SHUTDOWN_FLAGS", "Indexer_Q"):
            r_serv.srem("SHUTDOWN_FLAGS", "Indexer_Q")
            print "Shutdown Flag Up: Terminating"
            publisher.warning("Shutdown Flag Up: Terminating.")
            break

if __name__ == "__main__":
    main()
