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

from lib.data_retention_engine import update_obj_date
from lib.timeline_engine import Timeline

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None


################################################################################
################################################################################
################################################################################

class ChatSubChannel(AbstractChatObject):
    """
    AIL Chat Object. (strings)
    """

    # ID -> <CHAT ID>/<SubChannel ID>  subtype = chat_instance_uuid
    def __init__(self, id, subtype):
        super(ChatSubChannel, self).__init__('chat-subchannel', id, subtype)

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
            url = url_for('chats_explorer.objects_subchannel_messages', subtype=self.subtype, id=self.id)
        else:
            url = f'{baseurl}/chats/explorer/subchannel?subtype={self.subtype}&id={self.id}'
        return url

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
        style = 'far'
        icon = '\uf086'
        return {'style': style, 'icon': icon, 'color': '#4dffff', 'radius': 5}

    # TODO TIME LAST MESSAGES

    def get_meta(self, options=set(), translation_target=None):
        meta = self._get_meta(options=options)
        meta['tags'] = self.get_tags(r_list=True)
        meta['name'] = self.get_name()
        if 'chat' in options:
            meta['chat'] = self.get_chat()
        if 'icon' in options:
            meta['icon'] = self.get_icon()
            meta['img'] = meta['icon']
        if 'nb_messages' in options:
            meta['nb_messages'] = self.get_nb_messages()
        if 'created_at' in options:
            meta['created_at'] = self.get_created_at(date=True)
        if 'threads' in options:
            meta['threads'] = self.get_threads()
        if 'participants' in options:
            meta['participants'] = self.get_participants()
        if 'nb_participants' in options:
            meta['nb_participants'] = self.get_nb_participants()
        if 'translation' in options and translation_target:
            meta['translation_name'] = self.translate(meta['name'], field='name', target=translation_target)
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

    # others optional metas, ... -> # TODO ALL meta in hset

    def _get_timeline_name(self):
        return Timeline(self.get_global_id(), 'username')

    def update_name(self, name, timestamp):
        self._get_timeline_name().add_timestamp(timestamp, name)


    # TODO # # # # # # # # # # #
    def get_users(self):
        pass

    #### Categories ####

    #### Threads ####

    #### Messages #### TODO set parents

    # def get_last_message_id(self):
    #
    #     return r_object.hget(f'meta:{self.type}:{self.subtype}:{self.id}', 'last:message:id')


class ChatSubChannels(AbstractChatObjects):
    def __init__(self):
        super().__init__('chat-subchannel', ChatSubChannel)

    def get_name(self):
        return 'Chat-SubChannels'

    def get_icon(self):
        return {'fas': 'far', 'icon': 'comments'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('chats_explorer.chats_explorer_protocols')
        else:
            url = f'{baseurl}/chats/explorer/protocols'
        return url

    def sanitize_id_to_search(self, subtypes, name_to_search):
        return name_to_search

# if __name__ == '__main__':
#     chat = Chat('test', 'telegram')
#     r = chat.get_messages()
#     print(r)
