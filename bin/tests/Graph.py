#!/usr/bin/python2.7
# -*-coding:UTF-8 -*

from packages.lib_gephi import *
from packages.imported import *

def main():
    """Main Function"""

    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information
    Leak framework. It create a gephi graph to have a global
    view of the pastes but also which one are similar.''',
    epilog = '''The Redis database need to be populated by the script
    Populate.py before using this one.''')

    parser.add_argument('-t',
    type = int,
    default = 0,
    help = 'Type of the Redis population (Same arg than in Populate.py)',
    choices=[0, 2],
    action = 'store')

    parser.add_argument('-db',
    type = int,
    default = 0,
    help = 'The name of the Redis DB',
    choices=[0, 1, 2, 3, 4],
    action = 'store')

    parser.add_argument('-min',
    type = int,
    default = 3,
    help = 'minimum linked nodes (default 3)',
    action = 'store')

    parser.add_argument('-max',
    type = int,
    default = 50,
    help = 'maximum linked nodes created (execute top.py before for more info)',
    action = 'store')

    parser.add_argument('-p',
    type = str,
    default = '../graph/out',
    metavar = 'path',
    help = "pathname of the graph file created. ex: /home/graph",
    action = 'store')

    args = parser.parse_args()

    r = redis.StrictRedis(
        host='localhost',
        port=6379,
        db=args.db,
        unix_socket_path='/tmp/redis.sock')


    Gephi_Graph(r, args.p+".gexf", args.min, args.max, args.t)
    cprint("GRAPH CREATED AT:{0}.gexf".format(args.p),"green")

if __name__ == "__main__":
    main()

#OK