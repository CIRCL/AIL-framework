#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import argparse
import datetime
import configparser

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

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    r_serv = redis.StrictRedis(
        host=cfg.get("ARDB_DB", "host"),
        port=cfg.getint("ARDB_DB", "port"),
        db=cfg.getint("ARDB_DB", "db"),
        decode_responses=True)

    #Set current ail version
    r_serv.set('ail:version', update_tag)

    #Set current ail version
    r_serv.hset('ail:update_date', update_tag, datetime.datetime.now().strftime("%Y%m%d"))
