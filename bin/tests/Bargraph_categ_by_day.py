#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_refine import *
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information Leak
    framework. It create an histogram which display the occurency
    of the word category per days.''',
    epilog = '''The Redis database need to be populated by the script
    Classify_Paste_Token.py before.
    It's also usefull to launch Remove_longline_fp.py and Refine_with_regex.py
    to create a more accurate histogram.
    example: ./Bargraph_categ_by_day.py 2013 12 mails_categ''')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-f',
    type = str,
    metavar = "filename",
    default = "figure",
    help = 'The absolute path name of the "figure.png"',
    action = 'store')

    parser.add_argument('y',
    type = int,
    metavar = "year",
    help = 'The year processed',
    action = 'store')

    parser.add_argument('m',
    type = int,
    metavar = "month",
    help = 'The month processed',
    action = 'store')

    parser.add_argument('key',
    type = str,
    help ='name of the key to process in redis (the word_categ concerned)',
    action = 'store')

    args = parser.parse_args()


    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline(False)

    graph_categ_by_day(r, args.f, args.y, args.m, args.key)

if __name__ == "__main__":
    main()
