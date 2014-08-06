#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_words import *
from packages.imported import *
from pubsublogger import publisher

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information Leak
    framework. It's here to monitor some script which take time
    and lauched in parallel, You can display which process is running on which
    paste and how much time it spent processing it''',
    epilog = 'example : ./Display_pid -p pid -db 1 -d remain')

    parser.add_argument('-d',
    type = str,
    default = 'all',
    choices=['paste', 'up', 'start', 'kb', 'all', 'pid', 'prg', 'remain', 'processed'],
    help = 'Which info to display ?',
    action = 'store')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB (default 0)',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db)

    p = r.pipeline(False)

    publisher.channel = "youpi"

    display_listof_pid(r, args.d)

if __name__ == "__main__":
    main()
