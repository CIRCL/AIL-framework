#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis
import argparse
import ConfigParser
import time
import os
from pubsublogger import publisher
import texttable


def main():
    """Main Function"""

    # CONFIG #
    cfg = ConfigParser.ConfigParser()
    cfg.read('./packages/config.cfg')

    # SCRIPT PARSER #
    parser = argparse.ArgumentParser(
        description='''This script is a part of the Assisted Information Leak framework.''',
        epilog='''''')

    parser.add_argument('-db', type=int, default=0,
                        help='The name of the Redis DB (default 0)',
                        choices=[0, 1, 2, 3, 4], action='store')

    # REDIS #
    r_serv = redis.StrictRedis(
        host=cfg.get("Redis_Queues", "host"),
        port=cfg.getint("Redis_Queues", "port"),
        db=cfg.getint("Redis_Queues", "db"))

    # LOGGING #
    publisher.channel = "Queuing"

    # ZMQ #
    channel = cfg.get("PubSub_Global", "channel")

    # FUNCTIONS #
    publisher.info("""Suscribed to channel {0}""".format(channel))

    while True:
        table = texttable.Texttable()
        table.header(["Queue name", "#Items"])
        row = []
        for queue in r_serv.smembers("queues"):
            current = r_serv.llen(queue)
            current = current - r_serv.llen(queue)
            row.append((queue, r_serv.llen(queue)))

        time.sleep(0.5)
        row.sort()
        table.add_rows(row, header=False)
        os.system('clear')
        print table.draw()


if __name__ == "__main__":
    main()
