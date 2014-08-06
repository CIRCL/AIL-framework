#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_refine import *
from packages.imported import *
from pubsublogger import publisher

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information
    Leak framework. Is refining a redis set by
    re analysing set with regex and changing the score by the number of
    regex matching''',
    epilog = '''example of use: ./Refine_with_regex.py 2013 12 -regex mail
    -key mails_categ''')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-nbm',
    type = int,
    default = 1,
    help = 'Minimum matching regex occurence per file to keep in redis (1)',
    action = 'store')

    parser.add_argument('-regex',
    type = str,
    default = 'mail',
    choices=['mail', 'card', 'url', 'bitcoin'],
    help = 'Which regex wanted to be use to match',
    action = 'store')

    parser.add_argument('-key',
    type = str,
    default = "mails_categ",
    help = 'Name of the key to process in redis (same name than the wordlist concerned)',
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

    args = parser.parse_args()

    if args.regex == 'mail':
        regex = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}"
    elif args.regex == 'card':
        regex = "4[0-9]{12}(?:[0-9]{3})?"
    elif args.regex == 'bitcoin':
        regex = "[13][1-9A-HJ-NP-Za-km-z]{26,33}"

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline(False)

    publisher.channel = "youpi"

    refining_regex_dataset(r, args.key, regex, args.nbm, args.y, args.m)

if __name__ == "__main__":
    main()
