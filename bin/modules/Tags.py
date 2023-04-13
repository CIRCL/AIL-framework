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
from lib.objects.Items import Item
from lib import Tag


class Tags(AbstractModule):
    """
    Tags module for AIL framework
    """

    def __init__(self):
        super(Tags, self).__init__()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 10

        # Send module state to logs
        self.redis_logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        #  Extract item ID and tag from message
        mess_split = message.split(';')
        if len(mess_split) == 2:
            tag = mess_split[0]
            item = Item(mess_split[1])

            # Create a new tag
            Tag.add_object_tag(tag, 'item', item.get_id())
            print(f'{item.get_id()}: Tagged {tag}')

            # Forward message to channel
            self.add_message_to_queue(message, 'Tag_feed')

            message = f'{item.get_type()};{item.get_subtype(r_str=True)};{item.get_id()}'
            self.add_message_to_queue(message, 'Sync')

        else:
            # Malformed message
            raise Exception(f'too many values to unpack (expected 2) given {len(mess_split)} with message {message}')


if __name__ == '__main__':
    module = Tags()
    module.run()
