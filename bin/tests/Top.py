#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_search import Create_Common_Hash_File
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information Leak
    framework. It create a text file with the top common hash
    which are in the redis database''',
    epilog = '''The Redis database need to be populated by the script
    Populate.py before using this one.''')

    parser.add_argument('-db',
    default = 0,
    type = int,
    help = 'The name of the Redis DB',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-off',
    default = 1,
    type = int,
    metavar = 'offset',
    help = 'Starting point of the toplist',
    action = 'store')

    parser.add_argument('-top',
    default = 100,
    type = int,
    metavar = '100',
    help = 'How many occurence? top 10-50-100 ?',
    action = 'store')

    parser.add_argument('-p',
    type = str,
    default = '../graph/top',
    metavar = 'path',
    help = "pathname of the file created ex: /home/top",
    action = 'store')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    create_common_cash_file(r, args.off, args.top, args.p+str(args.top)+".top")
    cprint("LIST CREATED","green")

if __name__ == "__main__":
    main()

#OK