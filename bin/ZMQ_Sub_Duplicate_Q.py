#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis, zmq, ConfigParser
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
        host = cfg.get("Redis_Queues", "host"),
        port = cfg.getint("Redis_Queues", "port"),
        db = cfg.getint("Redis_Queues", "db"))

    # LOGGING #
    publisher.channel = "Queuing"

    # ZMQ #
    channel = cfg.get("PubSub_Global", "channel")
    Sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Global", channel, "duplicate")

    # FUNCTIONS #
    publisher.info("""Suscribed to channel {0}""".format(channel))

    while True:
        Sub.get_and_lpush(r_serv)

        if r_serv.sismember("SHUTDOWN_FLAGS", "Duplicate_Q"):
            r_serv.srem("SHUTDOWN_FLAGS", "Duplicate_Q")
            print "Shutdown Flag Up: Terminating"
            publisher.warning("Shutdown Flag Up: Terminating.")
            break

if __name__ == "__main__":
    main()
