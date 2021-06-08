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


class Template(AbstractModule):
    """
    Template module for AIL framework
    """

    def __init__(self):
        super(Template, self).__init__()

        # Pending time between two computation (computeNone) in seconds
        self.pending_seconds = 10

        # Send module state to logs
        self.redis_logger.info(f'Module {self.module_name} initialized')


    def computeNone(self):
        """
        Compute when no message in queue
        """
        self.redis_logger.debug("No message in queue")


    def compute(self, message):
        """
        Compute a message in queue
        """
        self.redis_logger.debug("Compute message in queue")


if __name__ == '__main__':

    module = Template()
    module.run()
