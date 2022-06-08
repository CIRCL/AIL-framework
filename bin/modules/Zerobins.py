#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Zerobins Module
======================
This module spots zerobins-like services for further processing
"""

##################################
# Import External packages
##################################
import os
import sys
import time
import pdb
import re
sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib import crawlers


class Zerobins(AbstractModule):
    """
    Zerobins module for AIL framework
    """

    def __init__(self):
        super(Zerobins, self).__init__()

        binz = [
            r'^https:\/\/(zerobin||privatebin)\..*$', # historical ones
            ]

        self.regex = re.compile('|'.join(binz))

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
        """regex_helper.regex_findall(self.module_name, self.redis_cache_key
        Compute a message in queue
        """
        print(message)
        url, id = message.split()

        # Extract zerobins addresses
        matching_binz = self.regex_findall(self.regex, id, url)

        if len(matching_binz) > 0:
            for bin in matching_binz:
                print("send {} to crawler".format(bin))
                crawlers.create_crawler_task(bin, screenshot=False, har=False, depth_limit=1, max_pages=1, auto_crawler=False, crawler_delta=3600, crawler_type=None, cookiejar_uuid=None, user_agent=None)

        self.redis_logger.debug("Compute message in queue")


if __name__ == '__main__':

    module = Zerobins()
    module.run()