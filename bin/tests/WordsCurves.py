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
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-cvs',
    type = str,
    metavar = "filename",
    default = "wordstrendingdata",
    help = 'The name of the cvs file wanted to be created',
    action = 'store')

    parser.add_argument('f',
    type = str,
    help = 'The file with the list of words',
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

    p = r.pipeline(False)

    create_curve_with_word_file(r, args.cvs, args.f, args.y, args.m)

if __name__ == "__main__":
    main()
