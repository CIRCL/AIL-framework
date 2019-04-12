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

    if r_serv.exists('ail:update_v1.5'):
        onions_update_status = r_serv.get('v1.5:onions')
        if onions_update_status is None:
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', 'v1.4', 'Update-ARDB_Onions.py')
            process = subprocess.run(['python' ,update_file])

        metadata_update_status = r_serv.get('v1.5:metadata')
        if metadata_update_status is None:
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', 'v1.4', 'Update-ARDB_Metadata.py')
            process = subprocess.run(['python' ,update_file])

        tags_update_status = r_serv.get('v1.5:tags')
        if tags_update_status is None:
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', 'v1.4', 'Update-ARDB_Tags.py')
            process = subprocess.run(['python' ,update_file])

        tags_background_update_status = r_serv.get('v1.5:tags_background')
        if tags_background_update_status is None:
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', 'v1.4', 'Update-ARDB_Tags_background.py')
            process = subprocess.run(['python' ,update_file])
