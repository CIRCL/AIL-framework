#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Default JSON Feeder Importer Module
================

Process Feeder Json (example: Twitter feeder)

"""
import os
import datetime
import sys
import uuid

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import ail_objects

class DefaultFeeder:
    """Default Feeder"""

    def __init__(self, json_data):
        self.json_data = json_data
        self.obj = None
        self.name = None

    def get_name(self):
        """
        Return feeder name. first part of the item_id and display in the UI
        """
        if not self.name:
            name = self.get_source()
        else:
            name = self.name
        if not name:
            name = 'default'
        return name

    def get_source(self):
        return self.json_data.get('source')

    def get_date(self):
        return datetime.date.today().strftime("%Y%m%d")

    def get_feeder_timestamp(self):
        timestamp = self.json_data.get('timestamp')
        if timestamp:
            return int(timestamp)

    def get_json_data(self):
        """
        Return the JSON data,
        """
        return self.json_data

    def get_json_meta(self):
        return self.json_data.get('meta')

    def get_uuid(self):
        return self.json_data.get('source_uuid')

    def get_default_encoding(self):
        return self.json_data.get('default_encoding')

    def get_gzip64_content(self):
        """
        Return the base64 encoded gzip content,
        """
        return self.json_data.get('data')

    def get_obj_type(self):
        meta = self.get_json_meta()
        return meta.get('type', 'item')

    ## OVERWRITE ME ##
    def get_obj(self):
        """
        Return obj global id. define obj global id
        Default == item object
        """
        date = datetime.date.today().strftime("%Y/%m/%d")
        obj_id = os.path.join(self.get_name(), date, str(uuid.uuid4()))
        obj_id = f'{obj_id}.gz'
        obj_id = f'item::{obj_id}'
        self.obj = ail_objects.get_obj_from_global_id(obj_id)
        return self.obj

    ## OVERWRITE ME ##
    def process_meta(self):
        """
        Process JSON meta filed.
        """
        # meta = self.get_json_meta()
        return set()
