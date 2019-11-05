#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import argparse
import datetime
import configparser

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AIL default update')
    parser.add_argument('-t', help='version tag' , type=str, dest='tag', required=True)
    args = parser.parse_args()

    if not args.tag:
        parser.print_help()
        sys.exit(0)

    # remove space
    update_tag = args.tag.replace(' ', '')

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()
    r_serv = config_loader.get_redis_conn("ARDB_DB")
    config_loader = None

    #Set current ail version
    r_serv.set('ail:version', update_tag)

    #Set current ail version
    r_serv.hset('ail:update_date', update_tag, datetime.datetime.now().strftime("%Y%m%d"))
