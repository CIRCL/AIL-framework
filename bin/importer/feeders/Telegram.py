#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Telegram Feeder Importer Module
================

Process Telegram JSON

"""
import os
import sys
import datetime

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.feeders.Default import DefaultFeeder
from lib.ConfigLoader import ConfigLoader
from lib.objects import ail_objects
from lib.objects.Chats import Chat
from lib.objects import Messages
from lib.objects import UsersAccount
from lib.objects.Usernames import Username

import base64
import io
import gzip

def gunzip_bytes_obj(bytes_obj):
    gunzipped_bytes_obj = None
    try:
        in_ = io.BytesIO()
        in_.write(bytes_obj)
        in_.seek(0)

        with gzip.GzipFile(fileobj=in_, mode='rb') as fo:
            gunzipped_bytes_obj = fo.read()
    except Exception as e:
        print(f'Global; Invalid Gzip file: {e}')

    return gunzipped_bytes_obj

class TelegramFeeder(DefaultFeeder):

    def __init__(self, json_data):
        super().__init__(json_data)
        self.name = 'telegram'

    def get_obj(self):  # TODO handle others objects -> images, pdf, ...
        # Get message date
        timestamp = self.json_data['meta']['date']['timestamp']  # TODO CREATE DEFAULT TIMESTAMP
        # if self.json_data['meta'].get('date'):
        #     date = datetime.datetime.fromtimestamp( self.json_data['meta']['date']['timestamp'])
        #     date = date.strftime('%Y/%m/%d')
        # else:
        #     date = datetime.date.today().strftime("%Y/%m/%d")
        chat_id = str(self.json_data['meta']['chat']['id'])
        message_id = str(self.json_data['meta']['id'])
        obj_id = Messages.create_obj_id('telegram', chat_id, message_id, timestamp)
        obj_id = f'message:telegram:{obj_id}'
        self.obj = ail_objects.get_obj_from_global_id(obj_id)
        return self.obj

    def process_meta(self):
        """
        Process JSON meta field.
        """
        # message chat
        meta = self.json_data['meta']
        mess_id = self.json_data['meta']['id']
        if meta.get('reply_to'):
            reply_to_id = int(meta['reply_to'])
        else:
            reply_to_id = None

        timestamp = meta['date']['timestamp']
        date = datetime.datetime.fromtimestamp(timestamp)
        date = date.strftime('%Y%m%d')

        if self.json_data.get('translation'):
            translation = self.json_data['translation']
        else:
            translation = None
        decoded = base64.standard_b64decode(self.json_data['data'])
        content = gunzip_bytes_obj(decoded)
        message = Messages.create(self.obj.id, content, translation=translation)

        if meta.get('chat'):
            chat = Chat(meta['chat']['id'], 'telegram')

            if meta['chat'].get('username'):
                chat_username = Username(meta['chat']['username'], 'telegram')
                chat.update_username_timeline(chat_username.get_global_id(), timestamp)

            # Chat---Message
            chat.add(date)
            chat.add_message(message.get_global_id(), timestamp, mess_id, reply_id=reply_to_id)
        else:
            chat = None

        # message sender
        if meta.get('sender'):  # TODO handle message channel forward - check if is user
            user_id = meta['sender']['id']
            user_account = UsersAccount.UserAccount(user_id, 'telegram')
            # UserAccount---Message
            user_account.add(date, obj=message)
            # UserAccount---Chat
            user_account.add_correlation(chat.type, chat.get_subtype(r_str=True), chat.id)

            if meta['sender'].get('firstname'):
                user_account.set_first_name(meta['sender']['firstname'])
            if meta['sender'].get('lastname'):
                user_account.set_last_name(meta['sender']['lastname'])
            if meta['sender'].get('phone'):
                user_account.set_phone(meta['sender']['phone'])

            if meta['sender'].get('username'):
                username = Username(meta['sender']['username'], 'telegram')
                # TODO timeline or/and correlation ????
                user_account.add_correlation(username.type, username.get_subtype(r_str=True), username.id)
                user_account.update_username_timeline(username.get_global_id(), timestamp)

                # Username---Message
                username.add(date)  # TODO # correlation message ???

                # if chat: # TODO Chat---Username correlation ???
                #     # Chat---Username
                #     chat.add_correlation(username.type, username.get_subtype(r_str=True), username.id)

        # if meta.get('fwd_from'):
            # if meta['fwd_from'].get('post_author') # user first name

        # TODO reply threads ????
        # message edit ????

        return None
