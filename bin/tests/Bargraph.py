#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_words import *
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information Leak
    framework. It create an histogram which display the occurency
    of the words per day but also the intersection of day and day-1 of these
    occurencies''',
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
    help = 'The year processed.',
    action = 'store')

    parser.add_argument('m',
    type = int,
    metavar = "month",
    help = 'The month processed.',
    action = 'store')

    parser.add_argument('-f',
    type = str,
    metavar = "filename",
    default = "figure",
    help = 'The absolute path name of the "figure.png"',
    action = 'store')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline(False)

    word_bar_graph(r,args.y,args.m, args.f)

if __name__ == "__main__":
    main()
