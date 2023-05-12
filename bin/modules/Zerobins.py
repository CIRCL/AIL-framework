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
import re
import sys

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
            r'^https:\/\/(zerobin||privatebin)\..*$',  # historical ones
            ]

        self.regex = re.compile('|'.join(binz))

        # Pending time between two computation (computeNone) in seconds
        self.pending_seconds = 10

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def computeNone(self):
        """
        Compute when no message in queue
        """
        self.logger.debug("No message in queue")

    def compute(self, message):
        """
        Compute a message in queue
        """
        url, item_id = message.split()

        # Extract zerobins addresses
        matching_binz = self.regex_findall(self.regex, item_id, url)

        if len(matching_binz) > 0:
            for bin_url in matching_binz:
                print(f'send {bin_url} to crawler')
                # TODO Change priority ???
                crawlers.create_task(bin_url, depth=0, har=False, screenshot=False, proxy='force_tor',
                                     parent='manual', priority=60)

        self.logger.debug("Compute message in queue")


if __name__ == '__main__':
    module = Zerobins()
    module.run()
