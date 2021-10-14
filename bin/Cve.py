#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The CVE Module
======================

This module is consuming the Redis-list created by the Categ module.

It apply CVE regexes on paste content and warn if a reference to a CVE is spotted.

"""

##################################
# Import External packages
##################################
import time
import re

##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from packages import Paste


class Cve(AbstractModule):
    """
    Cve module for AIL framework
    """

    def __init__(self):
        super(Cve, self).__init__()

        # regex to find CVE
        self.reg_cve = re.compile(r'(CVE-)[1-2]\d{1,4}-\d{1,5}')

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 1

        # Send module state to logs
        self.redis_logger.info(f'Module {self.module_name} initialized')


    def compute(self, message):

        filepath, count = message.split()
        paste = Paste.Paste(filepath)
        content = paste.get_p_content()
        
        # list of the regex results in the Paste, may be null
        results = set(self.reg_cve.findall(content))

        # if the list is positive, we consider the Paste may contain a list of cve
        if len(results) > 0:
            warning = f'{paste.p_name} contains CVEs'
            print(warning)
            self.redis_logger.warning(warning)

            msg = f'infoleak:automatic-detection="cve";{filepath}'
            # Send to Tags Queue
            self.send_message_to_queue(msg, 'Tags')
            # Send to Duplicate Queue
            self.send_message_to_queue(filepath, 'Duplicate')


if __name__ == '__main__':

    module = Cve()
    module.run()

