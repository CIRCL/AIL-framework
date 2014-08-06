#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_search import *
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = 'Analysis Information Leak framework',
    epilog = 'MSc Student Internship')

    parser.add_argument('-db',
    default = 0,
    type = int,
    help = 'The name of the Redis DB',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('name',
    type = str,
    metavar = 'pastename',
    help = 'The name of the paste',
    action = 'store')

    parser.add_argument('-min',
    type = int,
    default = 3,
    help = 'minimum linked hashs (default 3)',
    action = 'store')

    parser.add_argument('-max',
    type = int,
    default = 50,
    help = 'maximum linked hash (execute top.py to be more aware)',
    action = 'store')

    parser.add_argument('-p',
    type = str,
    default = '../graph/Search_',
    metavar = 'path',
    help = "pathname of the file created.",
    action = 'store')

    parser.add_argument('-t',
    type = int,
    default = 0,
    help = 'Type of the Redis population (Same arg than in Populate.py)',
    choices=[0, 2],
    action = 'store')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db,
        unix_socket_path='/tmp/redis.sock')


    if args.t == 2:
        paste_searching2(r, args.p+args.name+".txt", args.name, args.min, args.max)
        cprint("GRAPH CREATED AT:{0}{1}.txt".format(args.p,args.name),"green")
    elif args.t == 0:
        paste_searching(r, args.p+args.name+".txt", args.name, args.min, args.max)
        cprint("GRAPH CREATED AT:{0}{1}.txt".format(args.p,args.name),"green")
        pass


if __name__ == "__main__":
    main()
