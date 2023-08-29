#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Default JSON Feeder Importer Module
================

Process Feeder Json (example: Twitter feeder)

"""
import os
import datetime
import uuid

class DefaultFeeder:
    """Default Feeder"""

    def __init__(self, json_data):
        self.json_data = json_data
        self.item_id = None
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

    ## OVERWRITE ME ##
    def get_item_id(self):
        """
        Return item id. define item id
        """
        date = datetime.date.today().strftime("%Y/%m/%d")
        item_id = os.path.join(self.get_name(), date, str(uuid.uuid4()))
        self.item_id = f'{item_id}.gz'
        return self.item_id

    ## OVERWRITE ME ##
    def process_meta(self):
        """
        Process JSON meta filed.
        """
        # meta = self.get_json_meta()
        pass
