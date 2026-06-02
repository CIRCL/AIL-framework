#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, AbstractSubtypeObjects, r_object

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


class Forum(AbstractSubtypeObject):
    def __init__(self, id, subtype):
        super().__init__('forum', id, subtype)

    def get_name(self):
        return self._get_field('name')

    def set_name(self, name):
        self._set_field('name', name)

    def get_info(self):
        return self._get_field('info')

    def set_info(self, info):
        self._set_field('info', info)

    def get_url(self):
        return self._get_field('url')

    def set_url(self, url):
        self._set_field('url', url)

    def get_subforums(self):
        subforums = []
        for child in self.get_childrens():
            obj_type, _, obj_id = child.split(':', 2)
            if obj_type == 'subforum':
                subforums.append(obj_id)
        return subforums

    def get_nb_subforums(self):
        return len(self.get_subforums())

    def add_post_global_id(self, post_id, post_global_id):
        r_object.hset(f'posts:{self.subtype}:{self.id}', post_id, post_global_id)

    def get_post_global_id(self, post_id):
        return r_object.hget(f'posts:{self.subtype}:{self.id}', post_id)

    def get_link(self, flask_context=False):
        if flask_context:
            return url_for('correlation.show_correlation', type=self.type, subtype=self.subtype, id=self.id)
        return f'{baseurl}/correlation/show?type={self.type}&subtype={self.subtype}&id={self.id}'

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf086', 'color': '#4dffff', 'radius': 5}

    def get_misp_object(self):
        pass

    def get_meta(self, options=set(), flask_context=False):
        meta = self._get_meta(options=options, flask_context=flask_context)
        meta['tags'] = self.get_tags(r_list=True)
        if 'name' in options:
            meta['name'] = self._get_field('name')
        if 'info' in options:
            meta['info'] = self._get_field('info')
        if 'url' in options:
            meta['url'] = self._get_field('url')
        if 'subforums' in options:
            meta['subforums'] = self.get_subforums()
        if 'nb_subforums' in options:
            meta['nb_subforums'] = self.get_nb_subforums()
        return meta

    def create(self):  # TODO
        pass

    def delete(self):
        pass


class Forums(AbstractSubtypeObjects):
    def __init__(self):
        super().__init__('forum', Forum)

    def get_name(self):
        return 'Forums'

    def get_icon(self):
        return {'fa': 'fas', 'icon': 'comments'}

    def get_link(self, flask_context=False):
        if flask_context:
            return url_for('objects_subtypes.objects_dashboard_username')
        return f'{baseurl}/objects/forums'

    def sanitize_id_to_search(self, subtypes, name_to_search):
        return name_to_search
