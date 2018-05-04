#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import argparse
import redis
from pubsublogger import publisher
from packages.lib_words import create_dirfile
import configparser


def main():
    """Main Function"""

    # CONFIG #
    cfg = configparser.ConfigParser()
    cfg.read('./packages/config.cfg')

    parser = argparse.ArgumentParser(
        description='''This script is a part of the Analysis Information Leak
        framework. It create a redis list called "listfile" which contain
        the absolute filename of all the files from the directory given in
        the argument "directory".''',
        epilog='Example: ./Dir.py /home/2013/03/')

    parser.add_argument('directory', type=str,
                        help='The directory to run inside', action='store')

    parser.add_argument('-db', type=int, default=0,
                        help='The name of the Redis DB (default 0)',
                        choices=[0, 1, 2, 3, 4], action='store')

    parser.add_argument('-ow', help='trigger the overwritting mode',
                        action='store_true')

    args = parser.parse_args()

    r_serv = redis.StrictRedis(host=cfg.get("Redis_Queues", "host"),
                               port=cfg.getint("Redis_Queues", "port"),
                               db=cfg.getint("Redis_Queues", "db"),
                               decode_responses=True)

    publisher.port = 6380
    publisher.channel = "Script"

    create_dirfile(r_serv, args.directory, args.ow)

if __name__ == "__main__":
    main()
