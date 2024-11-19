#!/usr/bin/env python3
# -*-coding:UTF-8 -*
import base64

import mmh3
import os
import sys

from io import BytesIO

from flask import url_for
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects

config_loader = ConfigLoader()
r_objects = config_loader.get_db_conn("Kvrocks_Objects")
FAVICON_FOLDER = config_loader.get_files_directory('favicons')
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


class Favicon(AbstractDaterangeObject):
    """
    AIL Favicon Object.
    """

    def __init__(self, id):
        super(Favicon, self).__init__('favicon', id)

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
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    # TODO # CHANGE COLOR
    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf089', 'color': '#E1F5D0', 'radius': 5}  # f0c8 f45c f089

    def get_rel_path(self): # TODO USE MUMUR HASH
        rel_path = os.path.join(self.id[0:1], self.id[1:2], self.id[2:3], self.id[3:4], self.id[4:5], self.id[5:6], self.id[6:])
        return rel_path

    def get_filepath(self):
        filename = os.path.join(FAVICON_FOLDER, self.get_rel_path())
        return os.path.realpath(filename)

    def get_file_content(self, r_type='str'):
        filepath = self.get_filepath()
        if r_type == 'str':
            with open(filepath, 'rb') as f:
                file_content = f.read()
            b64 = base64.b64encode(file_content)
            # b64 = base64.encodebytes(file_content)
            return b64.decode()
        elif r_type == 'io':
            with open(filepath, 'rb') as f:
                file_content = BytesIO(f.read())
                return file_content

    def get_content(self, r_type='str'):
        return self.get_file_content()

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('favicon')
        first_seen = self.get_first_seen()
        last_seen = self.get_last_seen()
        if first_seen:
            obj.first_seen = first_seen
        if last_seen:
            obj.last_seen = last_seen
        if not first_seen or not last_seen:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={first_seen}, last={last_seen}')

        obj_attrs.append(obj.add_attribute('favicon-mmh3', value=self.id))
        obj_attrs.append(obj.add_attribute('favicon', value=self.get_content()))
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['img'] = self.id
        meta['tags'] = self.get_tags(r_list=True)
        if 'content' in options:
            meta['content'] = self.get_content()
        if 'tags_safe' in options:
            meta['tags_safe'] = self.is_tags_safe(meta['tags'])
        return meta

    def create(self, content):  # TODO first seen / last seen options
        filepath = self.get_filepath()
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filepath, 'wb') as f:
            f.write(content)
        self._create()

def create(b_content, size_limit=5000000, b64=False, force=False):
    if isinstance(b_content, str):
        b_content = b_content.encode()
    b64 = base64.encodebytes(b_content)  # newlines inserted after every 76 bytes of output
    favicon_id = str(mmh3.hash(b64))
    favicon = Favicon(favicon_id)
    if not favicon.exists():
        favicon.create(b_content)
    return favicon

class Favicons(AbstractDaterangeObjects):
    """
        Favicons Objects
    """
    def __init__(self):
        super().__init__('favicon', Favicon)

    def get_name(self):
        return 'Favicons'

    def get_icon(self):
        return {'fa': 'fas', 'icon': 'star-half'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_favicon.objects_favicons')
        else:
            url = f'{baseurl}/objects/favicons'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search  # TODO


# if __name__ == '__main__':
#     name_to_search = '98'
#     print(search_cves_by_name(name_to_search))
