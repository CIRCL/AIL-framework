#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_redis_insert import *
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information
    Leak framework. Is Populate the Redis database with
    the pastes names and theirs hashed line''',
    epilog = '''This script need to be run first in order to use the others:
    Graph.py, Search.py, Top.py ...''')

    parser.add_argument('input',
    type = str,
    metavar = 'pathfolder',
    help = 'Input folder',
    action = 'store')

    parser.add_argument('-t',
    type = int,
    default = 0,
    help = 'type of population wanted 0 = set 1 = zset 2 = mix',
    choices=[0, 1, 2],
    action = 'store')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-H',
    type = str,
    default = 'md5',
    metavar='hash',
    help = 'The hash method (default md5)',
    choices=["md5", "sha1", "crc", "murmur"],
    action = 'store')

    parser.add_argument('-jmp',
    type = int,
    default = 10,
    metavar = 'jump',
    help = '''Jumping line factor. 1 = All the line are taken. X = jump X line
    (default 10)''',
    action = 'store')

    parser.add_argument('-ml',
    type = int,
    default = 1,
    metavar = 'minlnline',
    help = '''Length line factor. 1 = All the line are taken.
    X = each line >= X char (default 1)''',
    action = 'store')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline()

    redis_populate(p, listdirectory(args.input), args.ml, args.H, args.jmp, args.t)

if __name__ == "__main__":
    main()

#OK