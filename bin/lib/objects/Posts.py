#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from datetime import datetime
from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_object import AbstractObject, r_object
from lib.objects import UsersAccount

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
        icon = '''<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
    <path d="M0 0h24v24H0z" fill="none" />
    <path fill="currentColor" d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2M6 9h12v2H6m8 3H6v-2h8m4-4H6V6h12" />
</svg>'''
        return {'style': 'svg', 'icon': icon, 'color': '#7E57C2', 'radius': 5}

    def get_misp_object(self):
        pass

    def get_timestamp(self):
        dirs = self.id.split('/')
        if len(dirs) >= 2:
            return dirs[1]
        return None

    def get_forum_id(self):
        return self.id.split('/', 1)[0]

    def get_subforum(self):
        subforum = self.get_correlation('subforum')
        if subforum.get('subforum'):
            subforum = f'subforum:{self.get_forum_id()}:{subforum["subforum"].pop()}'
            return subforum
        return None

    def get_thread(self):
        thread = self.get_correlation('forum-thread')
        if thread.get('forum-thread'):
            thread = f'forum-thread:{self.get_forum_id()}:{thread["forum-thread"].pop()}'
            return thread
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

    def get_user_account(self, meta=False):
        user_account = self.get_correlation('user-account')
        if user_account.get('user-account'):
            user_account = f'user-account:{user_account["user-account"].pop()}'
            if meta:
                _, user_account_subtype, user_account_id = user_account.split(':', 2)
                user_account = UsersAccount.UserAccount(user_account_id, user_account_subtype).get_meta(options={'icon', 'username', 'username_meta'})
            return user_account
        return None

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

    def get_container(self):
        thread = self.get_thread()
        if thread:
            return thread
        else:
            parent_gid = self.get_parent()
            if parent_gid:
                return parent_gid
        return None

    # TODO ADD SUBFORUMS PARENT ???
    def get_objs_container(self, root=False):
        objs_containers = set()
        # forum
        objs_containers.add(f'forum::{self.get_forum_id()}')
        if not root:
            # subforum s ????
            subforum = self.get_subforum()
            if subforum:
                objs_containers.add(subforum)
            # thread
            thread = self.get_thread()
            if thread:
                objs_containers.add(thread)
            # user account
            user_account = self.get_user_account()
            if user_account:
                objs_containers.add(user_account)
        return objs_containers

    # TODO:
    #   - Reactions
    #   - URLs
    #   - Images
    #   - Attachments
    def get_meta(self, options=set(), timestamp=None, translation_target=None, flask_context=False):
        meta = self.get_default_meta(options=options)
        meta['tags'] = self.get_tags(r_list=True)
        if 'link' in options:
            meta['link'] = self.get_link(flask_context=flask_context)
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
        if 'user-account' in options:
            meta['user-account'] = self.get_user_account(meta=True)
            if not meta['user-account']:
                meta['user-account'] = {'id': 'UNKNOWN'}
        if 'translation' in options and translation_target:
            source = meta.get('language')
            meta['translation'] = self.translate(content=meta.get('content'), source=source, target=translation_target)
        return meta

    def create(self, post_id, timestamp, content, parent_thread, forum_obj, state=None, quote_ids=None):
        if content:
            self.set_content(content)
        if state:
            self.set_state(state)
        return parent_thread.add_post(self, post_id, timestamp, forum_obj, quote_ids=quote_ids)

    def delete(self):
        self._delete()

# TODO function to create Post ID
# def get_post():
#     # build ID
#     # Build object
#     # check if exists
#     #   create object
#     # return post
#
#     pass
