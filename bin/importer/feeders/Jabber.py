#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Jabber Feeder Importer Module
================

Process Jabber JSON

"""
import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.feeders.Default import DefaultFeeder
from lib.objects.Usernames import Username
from lib.objects.Items import Item


class JabberFeeder(DefaultFeeder):
    """Jabber Feeder functions"""

    def __init__(self, json_data):
        super().__init__(json_data)
        self.name = 'jabber'

    # define item id
    def get_item_id(self):
        date = time.strptime(self.json_data['meta']['jabber:ts'], "%Y-%m-%dT%H:%M:%S.%f")
        date_str = time.strftime("%Y/%m/%d", date)
        item_id = str(self.json_data['meta']['jabber:id'])
        item_id = os.path.join('jabber', date_str, item_id)
        self.item_id = f'{item_id}.gz'
        return self.item_id

    def process_meta(self): # TODO replace me by message
        """
        Process JSON meta field.
        """
        # jabber_id = str(self.json_data['meta']['jabber:id'])
        # item_basic.add_map_obj_id_item_id(jabber_id, item_id, 'jabber_id') ##############################################
        to = str(self.json_data['meta']['jabber:to'])
        fr = str(self.json_data['meta']['jabber:from'])

        item = Item(self.item_id)
        date = item.get_date()

        user_to = Username(to, 'jabber')
        user_fr = Username(fr, 'jabber')
        user_to.add(date, item)
        user_fr.add(date, item)
        return set()
