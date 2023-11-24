#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Twitter Feeder Importer Module
================

Process Twitter JSON

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
from lib.objects.Items import Item

class TwitterFeeder(DefaultFeeder):

    def __init__(self, json_data):
        super().__init__(json_data)
        self.name = 'twitter'

    # define item id
    def get_item_id(self):
        # TODO twitter timestamp message date
        date = datetime.date.today().strftime("%Y/%m/%d")
        item_id = str(self.json_data['meta']['twitter:tweet_id'])
        item_id = os.path.join('twitter', date, item_id)
        self.item_id = f'{item_id}.gz'
        return self.item_id

    def process_meta(self):
        '''
        Process JSON meta field.
        '''
        # tweet_id = str(self.json_data['meta']['twitter:tweet_id'])
        # item_basic.add_map_obj_id_item_id(tweet_id, item_id, 'twitter_id') ############################################
        item = Item(self.item_id)
        date = item.get_date()
        user = str(self.json_data['meta']['twitter:id'])
        username = Username(user, 'twitter')
        username.add(date, item)
        return set()
