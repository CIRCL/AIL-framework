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

class Tags(AbstractModule):
    """
    Tags module for AIL framework
    """

    def __init__(self):
        super(Tags, self).__init__()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 10

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        item = self.obj
        tag = message

        # Create a new tag
        item.add_tag(tag)
        print(f'{item.get_id()}: Tagged {tag}')

        # Forward message to channel
        self.add_message_to_queue(message=tag, queue='Tag_feed')

        self.add_message_to_queue(queue='Sync')


if __name__ == '__main__':
    module = Tags()
    module.run()
