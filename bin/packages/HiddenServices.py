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
import sys
import time
import gzip
import redis
import random

from io import BytesIO
import zipfile

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
from Date import Date

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

class HiddenServices(object):
    """
    This class representing a hiddenServices as an object.
    When created, the object will have by default some "main attributes"

    :Example:

    PST = HiddenServices("xxxxxxxx.onion", "onion")

    """

    def __init__(self, domain, type, port=80):

        config_loader = ConfigLoader.ConfigLoader()
        self.r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
        self.r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")

        self.PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'

        self.domain = domain
        self.type = type
        self.port = port
        self.tags = {}

        if type == 'onion' or type == 'regular':
            self.paste_directory = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes"))
            self.paste_crawled_directory = os.path.join(self.paste_directory, config_loader.get_config_str("Directories", "crawled"))
            self.paste_crawled_directory_name = config_loader.get_config_str("Directories", "crawled")
            self.screenshot_directory = config_loader.get_files_directory('screenshot')
        elif type == 'i2p':
            self.paste_directory = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "crawled_screenshot"))
            self.screenshot_directory = config_loader.get_files_directory('screenshot')
        else:
            ## TODO: # FIXME: add error
            pass

        config_loader = None

    #def remove_absolute_path_link(self, key, value):
    #    print(key)
    #    print(value)

    def update_item_path_children(self, key, children):
        if self.PASTES_FOLDER in children:
            self.r_serv_metadata.srem(key, children)
            children = children.replace(self.PASTES_FOLDER, '', 1)
            self.r_serv_metadata.sadd(key, children)
        return children

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
        if item:

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
            for tag in p_tags:
                self.tags[tag] = self.tags.get(tag, 0) + 1

    def extract_epoch_from_history(self, crawled_history):
        epoch_list = []
        for res, epoch_val in crawled_history:
            epoch_val = int(epoch_val) # force int
            try:
                # domain down
                if int(res) == epoch_val:
                    status = False
                # domain up
                else:
                    status = True
            except ValueError:
                status = True
            epoch_val = int(epoch_val) # force int
            epoch_list.append((epoch_val, time.strftime('%Y/%m/%d - %H:%M.%S', time.gmtime(epoch_val)), status))
        return epoch_list

    def get_domain_crawled_history(self):
        return self.r_serv_onion.zrange('crawler_history_{}:{}:{}'.format(self.type, self.domain, self.port), 0, -1, withscores=True)

    def get_first_crawled(self):
        res = self.r_serv_onion.zrange('crawler_history_{}:{}:{}'.format(self.type, self.domain, self.port), 0, 0, withscores=True)
        if res:
            res = res[0]
            return {'root_item':res[0], 'epoch':int(res[1])}
        else:
            return {}

    def get_last_crawled(self):
        res = self.r_serv_onion.zrevrange('crawler_history_{}:{}:{}'.format(self.type, self.domain, self.port), 0, 0, withscores=True)
        if res:
            return {'root_item':res[0][0], 'epoch':res[0][1]}
        else:
            return {}

    #todo use the right paste
    def get_domain_crawled_core_item(self, epoch=None):
        core_item = {}
        if epoch:
            list_root = self.r_serv_onion.zrevrangebyscore('crawler_history_{}:{}:{}'.format(self.type, self.domain, self.port), int(epoch), int(epoch))
            if list_root:
                core_item['root_item'] = list_root[0]
                core_item['epoch'] = epoch
                return core_item

        # no history found for this epoch
        if not core_item:
            return self.get_last_crawled()

    #todo use the right paste
    def get_last_crawled_pastes(self, item_root=None):
        if item_root is None:
            item_root = self.get_domain_crawled_core_item()
            if item_root:
                item_root = item_root['root_item']
        return self.get_all_pastes_domain(item_root)

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
        key = 'paste_children:{}'.format(father)
        paste_childrens = self.r_serv_metadata.smembers(key)
        for children in paste_childrens:
            children = self.update_item_path_children(key, children)
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
                #if link:
                    #self.remove_absolute_path_link(key, link)

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
            paste_childrens = self.r_serv_metadata.smembers('paste_children:{}'.format(paste))
            for children in paste_childrens:
                if not self.domain in children:
                    set_domain.add((children.split('.onion')[0]+'.onion').split('/')[-1])

        return set_domain

    '''
    def get_all_domain_son(self, father):
        if father is None:
            return []
        l_crawled_pastes = []
        paste_childrens = self.r_serv_metadata.smembers('paste_children:{}'.format(father))
        for children in paste_childrens:
            if not self.domain in children:
                l_crawled_pastes.append(children)
                #self.update_domain_tags(children)
                l_crawled_pastes.extend(self.get_all_domain_son(children))

        return l_crawled_pastes
    '''

    def get_item_screenshot(self, item):
        screenshot = self.r_serv_metadata.hget('paste_metadata:{}'.format(item), 'screenshot')
        if screenshot:
            screenshot =  os.path.join(screenshot[0:2], screenshot[2:4], screenshot[4:6], screenshot[6:8], screenshot[8:10], screenshot[10:12], screenshot[12:])
            return screenshot
        return ''

    def get_domain_random_screenshot(self, l_crawled_pastes, num_screenshot = 1):
        l_screenshot_paste = []
        for paste in l_crawled_pastes:
            ## FIXME: # TODO: remove me
            origin_paste = paste
            paste= paste.replace(self.paste_directory+'/', '')

            screenshot = self.get_item_screenshot(paste)
            if screenshot:
                l_screenshot_paste.append({'screenshot': screenshot, 'item': origin_paste})

        if len(l_screenshot_paste) > num_screenshot:
            l_random_screenshot = []
            for index in random.sample( range(0, len(l_screenshot_paste)), num_screenshot ):
                l_random_screenshot.append(l_screenshot_paste[index])
            return l_random_screenshot
        else:
            return l_screenshot_paste

    def get_all_domain_screenshot(self, l_crawled_pastes, filename=False):
        l_screenshot_paste = []
        for paste in l_crawled_pastes:
            ## FIXME: # TODO: remove me
            origin_paste = paste
            paste= paste.replace(self.paste_directory+'/', '')

            screenshot = self.get_item_screenshot(paste)
            if screenshot:
                screenshot = screenshot + '.png'
                screenshot_full_path = os.path.join(self.screenshot_directory_screenshot, screenshot)
                if filename:
                    screen_file_name = os.path.basename(paste) + '.png'
                    l_screenshot_paste.append( (screenshot_full_path, screen_file_name) )
                else:
                    l_screenshot_paste.append(screenshot_full_path)
        return l_screenshot_paste

    def get_all_item_full_path(self, l_items, filename=False):
        l_full_items = []
        for item in l_items:
            item = os.path.join(self.PASTES_FOLDER, item)
            if filename:
                file_name = os.path.basename(item) + '.gz'
                l_full_items.append( (item, file_name) )
            else:
                l_full_items.append(item)
        return l_full_items

    def get_crawled_pastes_by_date(self, date):

        pastes_path = os.path.join(self.paste_crawled_directory, date[0:4], date[4:6], date[6:8])
        paste_parent = self.r_serv_onion.hget('onion_metadata:{}'.format(self.domain), 'last_check')

        l_crawled_pastes = []
        return l_crawled_pastes

    def get_all_har(self, l_pastes, filename=False):
        all_har = []
        for item in l_pastes:
            if filename:
                all_har.append( (self.get_item_har(item), os.path.basename(item) + '.json') )
            else:
                all_har.append(self.get_item_har(item))
        return all_har


    def get_item_har(self, item_path):
        item_path = item_path.replace('{}/'.format(self.paste_crawled_directory_name), '', 1)
        har_path = os.path.join(self.screenshot_directory, item_path) + '.json'
        return har_path

    def create_domain_basic_archive(self, l_pastes):
        all_har = self.get_all_har(l_pastes, filename=True)
        all_screenshot = self.get_all_domain_screenshot(l_pastes, filename=True)
        all_items = self.get_all_item_full_path(l_pastes, filename=True)

        # try:

        # zip buffer
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "a") as zf:

            #print(all_har)
            self.write_in_zip_buffer(zf, all_har)
            self.write_in_zip_buffer(zf, all_screenshot)
            self.write_in_zip_buffer(zf, all_items)

            # write map url
            map_file_content = self.get_metadata_file(l_pastes).encode()
            zf.writestr( '_URL_MAP_', BytesIO(map_file_content).getvalue())

        zip_buffer.seek(0)
        return zip_buffer

        # except Exception as e:
        #     print(e)
        #     return 'Server Error'

    def write_in_zip_buffer(self, zf, list_file):
        for file_path, file_name in list_file:
            with open(file_path, "rb") as f:
                har_content = f.read()
                zf.writestr( file_name, BytesIO(har_content).getvalue())

    def get_metadata_file(self, list_items):
        file_content = ''
        dict_url = self.get_all_links(list_items)
        for key in dict_url:
            file_content = '{}\n{}    :    {}'.format(file_content, os.path.basename(key), dict_url[key])
        return file_content


    '''
    def get_last_crawled_pastes_fileSearch(self):

        last_check = self.r_serv_onion.hget('onion_metadata:{}'.format(self.domain), 'last_check')
        return self.get_crawled_pastes_by_date_fileSearch(last_check)

    def get_crawled_pastes_by_date_fileSearch(self, date):
        pastes_path = os.path.join(self.paste_crawled_directory, date[0:4], date[4:6], date[6:8])
        l_crawled_pastes = [f for f in os.listdir(pastes_path) if self.domain in f]
        return l_crawled_pastes
    '''
