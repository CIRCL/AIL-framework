#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis, zmq, ConfigParser
from packages import Paste as P
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
        host = cfg.get("Redis_default", "host"),
        port = cfg.getint("Redis_default", "port"),
        db = args.db)

    p_serv = r_serv.pipeline(False)

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    channel = cfg.get("PubSub_Longlines", "channel_0")
    Sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Longlines", channel)

    # FUNCTIONS #
    publisher.info("Longlines ubscribed to channel {0}".format(cfg.get("PubSub_Longlines", "channel_0")))

    while True:
        PST = P.Paste(Sub.get_message().split(" ", -1)[-1])
        r_serv.sadd("Longlines", PST.p_mime)
        PST.save_in_redis(r_serv, PST.p_mime)


if __name__ == "__main__":
    main()
