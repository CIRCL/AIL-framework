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
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, AbstractSubtypeObjects

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


class Forum(AbstractSubtypeObject):
    def __init__(self, id, subtype):
        super().__init__('forum', id, subtype)

    def get_link(self, flask_context=False):
        if flask_context:
            return url_for('correlation.show_correlation', type=self.type, subtype=self.subtype, id=self.id)
        return f'{baseurl}/correlation/show?type={self.type}&subtype={self.subtype}&id={self.id}'

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf086', 'color': '#4dffff', 'radius': 5}

    def get_meta(self, options=set(), flask_context=False):
        meta = self._get_meta(options=options, flask_context=flask_context)
        meta['tags'] = self.get_tags(r_list=True)
        if 'title' in options:
            meta['title'] = self._get_field('title')
        if 'info' in options:
            meta['info'] = self._get_field('info')
        if 'url' in options:
            meta['url'] = self._get_field('url')
        return meta


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
