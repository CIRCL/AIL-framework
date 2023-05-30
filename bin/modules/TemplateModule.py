#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Template Module
======================

This module is a template for Template for new modules

"""

##################################
# Import External packages
##################################
import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
# from lib.objects.Items import Item

class Template(AbstractModule):
    """
    Template module for AIL framework
    """

    def __init__(self):
        super(Template, self).__init__()

        # Pending time between two computation (computeNone) in seconds, 10 by default
        # self.pending_seconds = 10

        # logs
        self.logger.info(f'Module {self.module_name} initialized')

    # def computeNone(self):
    #     """
    #     Do something when there is no message in the queue. Optional
    #     """
    #     self.logger.debug("No message in queue")

    def compute(self, message):
        """
        Compute a message in queue / process the message (item_id, ...)
        """
        self.logger.debug("Compute message in queue")
        # # if message is an item_id:
        # item = Item(message)
        # content = item.get_content()


if __name__ == '__main__':
    module = Template()
    module.run()
