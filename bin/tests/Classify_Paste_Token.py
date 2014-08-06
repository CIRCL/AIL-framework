#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_words import *
from packages.imported import *
from pubsublogger import publisher

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information Leak
    framework. It create sets in redis as much as category
    defined in the file given by the argument -l ''',
    epilog = '''Example : seq 5000 | parallel -n0 -j 10
    ./classify_Paste_Token.py -nbp 200''')

    parser.add_argument('-l',
    type = str,
    default = "../files/list_categ_files",
    help = 'Path to the list_categ_files (../files/list_categ_files)',
    action = 'store')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-s',
    help = 'Datastruct type, swapping between keys & members',
    action = 'store_true')

    parser.add_argument('-nbp',
    type = int,
    default = 200,
    help = 'Nbpaste',
    action = 'store')

    parser.add_argument('-set',
    type = str,
    default = 'filelist',
    help = 'The name of the list in redis which contain the filename to tokenise',
    action = 'store')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline(False)

    publisher.channel = "youpi"

    classify_token_paste(r, args.l, args.s, args.nbp, args.set)

if __name__ == "__main__":
    main()
