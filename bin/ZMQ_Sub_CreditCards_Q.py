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
    Sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Categ", "creditcard_categ", "cards")

    # FUNCTIONS #
    publisher.info("""Suscribed to channel {0}""".format("creditcard_categ"))

    while True:
        Sub.get_and_lpush(r_serv)

        if r_serv.sismember("SHUTDOWN_FLAGS", "Creditcards_Q"):
            r_serv.srem("SHUTDOWN_FLAGS", "Creditcards_Q")
            print "Shutdown Flag Up: Terminating"
            publisher.warning("Shutdown Flag Up: Terminating.")
            break

if __name__ == "__main__":
    main()
