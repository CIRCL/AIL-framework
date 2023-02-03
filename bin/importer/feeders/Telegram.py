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
from lib.objects.Usernames import Username
from lib import item_basic

class TelegramFeeder(DefaultFeeder):

    def __init__(self, json_data):
        super().__init__(json_data)
        self.name = 'telegram'

    # define item id
    def get_item_id(self):
        # TODO use telegram message date
        date = datetime.date.today().strftime("%Y/%m/%d")
        channel_id = str(self.json_data['meta']['channel_id'])
        message_id = str(self.json_data['meta']['message_id'])
        item_id = f'{channel_id}_{message_id}'
        item_id = os.path.join('telegram', date, item_id)
        self.item_id = f'{item_id}.gz'
        return self.item_id

    def process_meta(self):
        """
        Process JSON meta field.
        """
        # channel_id = str(self.json_data['meta']['channel_id'])
        # message_id = str(self.json_data['meta']['message_id'])
        # telegram_id = f'{channel_id}_{message_id}'
        # item_basic.add_map_obj_id_item_id(telegram_id, item_id, 'telegram_id') #########################################
        user = None
        if self.json_data['meta'].get('user'):
            user = str(self.json_data['meta']['user'])
        elif self.json_data['meta'].get('channel'):
            user = str(self.json_data['meta']['channel'].get('username'))
        if user:
            date = item_basic.get_item_date(self.item_id)
            username = Username(user, 'telegram')
            username.add(date, self.item_id)
        return None
