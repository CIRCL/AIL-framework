#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_words import *
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = 'Analysis Information Leak framework',
    epilog = 'Thats drawing')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB To get the info (0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-db1',
    type = int,
    default = 1,
    help = 'The name of the Redis DB To store (1)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('f',
    type = str,
    metavar= "file",
    help = 'Words filename',
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

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    r2 = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db1)


    p = r.pipeline(False)

    create_data_words_curve(r, r2, args.y, args.m, args.f)

if __name__ == "__main__":
    main()
