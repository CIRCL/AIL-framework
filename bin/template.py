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
import time
from pubsublogger import publisher


##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from Helper import Process


class Template(AbstractModule):
    """
    Template module for AIL framework
    """

    def __init__(self):
        super(Template, self).__init__()

        # Send module state to logs
        self.redis_logger.info("Module %s initialized"%(self.module_name))

        # Pending time between two computation in seconds
        self.pending_seconds = 10


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
