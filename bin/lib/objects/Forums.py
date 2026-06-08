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
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects, r_object

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


class Forum(AbstractDaterangeObject):
    def __init__(self, id):
        super().__init__('forum', id)

    def get_forum_type(self):
        return self._get_field('forum_type')

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

    def get_orphan_subforums(self):
        return r_object.smembers(f'subforums:orphans:{self.get_forum_type()}:{self.id}')

    def get_nb_orphan_subforums(self):
        return len(self.get_orphan_subforums())

    def add_orphan_subforum(self, subforum_global_id):
        r_object.sadd(f'subforums:orphans:{self.get_forum_type()}:{self.id}', subforum_global_id)

    def remove_orphan_subforum(self, subforum_global_id):
        r_object.srem(f'subforums:orphans:{self.get_forum_type()}:{self.id}', subforum_global_id)

    def is_orphan_subforum(self, subforum_global_id):
        return r_object.sismember(f'subforums:orphans:{self.get_forum_type()}:{self.id}', subforum_global_id)

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
        if 'forum_type' in options:
            meta['forum_type'] = self.get_forum_type()
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
        if 'orphan_subforums' in options:
            meta['orphan_subforums'] = self.get_orphan_subforums()
        if 'nb_orphan_subforums' in options:
            meta['nb_orphan_subforums'] = self.get_nb_orphan_subforums()
        return meta

    def create(self, forum_type, name=None, url=None, info=None):
        if not self.exists():
            self._set_field('forum_type', forum_type)
            self._add_create()
        if name:
            self.set_name(name)
        if url:
            self.set_url(url)
        if info:
            self.set_info(info)
        return self

    def delete(self):
        self._delete()

def get_forums():
    return Forums().get_ids()

class Forums(AbstractDaterangeObjects):
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

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search
