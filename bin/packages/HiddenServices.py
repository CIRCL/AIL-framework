#!/usr/bin/python3

"""
The ``hiddenServices Class``
===================

Use it to create an object from an existing paste or other random file.

Conditions to fulfill to be able to use this class correctly:
-------------------------------------------------------------

1/ The paste need to be saved on disk somewhere (have an accessible path)
2/ The paste need to be gziped.
3/ The filepath need to look like something like this:
    /directory/source/year/month/day/paste.gz

"""

import os
import gzip
import redis

import configparser
import sys
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
from Date import Date

class HiddenServices(object):
    """
    This class representing a hiddenServices as an object.
    When created, the object will have by default some "main attributes"

    :Example:

    PST = HiddenServices("xxxxxxxx.onion", "onion")

    """

    def __init__(self, domain, type):

        configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
        if not os.path.exists(configfile):
            raise Exception('Unable to find the configuration file. \
                            Did you set environment variables? \
                            Or activate the virtualenv.')

        cfg = configparser.ConfigParser()
        cfg.read(configfile)
        self.r_serv_onion = redis.StrictRedis(
            host=cfg.get("ARDB_Onion", "host"),
            port=cfg.getint("ARDB_Onion", "port"),
            db=cfg.getint("ARDB_Onion", "db"),
            decode_responses=True)

        self.domain = domain
        self.type = type

        if type == 'onion':
            self.paste_directory = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "pastes"), cfg.get("Directories", "crawled"))
            self.screenshot_directory = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "crawled_screenshot"))
        elif type == 'i2p':
            self.paste_directory = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "crawled_screenshot"))
            self.screenshot_directory = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "crawled_screenshot"))
        else:
            ## TODO: # FIXME: add error
            pass


    def get_last_crawled_pastes(self):

        last_check = self.r_serv_onion.hget('onion_metadata:{}'.format(self.domain), 'last_check')
        return self.get_crawled_pastes_by_date(last_check)

    def get_crawled_pastes_by_date(self, date):
        pastes_path = os.path.join(self.paste_directory, date[0:4], date[4:6], date[6:8])
        l_crawled_pastes = [f for f in os.listdir(pastes_path) if self.domain in f]
        print(len(l_crawled_pastes))
        print(l_crawled_pastes)
        return l_crawled_pastes
