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

    def __init__(self):
        super(Tags, self).__init__()

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 10

        # Send module state to logs
        self.redis_logger.info(f"Module {self.module_name} initialized")


    def compute(self, message):
        self.redis_logger.debug(message)

        tag, item_id = message.split(';')
        Tag.add_tag("item", tag, item_id)

        self.process.populate_set_out(message, 'MISP_The_Hive_feeder')


if __name__ == '__main__':
    
    module = Tags()
    module.run()
