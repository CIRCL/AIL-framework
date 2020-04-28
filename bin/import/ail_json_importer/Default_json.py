#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The JSON Receiver Module
================

Recieve Json Items (example: Twitter feeder)

"""
import os
import datetime
import json
import redis
import time
import sys
import uuid

#sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
#import ConfigLoader
#import item_basic

class Default_json(object):
    """Default Feeder functions"""

    def __init__(self, feeder_name, json_item):
        self.name = feeder_name
        self.json_item = json_item

    def get_feeder_source(self):
        '''
        Return the original feeder name (json source field).
        '''
        return self.name

    def get_feeder_name(self):
        '''
        Return feeder name. first part of the item_id and display in the UI
        '''
        return self.name

    def get_json_file(self):
        '''
        Return the JSON dict,
        '''
        return self.json_item

    def get_feeder_uuid(self):
        pass

    def get_item_gzip64encoded_content(self):
        '''
        Return item base64 encoded gzip content,
        '''
        return self.json_item['data']

    ## OVERWRITE ME ##
    def get_item_id(self):
        '''
        Return item id. define item id
        '''
        item_date = datetime.date.today().strftime("%Y/%m/%d")
        return os.path.join(self.get_feeder_name(), item_date, str(uuid.uuid4())) + '.gz'

    ## OVERWRITE ME ##
    def process_json_meta(self, process):
        '''
        Process JSON meta filed.
        '''
        return None
