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
        self.tags = {}

        if type == 'onion' or type == 'regular':
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

    def remove_absolute_path_link(self, key, value):
        print(key)
        print(value)

    def get_origin_paste_name(self):
        origin_item = self.r_serv_onion.hget('onion_metadata:{}'.format(self.domain), 'paste_parent')
        if origin_item is None:
            return ''
        elif origin_item == 'auto' or origin_item == 'manual':
            return origin_item
        return origin_item.replace(self.paste_directory+'/', '')

    def get_domain_tags(self, update=False):
        if not update:
            return self.tags
        else:
            self.get_last_crawled_pastes()
            return self.tags

    def update_domain_tags(self, item):
        if self.r_serv_metadata.exists('tag:{}'.format(item)):
            p_tags = self.r_serv_metadata.smembers('tag:{}'.format(item))
        # update path here
        else:
            # need to remove it
            if self.paste_directory in item:
                p_tags = self.r_serv_metadata.smembers('tag:{}'.format(item.replace(self.paste_directory+'/', '')))
            # need to remove it
            else:
                p_tags = self.r_serv_metadata.smembers('tag:{}'.format(os.path.join(self.paste_directory, item)))
        print(p_tags)
        for tag in p_tags:
            self.tags[tag] = self.tags.get(tag, 0) + 1

    def get_first_crawled(self):
        res = self.r_serv_onion.zrange('crawler_history_{}:{}'.format(self.type, self.domain), 0, 0, withscores=True)
        if res:
            res = res[0]
            return {'root_item':res[0], 'epoch':res[1]}
        else:
            return {}

    def get_last_crawled(self):
        res = self.r_serv_onion.zrevrange('crawler_history_{}:{}'.format(self.type, self.domain), 0, 0, withscores=True)
        if res:
            res = res[0]
            return {'root_item':res[0], 'epoch':res[1]}
        else:
            return {}

    #todo use the right paste
    def get_last_crawled_pastes(self, epoch=None):
        if epoch is None:
            list_root = self.r_serv_onion.zrevrange('crawler_history_{}:{}'.format(self.type, self.domain), 0, 0)
        else:
            list_root = self.r_serv_onion.zrevrangebyscore('crawler_history_{}:{}'.format(self.type, self.domain), int(epoch), int(epoch))
        if list_root:
            return self.get_all_pastes_domain(list_root[0])
        else:
            if epoch:
                return self.get_last_crawled_pastes()
            else:
                return list_root

    def get_all_pastes_domain(self, root_item):
        if root_item is None:
            return []
        l_crawled_pastes = []
        l_crawled_pastes = self.get_item_crawled_children(root_item)
        l_crawled_pastes.append(root_item)
        self.update_domain_tags(root_item)
        return l_crawled_pastes

    def get_item_crawled_children(self, father):
        if father is None:
            return []
        l_crawled_pastes = []
        paste_parent = father.replace(self.paste_directory+'/', '')
        paste_childrens = self.r_serv_metadata.smembers('paste_children:{}'.format(paste_parent))
        ## TODO: # FIXME: remove me
        paste_children = self.r_serv_metadata.smembers('paste_children:{}'.format(father))
        paste_childrens = paste_childrens | paste_children
        for children in paste_childrens:
            if self.domain in children:
                l_crawled_pastes.append(children)
                self.update_domain_tags(children)
                l_crawled_pastes.extend(self.get_item_crawled_children(children))
        return l_crawled_pastes

    def get_item_link(self, item):
        link = self.r_serv_metadata.hget('paste_metadata:{}'.format(item), 'real_link')
        if link is None:
            if self.paste_directory in item:
                self.r_serv_metadata.hget('paste_metadata:{}'.format(item.replace(self.paste_directory+'/', '')), 'real_link')
            else:
                key = os.path.join(self.paste_directory, item)
                link = self.r_serv_metadata.hget('paste_metadata:{}'.format(key), 'real_link')
                if link:
                    self.remove_absolute_path_link(key, link)

        return link

    def get_all_links(self, l_items):
        dict_links = {}
        for item in l_items:
            link = self.get_item_link(item)
            if link:
                dict_links[item] = link
        return dict_links

    # experimental
    def get_domain_son(self, l_paste):
        if l_paste is None:
            return None

        set_domain = set()
        for paste in l_paste:
            paste_full = paste.replace(self.paste_directory+'/', '')
            paste_childrens = self.r_serv_metadata.smembers('paste_children:{}'.format(paste_full))
            ## TODO: # FIXME: remove me
            paste_children = self.r_serv_metadata.smembers('paste_children:{}'.format(paste))
            paste_childrens = paste_childrens | paste_children
            for children in paste_childrens:
                if not self.domain in children:
                    print(children)
                    set_domain.add((children.split('.onion')[0]+'.onion').split('/')[-1])

        return set_domain

    '''
    def get_all_domain_son(self, father):
        if father is None:
            return []
        l_crawled_pastes = []
        paste_parent = father.replace(self.paste_directory+'/', '')
        paste_childrens = self.r_serv_metadata.smembers('paste_children:{}'.format(paste_parent))
        ## TODO: # FIXME: remove me
        paste_children = self.r_serv_metadata.smembers('paste_children:{}'.format(father))
        paste_childrens = paste_childrens | paste_children
        for children in paste_childrens:
            if not self.domain in children:
                l_crawled_pastes.append(children)
                #self.update_domain_tags(children)
                l_crawled_pastes.extend(self.get_all_domain_son(children))

        return l_crawled_pastes
    '''

    def get_domain_random_screenshot(self, l_crawled_pastes, num_screenshot = 1):
        l_screenshot_paste = []
        for paste in l_crawled_pastes:
            ## FIXME: # TODO: remove me
            origin_paste = paste
            paste= paste.replace(self.paste_directory+'/', '')

            paste = paste.replace(self.paste_crawled_directory_name, '')
            if os.path.isfile( '{}{}.png'.format(self.screenshot_directory, paste) ):
                l_screenshot_paste.append({'screenshot': paste[1:], 'item': origin_paste})

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

    '''
    def get_last_crawled_pastes_fileSearch(self):

        last_check = self.r_serv_onion.hget('onion_metadata:{}'.format(self.domain), 'last_check')
        return self.get_crawled_pastes_by_date_fileSearch(last_check)

    def get_crawled_pastes_by_date_fileSearch(self, date):
        pastes_path = os.path.join(self.paste_crawled_directory, date[0:4], date[4:6], date[6:8])
        l_crawled_pastes = [f for f in os.listdir(pastes_path) if self.domain in f]
        return l_crawled_pastes
    '''
