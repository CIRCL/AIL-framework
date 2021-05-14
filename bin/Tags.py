#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Tags Module
================================

This module create tags.

"""

##################################
# Import External packages
##################################
import time
from pubsublogger import publisher


##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from Helper import Process
from packages import Tag


class Tags(AbstractModule):
    """
    Tags module for AIL framework
    """

    # Channel name to forward message
    out_channel_name = 'MISP_The_Hive_feeder'

    # Split char in incomming message 
    msg_sep = ';'

    # Tag object type
    # TODO could be an enum in Tag class
    tag_type = 'item'


    def __init__(self):
        super(Tags, self).__init__()

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 10

        # Send module state to logs
        self.redis_logger.info(f'Module {self.module_name} initialized')


    def compute(self, message):
        self.redis_logger.debug(message)

        if len(message.split(Tags.msg_sep)) == 2:
            #  Extract item ID and tag from message
            tag, item_id = message.split(Tags.msg_sep)

            # Create a new tag
            Tag.add_tag(Tags.tag_type, tag, item_id)

            # Forward message to channel
            self.process.populate_set_out(message, Tags.out_channel_name)
        else:
            # Malformed message
            raise Exception(f'too many values to unpack (expected 2) given {len(message.split(Tags.msg_sep))} with message {message}')


if __name__ == '__main__':
    
    module = Tags()
    module.run()
