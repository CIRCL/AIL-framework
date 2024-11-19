#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from hashlib import sha256
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

# TODO NEW ABSTRACT OBJECT -> daterange for all objects ????

class Etag(AbstractDaterangeObject):
    """
    AIL Etag Object.
    """

    def __init__(self, obj_id):
        super(Etag, self).__init__('etag', obj_id)

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
        return {'style': 'fas', 'icon': '\uf02b', 'color': '#556F65', 'radius': 5}

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('etag')
        first_seen = self.get_first_seen()
        last_seen = self.get_last_seen()
        if first_seen:
            obj.first_seen = first_seen
        if last_seen:
            obj.last_seen = last_seen
        if not first_seen or not last_seen:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={first_seen}, last={last_seen}')

        obj_attrs.append(obj.add_attribute('etag', value=self.get_content()))
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
        meta['content'] = self.get_content()
        return meta

    def create(self, content, _first_seen=None, _last_seen=None):
        if not isinstance(content, str):
            content = content.decode()
        self._set_field('content', content)
        self._create()


def create(content):
    if isinstance(content, str):
        content = content.encode()
    obj_id = sha256(content).hexdigest()
    etag = Etag(obj_id)
    if not etag.exists():
        etag.create(content)
    return etag


class Etags(AbstractDaterangeObjects):
    """
        Etags Objects
    """
    def __init__(self):
        super().__init__('etag', Etag)

    def get_name(self):
        return 'Etags'

    def get_icon(self):
        return {'fa': 'fas', 'icon': 'tag'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_etag.objects_etags')
        else:
            url = f'{baseurl}/objects/etags'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search  # TODO


# if __name__ == '__main__':
#     name_to_search = '98'
#     print(search_cves_by_name(name_to_search))
