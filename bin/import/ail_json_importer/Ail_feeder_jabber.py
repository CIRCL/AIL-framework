#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The JSON Receiver Module
================

Receiver Jabber Json Items

"""
import os
import json
import sys
import time
import datetime

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import item_basic
import Username

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'import', 'ail_json_importer'))
from Default_json import Default_json

class Ail_feeder_jabber(Default_json):
    """Jabber Feeder functions"""

    def __init__(self, name, json_item):
        super().__init__(name, json_item)

    def get_feeder_name(self):
        return 'jabber'

    # define item id
    def get_item_id(self):
        item_date = time.strptime(self.json_item['meta']['jabber:ts'], "%Y-%m-%dT%H:%M:%S.%f")
        item_date_str = time.strftime("%Y/%m/%d", item_date)
        item_id = str(self.json_item['meta']['jabber:id'])
        return os.path.join('jabber', item_date_str, item_id) + '.gz'

    def process_json_meta(self, process, item_id):
        '''
        Process JSON meta filed.
        '''
        jabber_id = str(self.json_item['meta']['jabber:id'])
        item_basic.add_map_obj_id_item_id(jabber_id, item_id, 'jabber_id')
        to = str(self.json_item['meta']['jabber:to'])
        fr = str(self.json_item['meta']['jabber:from'])
        item_date = item_basic.get_item_date(item_id)
        Username.save_item_correlation('jabber', to, item_id, item_date)
        Username.save_item_correlation('jabber', fr, item_id, item_date)
        return None