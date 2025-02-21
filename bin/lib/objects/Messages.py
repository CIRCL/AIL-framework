#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys

from datetime import datetime

from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ail_core import get_ail_uuid
from lib.objects.abstract_object import AbstractObject
from lib.ConfigLoader import ConfigLoader
from lib import Language
from lib.objects import UsersAccount
from lib.data_retention_engine import update_obj_date, get_obj_date_first
# TODO Set all messages ???


from flask import url_for

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
# r_content = config_loader.get_db_conn("Kvrocks_Content")
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


# TODO SAVE OR EXTRACT MESSAGE SOURCE FOR ICON ?????????
# TODO iterate on all objects
# TODO also add support for small objects ????

# CAN Message exists without CHAT -> no convert it to object

# ID:   source:chat_id:message_id ????
#
# /!\ handle null chat and message id -> chat = uuid and message = timestamp ???


# ID = <ChatInstance UUID>/<timestamp>/<chat ID>/<message ID> => telegram without channels
# ID = <ChatInstance UUID>/<timestamp>/<chat ID>/<Channel ID>/<message ID>
# ID = <ChatInstance UUID>/<timestamp>/<chat ID>/<Thread ID>/<message ID>
# ID = <ChatInstance UUID>/<timestamp>/<chat ID>/<Channel ID>/<Thread ID>/<message ID>
class Message(AbstractObject):
    """
    AIL Message Object. (strings)
    """

    def __init__(self, id):  # TODO subtype or use source ????
        super(Message, self).__init__('message', id)  # message::< telegram/1692189934.380827/ChatID_MessageID >

    def exists(self):
        if self.subtype is None:
            return r_object.exists(f'meta:{self.type}:{self.id}')
        else:
            return r_object.exists(f'meta:{self.type}:{self.get_subtype(r_str=True)}:{self.id}')

    def get_source(self):
        """
        Returns source/feeder name
        """
        l_source = self.id.split('/')[:-2]
        return os.path.join(*l_source)

    def get_basename(self):
        return os.path.basename(self.id)

    def get_chat_instance(self):
        c_id = self.id.split('/')
        return c_id[0]

    def get_content(self, r_type='str'): # TODO ADD cache # TODO Compress content ???????
        """
        Returns content
        """
        global_id = self.get_global_id()
        content = r_cache.get(f'content:{global_id}')
        if not content:
            content = self._get_field('content')
            if content:
                r_cache.set(f'content:{global_id}', content)
                r_cache.expire(f'content:{global_id}', 300)
        if r_type == 'str':
            return content
        elif r_type == 'bytes':
            if content:
                return content.encode()

    def get_date(self):
        timestamp = self.get_timestamp()
        return datetime.utcfromtimestamp(float(timestamp)).strftime('%Y%m%d')

    def get_last_full_date(self):
        timestamp = datetime.utcfromtimestamp(float(self.get_timestamp()))
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')

    def get_timestamp(self):
        dirs = self.id.split('/')
        return dirs[1]

    def get_message_id(self):  # TODO optimize
        message_id = self.get_basename().rsplit('/', 1)[1]
        # if message_id.endswith('.gz'):
        #     message_id = message_id[:-3]
        return message_id

    def get_chat_id(self):  # TODO optimize -> use me to tag Chat
        c_id = self.id.split('/')
        return c_id[2]

    def get_chat(self):
        c_id = self.id.split('/')
        return f'chat:{c_id[0]}:{c_id[2]}'

    def get_subchannel(self):
        subchannel = self.get_correlation('chat-subchannel')
        if subchannel.get('chat-subchannel'):
            return f'chat-subchannel:{subchannel["chat-subchannel"].pop()}'

    def get_current_thread(self):
        subchannel = self.get_correlation('chat-thread')
        if subchannel.get('chat-thread'):
            return f'chat-thread:{subchannel["chat-thread"].pop()}'

    # children thread
    def get_thread(self):
        for child in self.get_childrens():
            obj_type, obj_subtype, obj_id = child.split(':', 2)
            if obj_type == 'chat-thread':
                nb_messages = r_object.zcard(f'messages:{obj_type}:{obj_subtype}:{obj_id}')
                return {'type': obj_type, 'subtype': obj_subtype, 'id': obj_id, 'nb': nb_messages}

    # TODO get Instance ID
    # TODO get channel ID
    # TODO get thread  ID

    def _get_image_ocr(self, obj_id):
        return bool(self.get_correlation('ocr').get('ocr'))

    def get_images(self):
        images = []
        for child in self.get_childrens():
            obj_type, _, obj_id = child.split(':', 2)
            if obj_type == 'image':
                images.append({'id': obj_id, 'ocr': self._get_image_ocr(obj_id)})
        return images

    def get_barcodes(self):
        barcodes = []
        for c in self.get_correlation('barcode').get('barcode', []):
            barcodes.append(c[1:])
        return barcodes

    def get_qrcodes(self):
        qrcodes = []
        for c in self.get_correlation('qrcode').get('qrcode', []):
            qrcodes.append(c[1:])
        return qrcodes

    def get_user_account(self, meta=False):
        user_account = self.get_correlation('user-account')
        if user_account.get('user-account'):
            user_account = f'user-account:{user_account["user-account"].pop()}'
            if meta:
                _, user_account_subtype, user_account_id = user_account.split(':', 2)
                user_account = UsersAccount.UserAccount(user_account_id, user_account_subtype).get_meta(options={'icon', 'username', 'username_meta'})
        return user_account

    def get_files_names(self):
        names = []
        filenames = self.get_correlation('file-name').get('file-name')
        if filenames:
            for name in filenames:
                names.append(name[1:])
        return names

    def get_nb_files(self):
        return self.get_nb_correlation('item')

    def get_files(self, file_names=None):
        if not file_names:
            file_names = self.get_files_names()
        files = {}
        nb_files = 0
        s_files = set()
        for file_name in file_names:
            for it in self.get_correlation_iter('file-name', '', file_name, 'item'):
                if file_name not in files:
                    files[file_name] = []
                files[file_name].append({'obj': it[1:], 'tags': self.get_obj_tags('item', '', it[1:])})
                s_files.add(it[1:])
                nb_files += 1
        if nb_files < self.get_nb_files():
            files['undefined'] = []
            for f in self.get_correlation('item').get('item'):
                if f[1:] not in s_files:
                    files['undefined'].append({'obj': f[1:], 'tags': self.get_obj_tags('item', '', f[1:])})
        return files

    def get_reactions(self):
        return r_object.hgetall(f'meta:reactions:{self.type}::{self.id}')

    # TODO sanitize reactions
    def add_reaction(self, reactions, nb_reaction):
        r_object.hset(f'meta:reactions:{self.type}::{self.id}', reactions, nb_reaction)

    # Interactions between users -> use replies
    # nb views
    # MENTIONS -> Messages + Chats
    #       # relationship -> mention       - Chat    -> Chat
    #                                       - Message -> Chat
    #                                       - Message -> Message ??? fetch mentioned messages
    # FORWARDS
    # TODO Create forward CHAT -> message
    #                       message (is forwarded) -> message (is forwarded from) ???
    #                       # TODO get source message timestamp
    #
    #       # is forwarded
    #       # forwarded from -> check if relationship
    #       # nb forwarded -> scard relationship
    #
    #       Messages -> CHATS -> NB forwarded
    #       CHAT -> NB forwarded by chats -> NB messages -> parse full set ????
    #
    #
    #
    #
    #
    #
    # show users chats
    # message media
    # flag is deleted -> event or missing from feeder pass ???

    def get_language(self):
        languages = self.get_languages()
        if languages:
            return languages.pop()
        else:
            return None

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True)}
    #     return payload

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('chats_explorer.objects_message', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/objects/message?id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf4ad', 'color': '#4dffff', 'radius': 5}

    def get_misp_object(self):  # TODO
        obj = MISPObject('instant-message', standalone=True)
        obj_date = self.get_date()
        if obj_date:
            obj.first_seen = obj_date
        else:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={obj_date}')

        # obj_attrs = [obj.add_attribute('first-seen', value=obj_date),
        #              obj.add_attribute('raw-data', value=self.id, data=self.get_raw_content()),
        #              obj.add_attribute('sensor', value=get_ail_uuid())]
        obj_attrs = []
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    # def get_url(self):
    #     return r_object.hget(f'meta:item::{self.id}', 'url')

    # options: set of optional meta fields
    def get_meta(self, options=None, timestamp=None, translation_target=''):
        """
        :type options: set
        :type timestamp: float
        """
        if options is None:
            options = set()
        meta = self.get_default_meta(tags=True)
        # original_id
        meta['_id'] = self.id.rsplit('/', 1)[-1]

        # timestamp
        if not timestamp:
            timestamp = self.get_timestamp()
        else:
            timestamp = float(timestamp)
        timestamp = datetime.utcfromtimestamp(float(timestamp))
        meta['date'] = timestamp.strftime('%Y-%m-%d')
        meta['hour'] = timestamp.strftime('%H:%M:%S')
        meta['full_date'] = timestamp.isoformat(' ')
        if 'last_full_date' in options:
            meta['last_full_date'] = meta['full_date']

        # meta['source'] = self.get_source()
        # optional meta fields
        if 'content' in options:
            meta['content'] = self.get_content()
        if 'parent' in options:
            meta['parent'] = self.get_parent()
            if meta['parent'] and 'parent_meta' in options:
                options.remove('parent')
                parent_type, _, parent_id = meta['parent'].split(':', 3)
                if parent_type == 'message':
                    message = Message(parent_id)
                    meta['reply_to'] = message.get_meta(options=options, translation_target=translation_target)
        if 'forwarded_from' in options:
            fwd_from = self.get_first_relationship('forwarded_from', 'chat')
            if fwd_from:
                meta['forwarded_from'] = fwd_from['id']
        if 'investigations' in options:
            meta['investigations'] = self.get_investigations()
        if 'link' in options:
            meta['link'] = self.get_link(flask_context=True)
        if 'icon' in options:
            meta['icon'] = self.get_svg_icon()
        if 'user-account' in options:
            meta['user-account'] = self.get_user_account(meta=True)
            if not meta['user-account']:
                meta['user-account'] = {'id': 'UNKNOWN'}
        if 'container' in options:
            meta['container'] = self.get_container()
        if 'chat' in options:
            meta['chat'] = self.get_chat_id()
        if 'thread' in options:
            thread = self.get_thread()
            if thread:
                meta['thread'] = thread
        if 'images' in options:
            meta['images'] = self.get_images()
        if 'barcodes' in options:
            meta['barcodes'] = self.get_barcodes()
        if 'qrcodes' in options:
            meta['qrcodes'] = self.get_qrcodes()
        if 'files-names' in options:
            meta['files-names'] = self.get_files_names()
        if 'files' in options:
            if meta.get('files-names'):
                meta['files'] = self.get_files(file_names=meta['files-names'])
        if 'reactions' in options:
            meta['reactions'] = self.get_reactions()
        if 'language' in options:
            meta['language'] = self.get_language()
        if 'translation' in options and translation_target:
            if meta.get('language'):
                source = meta['language']
            else:
                source = None
            meta['translation'] = self.translate(content=meta.get('content'), source=source, target=translation_target)
            if 'language' in options:
                meta['language'] = self.get_language()

        # meta['encoding'] = None
        return meta

    # def translate(self, content=None): # TODO translation plugin
    #     # TODO get text language
    #     if not content:
    #         content = self.get_content()
    #     translated = argostranslate.translate.translate(content, 'ru', 'en')
    #     # Save translation
    #     return translated

    ## Language ##

    def get_root_obj(self):
        return self.get_objs_container(root=True).pop()

    def get_container(self):
        thread = self.get_current_thread()
        if thread:
            return thread
        subchannel = self.get_subchannel()
        if subchannel:
            return subchannel
        return self.get_chat()

    def get_objs_container(self, root=False):
        objs_containers = set()
        # chat
        objs_containers.add(self.get_chat())
        if not root:
            subchannel = self.get_subchannel()
            if subchannel:
                objs_containers.add(subchannel)
            thread = self.get_current_thread()
            if thread:
                objs_containers.add(thread)
        return objs_containers

    #- Language -#

    def create(self, content, language=None, translation=None, tags=[]):
        self._set_field('content', content)
        if not language and content:
            language = self.detect_language()
        if translation and content:
            self.set_translation(language, translation)
        for tag in tags:
            self.add_tag(tag)

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        pass

def create_obj_id(chat_instance, chat_id, message_id, timestamp, channel_id=None, thread_id=None): # TODO CHECK COLLISIONS
    timestamp = int(timestamp)
    if channel_id and thread_id:
        return f'{chat_instance}/{timestamp}/{chat_id}/{thread_id}/{message_id}'
    elif channel_id:
        return f'{chat_instance}/{timestamp}/{channel_id}/{chat_id}/{message_id}'
    elif thread_id:
        return f'{chat_instance}/{timestamp}/{chat_id}/{thread_id}/{message_id}'
    else:
        return f'{chat_instance}/{timestamp}/{chat_id}/{message_id}'

    # thread id of message
    # thread id of chat
    # thread id of subchannel

# TODO Check if already exists
# def create(source, chat_id, message_id, timestamp, content, tags=[]):
def create(obj_id, content, translation=None, tags=[]):
    message = Message(obj_id)
    # if not message.exists():
    message.create(content, translation=translation, tags=tags)
    return message

# TODO Encode translation


#####################################

# class Messages:
#     def __init__(self):
#         super().__init__('message', Message)
#
#     def get_name(self):
#         return 'Messages'
#
#     def get_icon(self):
#         return {'fas': 'fas', 'icon': 'comment-dots'}
#
#     def get_link(self, flask_context=False):
#         # if flask_context:
#         #     url = url_for('chats_explorer.chats_explorer_protocols')
#         # else:
#         #     url = f'{baseurl}/chats/explorer/protocols'
#         return None
#
#     # def get_by_date(self, date):
#     #     pass
#
#     def get_nb_by_date(self, date):
#         nb = 0
#         for subtype in self.get_subtypes():
#             nb += self.get_nb_by_date_subtype(subtype, date)
#         return nb


if __name__ == '__main__':
    r = 'test'
    print(r)
