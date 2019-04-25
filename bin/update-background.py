#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
Update AIL
============================

Update AIL in the background

"""

import os
import sys
import redis
import subprocess
import configparser

if __name__ == "__main__":

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

    if r_serv.scard('ail:update_v1.5') != 5:
        r_serv.delete('ail:update_error')
        r_serv.set('ail:update_in_progress', 'v1.5')
        r_serv.set('ail:current_background_update', 'v1.5')
        if not r_serv.sismember('ail:update_v1.5', 'onions'):
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', 'v1.5', 'Update-ARDB_Onions.py')
            process = subprocess.run(['python' ,update_file])

        if not r_serv.sismember('ail:update_v1.5', 'metadata'):
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', 'v1.5', 'Update-ARDB_Metadata.py')
            process = subprocess.run(['python' ,update_file])

        if not r_serv.sismember('ail:update_v1.5', 'tags'):
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', 'v1.5', 'Update-ARDB_Tags.py')
            process = subprocess.run(['python' ,update_file])

        if not r_serv.sismember('ail:update_v1.5', 'tags_background'):
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', 'v1.5', 'Update-ARDB_Tags_background.py')
            process = subprocess.run(['python' ,update_file])
        if not r_serv.sismember('ail:update_v1.5', 'crawled_screenshot'):
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', 'v1.5', 'Update-ARDB_Onions_screenshots.py')
            process = subprocess.run(['python' ,update_file])
        if r_serv.scard('ail:update_v1.5') != 5:
            r_serv.set('ail:update_error', 'Update v1.5 Failed, please relaunch the bin/update-background.py script')
        else:
            r_serv.delete('ail:update_in_progress')
            r_serv.delete('ail:current_background_script')
            r_serv.delete('ail:current_background_script_stat')
            r_serv.delete('ail:current_background_update')
