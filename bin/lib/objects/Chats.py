#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from datetime import datetime

from flask import url_for
# from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_chat_object import AbstractChatObject, AbstractChatObjects


from lib.objects.abstract_subtype_object import get_all_id
# from lib.data_retention_engine import update_obj_date
from lib.timeline_engine import Timeline

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None


################################################################################
################################################################################
################################################################################

class Chat(AbstractChatObject):
    """
    AIL Chat Object.
    """

    def __init__(self, id, subtype):
        super(Chat, self).__init__('chat', id, subtype)

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('chats_explorer.chats_explorer_chat', subtype=self.subtype, id=self.id)
        else:
            url = f'{baseurl}/chats/explorer/chat?subtype={self.subtype}&id={self.id}'
        return url

    def get_origin_link(self):
        if self.subtype == '00098785-7e70-5d12-a120-c5cdc1252b2b':
            username = self.get_username()
            if username:
                username = username.split(':', 2)[2]
                return f'https://t.me/{username}'

    def get_chat_instance(self):
        if self.subtype == '00098785-7e70-5d12-a120-c5cdc1252b2b':
            return 'telegram'
        elif self.subtype == 'd2426e3f-22f3-5a57-9a98-d2ae9794e683':
            return 'discord'
        else:
            return self.subtype

    def get_svg_icon(self):  # TODO
        # if self.subtype == 'telegram':
        #     style = 'fab'
        #     icon = '\uf2c6'
        # elif self.subtype == 'discord':
        #     style = 'fab'
        #     icon = '\uf099'
        # else:
        #     style = 'fas'
        #     icon = '\uf007'
        style = 'fas'
        icon = '\uf086'
        return {'style': style, 'icon': icon, 'color': '#4dffff', 'radius': 5}

    def get_meta(self, options=set(), translation_target=None):
        meta = self._get_meta(options=options)
        meta['name'] = self.get_name()
        meta['tags'] = self.get_tags(r_list=True)
        if 'icon' in options:
            meta['svg_icon'] = self.get_svg_icon()
            meta['icon'] = self.get_icon()
            meta['img'] = meta['icon']
        if 'info' in options:
            meta['info'] = self.get_info()
            if 'translation' in options and translation_target:
                meta['translation_info'] = self.translate(meta['info'], field='info', target=translation_target)
        if 'participants' in options:
            meta['participants'] = self.get_participants()
        if 'nb_participants' in options:
            meta['nb_participants'] = self.get_nb_participants()
        if 'nb_messages' in options:
            meta['nb_messages'] = self.get_nb_messages()
        if 'username' in options:
            meta['username'] = self.get_username()
            if meta['username'] and 'str_username' in options:
                meta['username'] = meta['username'].split(':', 2)[2]
        if 'subchannels' in options:
            meta['subchannels'] = self.get_subchannels()
        if 'nb_subchannels':
            meta['nb_subchannels'] = self.get_nb_subchannels()
        if 'created_at':
            meta['created_at'] = self.get_created_at(date=True)
        if 'threads' in options:
            meta['threads'] = self.get_threads()
        if 'tags_safe' in options:
            meta['tags_safe'] = self.is_tags_safe(meta['tags'])
        if 'origin_link' in options:
            meta['origin_link'] = self.get_origin_link()
        return meta

    def get_misp_object(self):
        # obj_attrs = []
        # if self.subtype == 'telegram':
        #     obj = MISPObject('telegram-account', standalone=True)
        #     obj_attrs.append(obj.add_attribute('username', value=self.id))
        #
        # elif self.subtype == 'twitter':
        #     obj = MISPObject('twitter-account', standalone=True)
        #     obj_attrs.append(obj.add_attribute('name', value=self.id))
        #
        # else:
        #     obj = MISPObject('user-account', standalone=True)
        #     obj_attrs.append(obj.add_attribute('username', value=self.id))
        #
        # first_seen = self.get_first_seen()
        # last_seen = self.get_last_seen()
        # if first_seen:
        #     obj.first_seen = first_seen
        # if last_seen:
        #     obj.last_seen = last_seen
        # if not first_seen or not last_seen:
        #     self.logger.warning(
        #         f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={first_seen}, last={last_seen}')
        #
        # for obj_attr in obj_attrs:
        #     for tag in self.get_tags():
        #         obj_attr.add_tag(tag)
        # return obj
        return

    ############################################################################
    ############################################################################

    # users that send at least a message else participants/spectator
    # correlation created by messages
    def get_users(self):
        users = set()
        accounts = self.get_correlation('user-account').get('user-account', [])
        for account in accounts:
            users.add(account[1:])
        return users

    def _get_timeline_username(self):
        return Timeline(self.get_global_id(), 'username')

    def get_username(self):
        return self._get_timeline_username().get_last_obj_id()

    def get_usernames(self):
        return self._get_timeline_username().get_objs_ids()

    def update_username_timeline(self, username_global_id, timestamp):
        self._get_timeline_username().add_timestamp(timestamp, username_global_id)

    def get_label(self):
        username = self.get_username()
        if username:
            username = username.split(':', 2)[2]
        name = self.get_name()
        if username and name:
            label = f'{username} - {name}'
        elif username:
            label = username
        elif name:
            label = name
        else:
            label = ''
        return label

    #### ChatSubChannels ####


    #### Categories ####

    #### Threads ####

    #### Messages #### TODO set parents

    # def get_last_message_id(self):
    #
    #     return r_object.hget(f'meta:{self.type}:{self.subtype}:{self.id}', 'last:message:id')

    # def add(self, timestamp, obj_id, mess_id=0, username=None, user_id=None):
    #     date = # TODO get date from object
    #     self.update_daterange(date)
    #     update_obj_date(date, self.type, self.subtype)
    #
    #
    #     # daily
    #     r_object.hincrby(f'{self.type}:{self.subtype}:{date}', self.id, 1)
    #     # all subtypes
    #     r_object.zincrby(f'{self.type}_all:{self.subtype}', 1, self.id)
    #
    #     #######################################################################
    #     #######################################################################
    #
    #     # Correlations
    #     self.add_correlation('item', '', item_id)
    #     # domain
    #     if is_crawled(item_id):
    #         domain = get_item_domain(item_id)
    #         self.add_correlation('domain', '', domain)

    # importer -> use cache for previous reply SET to_add_id: previously_imported : expire SET key -> 30 mn


class Chats(AbstractChatObjects):
    def __init__(self):
        super().__init__('chat', Chat)

    def get_name(self):
        return 'Chats'

    def get_icon(self):
        return {'fas': 'fas', 'icon': 'comment'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('chats_explorer.chats_explorer_protocols')
        else:
            url = f'{baseurl}/chats/explorer/protocols'
        return url

    def sanitize_id_to_search(self, subtypes, name_to_search):
        return name_to_search

    def get_ids_with_messages_by_subtype(self, subtype):
        return r_object.smembers(f'{self.type}_w_mess:{subtype}')

    # def get_ids_with_messages_iter(self, subtype):
    #     return sscan_iter(r_object, f'{self.type}_w_mess:{subtype}')

# TODO factorize
def get_all_subtypes():
    return ail_core.get_object_all_subtypes('chat')

def get_all():
    objs = {}
    for subtype in get_all_subtypes():
        objs[subtype] = get_all_by_subtype(subtype)
    return objs

def get_all_by_subtype(subtype):
    return get_all_id('chat', subtype)


if __name__ == '__main__':
    chat = Chat('test', 'telegram')
    r = chat.get_messages()
    print(r)
