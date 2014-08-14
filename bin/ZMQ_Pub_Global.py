#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Pub_Global Module
=========================

This module is consuming the Redis-list created by the script ./Dir.py.
This module is as the same level of the ZMQ tree than the Module ZMQ_Feed

Whereas the ZMQ_Feed is poping the list created in redis by ZMQ_Feed_Q which is
listening a stream, ZMQ_Pub_Global is poping the list created in redis by
./Dir.py.

Thanks to this Module there is now two way to Feed the ZMQ tree:
*By a continuous stream ..seealso:: ZMQ_Feed Module
*Manually with this module and ./Dir.py script.

Requirements
------------

*Need running Redis instances. (Redis)

"""
import redis
import ConfigParser
import time
from packages import ZMQ_PubSub
from pubsublogger import publisher

configfile = './packages/config.cfg'


def main():
    """Main Function"""

    # CONFIG #
    cfg = ConfigParser.ConfigParser()
    cfg.read('./packages/config.cfg')

    # REDIS #
    r_serv = redis.StrictRedis(
        host=cfg.get("Redis_Queues", "host"),
        port=cfg.getint("Redis_Queues", "port"),
        db=cfg.getint("Redis_Queues", "db"))

    # LOGGING #
    publisher.channel = "Global"

    # ZMQ #
    pub_glob = ZMQ_PubSub.ZMQPub(configfile, "PubSub_Global", "global")

    # FONCTIONS #
    publisher.info("Starting to publish.")

    while True:
        filename = r_serv.lpop("filelist")

        if filename is not None:

            msg = cfg.get("PubSub_Global", "channel")+" "+filename
            pub_glob.send_message(msg)
            publisher.debug("{0} Published".format(msg))
        else:
            time.sleep(10)
            publisher.debug("Nothing to publish")


if __name__ == "__main__":
    main()
