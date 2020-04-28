#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The JSON Receiver Module
================

Recieve Json Items (example: Twitter feeder)

"""
import os
import json
import sys
import datetime

# sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
# import item_basic

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'import', 'ail_json_importer'))
from Default_json import Default_json

class Ail_feeder_twitter(Default_json):
    """Twitter Feeder functions"""

    def __init__(self, name, json_item):
        super().__init__(name, json_item)

    def get_feeder_name(self):
        return 'twitter'

    # define item id
    def get_item_id(self):
        # use twitter timestamp ?
        item_date = datetime.date.today().strftime("%Y/%m/%d")
        item_id = str(self.json_item['meta']['twitter:tweet_id'])
        return os.path.join('twitter', item_date, item_id) + '.gz'

    # # TODO: 
    def process_json_meta(self, process):
        '''
        Process JSON meta filed.
        '''
        return None
