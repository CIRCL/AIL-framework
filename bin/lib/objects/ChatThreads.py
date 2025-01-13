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


config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None


################################################################################
################################################################################
################################################################################

class ChatThread(AbstractChatObject):
    """
    AIL Chat Object. (strings)
    """

    def __init__(self, id, subtype):
        super().__init__('chat-thread', id, subtype)

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
            url = url_for('chats_explorer.objects_thread_messages', subtype=self.subtype, id=self.id)
        else:
            url = f'{baseurl}/chats/explorer/thread?subtype={self.subtype}&id={self.id}'
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
        style = 'fas'
        icon = '\uf7a4'
        return {'style': style, 'icon': icon, 'color': '#4dffff', 'radius': 5}

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['subtype'] = self.subtype
        meta['tags'] = self.get_tags(r_list=True)
        if 'name':
            meta['name'] = self.get_name()
        if 'nb_messages':
            meta['nb_messages'] = self.get_nb_messages()
        if 'participants':
            meta['participants'] = self.get_participants()
        if 'nb_participants':
            meta['nb_participants'] = self.get_nb_participants()
        # created_at ???
        return meta

    def get_misp_object(self):
        return

    def create(self, container_obj, message_id):
        if message_id:
            parent_message = container_obj.get_obj_by_message_id(message_id)
            if parent_message:  # TODO EXCEPTION IF DON'T EXISTS
                self.set_parent(obj_global_id=parent_message)
                _, _, parent_id = parent_message.split(':', 2)
                self.add_correlation('message', '', parent_id)
        else:
            self.set_parent(obj_global_id=container_obj.get_global_id())
            self.add_correlation(container_obj.get_type(), container_obj.get_subtype(r_str=True), container_obj.get_id())

def create(thread_id, chat_instance, chat_id, subchannel_id, message_id, container_obj):
    if container_obj.get_type() == 'chat':
        new_thread_id = f'{chat_id}/{thread_id}'
    # sub-channel
    else:
        new_thread_id = f'{chat_id}/{subchannel_id}/{thread_id}'

    thread = ChatThread(new_thread_id, chat_instance)
    if not thread.is_children():
        thread.create(container_obj, message_id)
    return thread

class ChatThreads(AbstractChatObjects):
    def __init__(self):
        super().__init__('chat-thread', ChatThread)

    def get_name(self):
        return 'Chat-Threads'

    def get_icon(self):
        return {'fas': 'fas', 'icon': 'grip-lines'}

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
