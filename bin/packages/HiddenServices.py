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
import random

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

        self.r_serv_metadata = redis.StrictRedis(
            host=cfg.get("ARDB_Metadata", "host"),
            port=cfg.getint("ARDB_Metadata", "port"),
            db=cfg.getint("ARDB_Metadata", "db"),
            decode_responses=True)

        self.domain = domain
        self.type = type

        if type == 'onion':
            self.paste_directory = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "pastes"))
            self.paste_crawled_directory = os.path.join(self.paste_directory, cfg.get("Directories", "crawled"))
            self.paste_crawled_directory_name = cfg.get("Directories", "crawled")
            self.screenshot_directory = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "crawled_screenshot"))
        elif type == 'i2p':
            self.paste_directory = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "crawled_screenshot"))
            self.screenshot_directory = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "crawled_screenshot"))
        else:
            ## TODO: # FIXME: add error
            pass

    #todo use the right paste
    def get_last_crawled_pastes(self):
        paste_parent = self.r_serv_onion.hget('onion_metadata:{}'.format(self.domain), 'paste_parent')
        #paste_parent = paste_parent.replace(self.paste_directory, '')[1:]
        return self.get_all_pastes_domain(paste_parent)

    def get_all_pastes_domain(self, father):
        l_crawled_pastes = []
        paste_parent = father.replace(self.paste_directory, '')[1:]
        paste_childrens = self.r_serv_metadata.smembers('paste_children:{}'.format(paste_parent))
        ## TODO: # FIXME: remove me
        paste_children = self.r_serv_metadata.smembers('paste_children:{}'.format(father))
        paste_childrens = paste_childrens | paste_children
        for children in paste_childrens:
            if self.domain in children:
                l_crawled_pastes.append(children)
                l_crawled_pastes.extend(self.get_all_pastes_domain(children))
        return l_crawled_pastes

    def get_domain_random_screenshot(self, l_crawled_pastes, num_screenshot = 1):
        l_screenshot_paste = []
        for paste in l_crawled_pastes:
            ## FIXME: # TODO: remove me
            paste= paste.replace(self.paste_directory, '')[1:]

            paste = paste.replace(self.paste_crawled_directory_name, '')
            if os.path.isfile( '{}{}.png'.format(self.screenshot_directory, paste) ):
                l_screenshot_paste.append(paste[1:])

        if len(l_screenshot_paste) > num_screenshot:
            l_random_screenshot = []
            for index in random.sample( range(0, len(l_screenshot_paste)), num_screenshot ):
                l_random_screenshot.append(l_screenshot_paste[index])
            return l_random_screenshot
        else:
            return l_screenshot_paste

    def get_crawled_pastes_by_date(self, date):

        pastes_path = os.path.join(self.paste_crawled_directory, date[0:4], date[4:6], date[6:8])
        paste_parent = self.r_serv_onion.hget('onion_metadata:{}'.format(self.domain), 'last_check')

        l_crawled_pastes = []
        return l_crawled_pastes

    def get_last_crawled_pastes_fileSearch(self):

        last_check = self.r_serv_onion.hget('onion_metadata:{}'.format(self.domain), 'last_check')
        return self.get_crawled_pastes_by_date_fileSearch(last_check)

    def get_crawled_pastes_by_date_fileSearch(self, date):
        pastes_path = os.path.join(self.paste_crawled_directory, date[0:4], date[4:6], date[6:8])
        l_crawled_pastes = [f for f in os.listdir(pastes_path) if self.domain in f]
        return l_crawled_pastes
