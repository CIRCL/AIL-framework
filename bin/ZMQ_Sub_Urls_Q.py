#!/usr/bin/env python2
# -*-coding:UTF-8 -*

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
    sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Categ", "web_categ", "urls")

    # FUNCTIONS #
    publisher.info("""Suscribed to channel {0}""".format("web_categ"))

    while True:
        sub.get_and_lpush(r_serv)

        if r_serv.sismember("SHUTDOWN_FLAGS", "Urls_Q"):
            r_serv.srem("SHUTDOWN_FLAGS", "Urls_Q")
            print "Shutdown Flag Up: Terminating"
            publisher.warning("Shutdown Flag Up: Terminating.")
            break

if __name__ == "__main__":
    main()
