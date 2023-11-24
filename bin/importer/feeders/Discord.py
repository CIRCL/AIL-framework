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
from importer.feeders.abstract_chats_feeder import AbstractChatFeeder
from lib.ConfigLoader import ConfigLoader
from lib.objects import ail_objects
from lib.objects.Chats import Chat
from lib.objects import Messages
from lib.objects import UsersAccount
from lib.objects.Usernames import Username

import base64

class DiscordFeeder(AbstractChatFeeder):

    def __init__(self, json_data):
        super().__init__('discord', json_data)

    # def get_obj(self):.
    #     obj_id = Messages.create_obj_id('telegram', chat_id, message_id, timestamp)
    #     obj_id = f'message:telegram:{obj_id}'
    #     self.obj = ail_objects.get_obj_from_global_id(obj_id)
    #     return self.obj

