#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import base64
import os
import re
import sys

from hashlib import sha256
from io import BytesIO
from flask import url_for
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_object import AbstractObject
# from lib import data_retention_engine

config_loader = ConfigLoader()
r_serv_metadata = config_loader.get_db_conn("Kvrocks_Objects")
SCREENSHOT_FOLDER = config_loader.get_files_directory('screenshot')
config_loader = None


class Screenshot(AbstractObject):
    """
    AIL Screenshot Object. (strings)
    """

    # ID = SHA256
    def __init__(self, screenshot_id):
        super(Screenshot, self).__init__('screenshot', screenshot_id)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def exists(self):
        return os.path.isfile(self.get_filepath())

    def get_last_seen(self):
        dates = self.get_dates()
        date = 0
        for d in dates:
            if int(d) > int(date):
                date = d
        return date

    def get_dates(self):
        dates = []
        for i_id in self.get_correlation('item').get('item'):
            if i_id.startswith(':crawled'):
                i_id = i_id.split('/', 4)
                dates.append(f'{i_id[1]}{i_id[2]}{i_id[3]}')
        return dates

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf03e', 'color': '#E1F5DF', 'radius': 5}

    def get_rel_path(self, add_extension=False):
        rel_path = os.path.join(self.id[0:2], self.id[2:4], self.id[4:6], self.id[6:8], self.id[8:10], self.id[10:12], self.id[12:])
        if add_extension:
            rel_path = f'{rel_path}.png'
        return rel_path

    def get_filepath(self):
        filename = os.path.join(SCREENSHOT_FOLDER, self.get_rel_path(add_extension=True))
        return os.path.realpath(filename)

    def get_file_content(self):
        filepath = self.get_filepath()
        with open(filepath, 'rb') as f:
            file_content = BytesIO(f.read())
        return file_content

    def get_content(self):
        return self.get_file_content()

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('file')

        obj_attrs.append(obj.add_attribute('sha256', value=self.id))
        obj_attrs.append(obj.add_attribute('attachment', value=self.id, data=self.get_file_content()))
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_meta(self, options=set()):
        meta = self.get_default_meta()
        meta['img'] = get_screenshot_rel_path(self.id)  ######### # TODO: Rename ME ??????
        meta['tags'] = self.get_tags(r_list=True)
        if 'tags_safe' in options:
            meta['tags_safe'] = self.is_tags_safe(meta['tags'])
        return meta

def get_screenshot_dir():
    return SCREENSHOT_FOLDER

# get screenshot relative path
def get_screenshot_rel_path(sha256_str, add_extension=False):
    screenshot_path = os.path.join(sha256_str[0:2], sha256_str[2:4], sha256_str[4:6], sha256_str[6:8], sha256_str[8:10], sha256_str[10:12], sha256_str[12:])
    if add_extension:
        screenshot_path = f'{screenshot_path}.png'
    return screenshot_path


def get_all_screenshots():
    screenshots = []
    screenshot_dir = os.path.join(os.environ['AIL_HOME'], SCREENSHOT_FOLDER)
    for root, dirs, files in os.walk(screenshot_dir):
        for file in files:
            screenshot_path = f'{root}{file}'
            screenshot_id = screenshot_path.replace(SCREENSHOT_FOLDER, '').replace('/', '')[:-4]
            screenshots.append(screenshot_id)
    return screenshots

def get_screenshots_obj_iterator(filters=[]):
    screenshot_dir = os.path.join(os.environ['AIL_HOME'], SCREENSHOT_FOLDER)
    for root, dirs, files in os.walk(screenshot_dir):
        for file in files:
            screenshot_path = f'{root}{file}'
            screenshot_id = screenshot_path.replace(SCREENSHOT_FOLDER, '').replace('/', '')[:-4]
            yield Screenshot(screenshot_id)

# FIXME STR SIZE LIMIT
def create_screenshot(content, size_limit=5000000, b64=True, force=False):
    size = (len(content)*3) / 4
    if size <= size_limit or size_limit < 0 or force:
        if b64:
            content = base64.standard_b64decode(content.encode())
        screenshot_id = sha256(content).hexdigest()
        screenshot = Screenshot(screenshot_id)
        if not screenshot.exists():
            filepath = screenshot.get_filepath()
            dirname = os.path.dirname(filepath)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(filepath, 'wb') as f:
                f.write(content)
        return screenshot
    return  None

def sanitize_screenshot_name_to_search(name_to_search): # TODO FILTER NAME
    return name_to_search

def search_screenshots_by_name(name_to_search, r_pos=False):
    screenshots = {}
    # for subtype in subtypes:
    r_name = sanitize_screenshot_name_to_search(name_to_search)
    if not name_to_search or isinstance(r_name, dict):
        return screenshots
    r_name = re.compile(r_name)
    for screenshot_name in get_all_screenshots():
        res = re.search(r_name, screenshot_name)
        if res:
            screenshots[screenshot_name] = {}
            if r_pos:
                screenshots[screenshot_name]['hl-start'] = res.start()
                screenshots[screenshot_name]['hl-end'] = res.end()
    return screenshots


# if __name__ == '__main__':
#     obj_id = ''
#     obj = Screenshot(obj_id)
#     obj.get_last_seen()
