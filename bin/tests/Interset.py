#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_words import *
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information
    Leak framework. It create in redis the intersection
    between all the days two by two of the date given in argument.''',
    epilog = '''The Redis database need to be populated by the script
    Wordsranking_Populate.py before using this one.''')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('y',
    type = int,
    metavar = "year",
    help = 'The year',
    action = 'store')

    parser.add_argument('m',
    type = int,
    metavar = "month",
    help = 'The month',
    action = 'store')

    parser.add_argument('-ow',
    help = 'trigger the overwritting mode',
    action = 'store_true')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline(False)

    redis_interbargraph_set(r, args.y, args.m, args.ow)

if __name__ == "__main__":
    main()
