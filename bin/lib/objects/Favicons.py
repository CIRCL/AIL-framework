#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import mmh3
import os
import sys

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

    def get_content(self, r_type='str'):
        if r_type == 'str':
            return self._get_field('content')

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    # TODO # CHANGE COLOR
    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf20a', 'color': '#1E88E5', 'radius': 5}  # f0c8 f45c

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
        obj_attrs.append(obj.add_attribute('favicon', value=self.get_content(r_type='bytes')))
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['tags'] = self.get_tags(r_list=True)
        if 'content' in options:
            meta['content'] = self.get_content()
        return meta

    # def get_links(self):
    #     # TODO GET ALL URLS FROM CORRELATED ITEMS

    def add(self, date, item_id):  # TODO correlation base 64 -> calc md5
        self._add(date, item_id)

    def create(self, content, _first_seen=None, _last_seen=None):
        if not isinstance(content, str):
            content = content.decode()
        self._set_field('content', content)
        self._create()


def create_favicon(content, url=None):  # TODO URL ????
    if isinstance(content, str):
        content = content.encode()
    favicon_id = mmh3.hash_bytes(content)
    favicon = Favicon(favicon_id)
    if not favicon.exists():
        favicon.create(content)


# TODO  ADD SEARCH FUNCTION

class Favicons(AbstractDaterangeObjects):
    """
        Favicons Objects
    """
    def __init__(self):
        super().__init__('favicon')

    def get_metas(self, obj_ids, options=set()):
        return self._get_metas(Favicon, obj_ids, options=options)

    def sanitize_name_to_search(self, name_to_search):
        return name_to_search  # TODO


# if __name__ == '__main__':
#     name_to_search = '98'
#     print(search_cves_by_name(name_to_search))
