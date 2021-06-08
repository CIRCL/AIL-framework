#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Tags Module
================================

This module add tags to an item.

"""

##################################
# Import External packages
##################################
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from packages.Item import Item
from packages import Tag


class Tags(AbstractModule):
    """
    Tags module for AIL framework
    """

    def __init__(self):
        super(Tags, self).__init__()

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 10

        # Send module state to logs
        self.redis_logger.info(f'Module {self.module_name} initialized')


    def compute(self, message):
        #  Extract item ID and tag from message
        mess_split = message.split(';')
        if len(mess_split) == 2:
            tag = mess_split[0]
            item = Item(mess_split[1])
            item_id = item.get_id()

            # Create a new tag
            Tag.add_tag('item', tag, item.get_id())
            print(f'{item_id}: Tagged {tag}')

            # Forward message to channel
            self.send_message_to_queue(message, 'MISP_The_Hive_feeder')
        else:
            # Malformed message
            raise Exception(f'too many values to unpack (expected 2) given {len(mess_split)} with message {message}')


if __name__ == '__main__':

    module = Tags()
    module.run()
