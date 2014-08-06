#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_words import *
from packages.imported import *
from pubsublogger import publisher

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = 'Analysis Information Leak framework',
    epilog = 'example : seq 2 | parallel ./Wordsranking_Populate.py -nbp 20')

    parser.add_argument('-nbp',
    type = int,
    default = 200,
    help = 'nbpaste',
    action = 'store')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-min',
    type = int,
    default = 4,
    help = 'Minimum length of the inserted words (default 4)',
    action = 'store')

    parser.add_argument('-max',
    type = int,
    default = 200,
    help = 'Maximum length of the inserted words (default 200)',
    action = 'store')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline(False)

    publisher.channel = "youpi"

    redis_words_ranking(p, r, args.nbp, args.min, args.max)

if __name__ == "__main__":
    main()
