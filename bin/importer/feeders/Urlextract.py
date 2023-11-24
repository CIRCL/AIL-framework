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
import uuid

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.feeders.Default import DefaultFeeder
from lib.objects.Items import Item


class UrlextractFeeder(DefaultFeeder):

    def __init__(self, json_data):
        super().__init__(json_data)
        self.name = 'urlextract'

    # define item id
    def get_item_id(self):
        date = datetime.date.today().strftime("%Y/%m/%d")
        item_id = str(self.json_data['meta']['twitter:url-extracted'])
        item_id = item_id.split('//')
        if len(item_id) > 1:
            item_id = ''.join(item_id[1:])
        else:
            item_id = item_id[0]
        item_id = item_id.replace('/', '_')
        # limit ID length
        if len(item_id) > 215:
            item_id = item_id[:215]
        item_id = f'{item_id}{str(uuid.uuid4())}.gz'
        self.item_id = os.path.join('urlextract', date, item_id)
        return self.item_id

    def process_meta(self):
        """
        Process JSON meta field.
        """
        # ADD Other parents here
        parent_id = None
        if self.json_data['meta'].get('parent:twitter:tweet_id'):
            parent_id = str(self.json_data['meta']['parent:twitter:tweet_id'])

        if parent_id:
            item = Item(self.item_id)
            item.set_parent(parent_id)

        return set()

