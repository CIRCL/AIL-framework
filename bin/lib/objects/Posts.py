#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from datetime import datetime
from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_object import AbstractObject, r_object

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


class Post(AbstractObject):
    def __init__(self, id):
        super().__init__('post', id)

    def exists(self):
        return r_object.exists(f'meta:{self.type}:{self.id}')

    def get_link(self, flask_context=False):
        if flask_context:
            return url_for('correlation.show_correlation', type=self.type, subtype='', id=self.id)
        return f'{baseurl}/correlation/show?type={self.type}&subtype=&id={self.id}'

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf075', 'color': '#4dffff', 'radius': 5}

    def get_misp_object(self):
        pass

    def get_timestamp(self):
        dirs = self.id.split('/')
        if len(dirs) >= 3:
            return dirs[2]
        return None

    def get_date(self):
        timestamp = self.get_timestamp()
        if timestamp:
            return datetime.utcfromtimestamp(float(timestamp)).strftime('%Y%m%d')

    def get_last_full_date(self):
        timestamp = self.get_timestamp()
        if timestamp:
            return datetime.utcfromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def get_post_id(self):
        return os.path.basename(self.id)

    def set_content(self, content):
        self._set_field('content', content)

    def get_content(self, r_type='str'):
        content = self._get_field('content')
        if not content:
            content = ''
        if r_type == 'str':
            return content
        if r_type == 'bytes':
            return content.encode()

    def get_state(self):
        return self._get_field('state')

    def set_state(self, state):
        self._set_field('state', state)

    # TODO:
    #   - Language
    #   - Translation
    #   - Reactions
    #   - URLs
    #   - Images
    #   - Attachments
    def get_meta(self, options=set(), timestamp=None, flask_context=False):
        meta = self._get_meta(options=options, flask_context=flask_context)
        meta['tags'] = self.get_tags(r_list=True)
        if not timestamp:
            timestamp = self.get_timestamp()
        timestamp = datetime.utcfromtimestamp(float(timestamp))
        meta['date'] = timestamp.strftime('%Y-%m-%d')
        meta['hour'] = timestamp.strftime('%H:%M:%S')
        meta['full_date'] = timestamp.isoformat(' ')
        if 'content' in options:
            meta['content'] = self.get_content()
        if 'timestamp' in options:
            meta['timestamp'] = self.get_timestamp()
        if 'state' in options:
            meta['state'] = self.get_state()
        return meta

    def create(self):
        pass

    def delete(self):
        self._delete()
