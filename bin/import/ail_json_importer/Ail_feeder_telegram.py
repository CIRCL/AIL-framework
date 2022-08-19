#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The JSON Receiver Module
================

Recieve Json Items (example: Twitter feeder)

"""
import os
import sys
import datetime

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import item_basic
from lib.objects.Usernames import Username

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'import', 'ail_json_importer'))
from Default_json import Default_json

class Ail_feeder_telegram(Default_json):
    """Twitter Feeder functions"""

    def __init__(self, name, json_item):
        super().__init__(name, json_item)

    def get_feeder_name(self):
        return 'telegram'

    # define item id
    def get_item_id(self):
        # use twitter timestamp ?
        item_date = datetime.date.today().strftime("%Y/%m/%d")
        channel_id = str(self.json_item['meta']['channel_id'])
        message_id = str(self.json_item['meta']['message_id'])
        item_id = f'{channel_id}_{message_id}'
        return os.path.join('telegram', item_date, item_id) + '.gz'

    def process_json_meta(self, process, item_id):
        '''
        Process JSON meta filed.
        '''
        channel_id = str(self.json_item['meta']['channel_id'])
        message_id = str(self.json_item['meta']['message_id'])
        telegram_id = f'{channel_id}_{message_id}'
        item_basic.add_map_obj_id_item_id(telegram_id, item_id, 'telegram_id')
        #print(self.json_item['meta'])
        user = None
        if self.json_item['meta'].get('user'):
            user = str(self.json_item['meta']['user'])
        else:
            if self.json_item['meta'].get('channel'):
                user = str(self.json_item['meta']['channel']['username'])
        if user:
            item_date = item_basic.get_item_date(item_id)
            username = Username(user, 'telegram')
            username.add(date, item_id)
        return None
