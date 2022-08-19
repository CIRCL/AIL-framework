#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from io import BytesIO
from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_object import AbstractObject

config_loader = ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
SCREENSHOT_FOLDER = config_loader.get_files_directory('screenshot')
config_loader = None

class Screenshot(AbstractObject):
    """
    AIL Screenshot Object. (strings)
    """

    # ID = SHA256
    def __init__(self, id):
        super(Screenshot, self).__init__('screenshot', id)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', object_type=self.type, correlation_id=self.id)
        else:
            url = f'{baseurl}/correlation/show_correlation?object_type={self.type}&correlation_id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf03e', 'color': '#E1F5DF', 'radius':5}

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

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('file')

        obj_attrs.append( obj.add_attribute('sha256', value=self.id) )
        obj_attrs.append( obj.add_attribute('attachment', value=self.id, data=self.get_file_content()) )
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_meta(self, options=set()):
        meta = {}
        meta['id'] = self.id
        metadata_dict['img'] = get_screenshot_rel_path(sha256_string) ######### # TODO: Rename ME ??????
        meta['tags'] = self.get_tags()
        # TODO: ADD IN ABSTRACT CLASS
        #meta['is_tags_safe'] = Tag.is_tags_safe(metadata_dict['tags']) ################## # TODO: ADD IN ABSZTRACT CLASS
        return meta

    ############################################################################
    ############################################################################
    ############################################################################

    def exist_correlation(self):
        pass

    ############################################################################
    ############################################################################

def get_screenshot_dir():
    return SCREENSHOT_FOLDER

# get screenshot relative path
def get_screenshot_rel_path(sha256_str, add_extension=False):
    screenshot_path =  os.path.join(sha256_str[0:2], sha256_str[2:4], sha256_str[4:6], sha256_str[6:8], sha256_str[8:10], sha256_str[10:12], sha256_str[12:])
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


#if __name__ == '__main__':
