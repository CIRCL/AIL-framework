#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_redis_insert import *
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information
    Leak framework. It Add to a temporary list the hash
    of wholes files and compare the new hash to the element of this
    list. If the hash is already inside, the file is deleted
    otherwise the hash is added in the list.''',
    epilog = '''This script need Redis to be populated before by
    ./Dir.py''')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-nbp',
    type = int,
    default = 200,
    help = 'nbpaste',
    action = 'store')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline(False)

    remove_pure_doppelganger(r, args.nbp)

if __name__ == "__main__":
    main()