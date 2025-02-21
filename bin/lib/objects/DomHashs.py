#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from bs4 import BeautifulSoup
from hashlib import sha256
from flask import url_for

# import warnings
# warnings.filterwarnings("ignore", category=DeprecationWarning)
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


class DomHash(AbstractDaterangeObject):
    """
    AIL Title Object.
    """

    def __init__(self, id):
        super(DomHash, self).__init__('dom-hash', id)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    # def get_content(self, r_type='str'): # TODO Get random item -> compute hash
    #     if r_type == 'str':
    #         return self._get_field('content')
    #     elif r_type == 'bytes':
    #         return self._get_field('content').encode()

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\ue58a', 'color': 'grey', 'radius': 5}

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('dom-hash')
        first_seen = self.get_first_seen()
        last_seen = self.get_last_seen()
        if first_seen:
            obj.first_seen = first_seen
        if last_seen:
            obj.last_seen = last_seen
        if not first_seen or not last_seen:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={first_seen}, last={last_seen}')

        obj_attrs.append(obj.add_attribute('dom-hash', value=self.get_id()))
        # TODO ############################# URLS
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_nb_seen(self):
        return self.get_nb_correlation('domain')

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['tags'] = self.get_tags(r_list=True)
        return meta

    def create(self, _first_seen=None, _last_seen=None):
        self._create()


def _compute_dom_hash(html_content):
    soup = BeautifulSoup(html_content, "lxml")
    to_hash = "|".join(t.name for t in soup.findAll()).encode()
    return sha256(to_hash).hexdigest()[:32]


def create(content):
    obj_id = _compute_dom_hash(content)
    obj = DomHash(obj_id)
    if not obj.exists():
        obj.create()
    return obj


class DomHashs(AbstractDaterangeObjects):
    """
        Titles Objects
    """
    def __init__(self):
        super().__init__('dom-hash', DomHash)

    def get_name(self):
        return 'DomHashs'

    def get_icon(self):
        return {'fa': 'fa-solid', 'icon': 'trowel-bricks'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_dom_hash.objects_dom_hashs')
        else:
            url = f'{baseurl}/objects/dom-hashs'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search


# if __name__ == '__main__':
#     # from lib import crawlers
#     # from lib.objects import Items
#     # for item in Items.get_all_items_objects(filters={'sources': ['crawled']}):
#     #     title_content = crawlers.extract_title_from_html(item.get_content())
#     #     if title_content:
#     #         print(item.id, title_content)
#     #         title = create_title(title_content)
#     #         title.add(item.get_date(), item.id)
#     titles = Titles()
#     # for r in titles.get_ids_iterator():
#     #     print(r)
#     r = titles.search_by_id('f7d57B', r_pos=True, case_sensitive=False)
#     print(r)
