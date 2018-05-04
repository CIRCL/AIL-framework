#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The ZMQ_Feed_Q Module
=====================

This module is consuming the Redis-list created by the ZMQ_Feed_Q Module,
And save the paste on disk to allow others modules to work on them.

..todo:: Be able to choose to delete or not the saved paste after processing.
..todo:: Store the empty paste (unprocessed) somewhere in Redis.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances.
*Need the ZMQ_Feed_Q Module running to be able to work properly.

"""
import redis
import configparser
import os

configfile = os.path.join(os.environ['AIL_BIN'], './packages/config.cfg')


def main():
    """Main Function"""

    # CONFIG #
    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    # REDIS
    r_serv = redis.StrictRedis(host=cfg.get("Redis_Queues", "host"),
                               port=cfg.getint("Redis_Queues", "port"),
                               db=cfg.getint("Redis_Queues", "db"),
                               decode_responses=True)

    # FIXME: automatic based on the queue name.
    # ### SCRIPTS ####
    r_serv.sadd("SHUTDOWN_FLAGS", "Feed")
    r_serv.sadd("SHUTDOWN_FLAGS", "Categ")
    r_serv.sadd("SHUTDOWN_FLAGS", "Lines")
    r_serv.sadd("SHUTDOWN_FLAGS", "Tokenize")
    r_serv.sadd("SHUTDOWN_FLAGS", "Attributes")
    r_serv.sadd("SHUTDOWN_FLAGS", "Creditcards")
    r_serv.sadd("SHUTDOWN_FLAGS", "Duplicate")
    r_serv.sadd("SHUTDOWN_FLAGS", "Mails")
    r_serv.sadd("SHUTDOWN_FLAGS", "Onion")
    r_serv.sadd("SHUTDOWN_FLAGS", "Urls")

    r_serv.sadd("SHUTDOWN_FLAGS", "Feed_Q")
    r_serv.sadd("SHUTDOWN_FLAGS", "Categ_Q")
    r_serv.sadd("SHUTDOWN_FLAGS", "Lines_Q")
    r_serv.sadd("SHUTDOWN_FLAGS", "Tokenize_Q")
    r_serv.sadd("SHUTDOWN_FLAGS", "Attributes_Q")
    r_serv.sadd("SHUTDOWN_FLAGS", "Creditcards_Q")
    r_serv.sadd("SHUTDOWN_FLAGS", "Duplicate_Q")
    r_serv.sadd("SHUTDOWN_FLAGS", "Mails_Q")
    r_serv.sadd("SHUTDOWN_FLAGS", "Onion_Q")
    r_serv.sadd("SHUTDOWN_FLAGS", "Urls_Q")

if __name__ == "__main__":
    main()
