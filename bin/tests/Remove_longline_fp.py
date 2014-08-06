#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_words import *
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information Leak
    framework. It removes the line which are in redis under
    the "key" name argument''',
    epilog = '''This script is usually usefull launched after using
    ./Classify_Paste_Token.py example: ./Remove_longline_fp.py mails_categ''')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('key',
    type = str,
    help = 'Name of the key to process in redis ("")',
    action = 'store')

    parser.add_argument('-d',
    help = 'Delete the set of longline created?',
    action = 'store_true')

    parser.add_argument('-s',
    help = 'Store the longline numbers inside a set?',
    action = 'store_true')

    parser.add_argument('-max',
    type = int,
    default = 500,
    help = 'The limit between "short lines" and "long lines" (500)',
    action = 'store')


    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline(False)

    #remove_longline_from_categ(r, args.key, args.d, args.s, args.max)
    detect_longline_from_list(r,args.max)

if __name__ == "__main__":
    main()