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
import os
import re
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects import Cves
from lib.objects.Items import Item


class CveModule(AbstractModule):
    """
    CveModule for AIL framework
    """

    def __init__(self):
        super(CveModule, self).__init__()

        # regex to find CVE
        self.reg_cve = re.compile(r'CVE-[1-2]\d{1,4}-\d{1,5}')

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        item = self.get_obj()
        item_id = item.get_id()

        cves = self.regex_findall(self.reg_cve, item_id, item.get_content())
        if cves:
            # print(cves)
            date = item.get_date()
            for cve_id in cves:
                cve = Cves.Cve(cve_id)
                cve.add(date, item)

            print(f'{self.obj.get_global_id()} contains CVEs {cves}')

            tag = 'infoleak:automatic-detection="cve"'
            # Send to Tags Queue
            self.add_message_to_queue(message=tag, queue='Tags')


if __name__ == '__main__':

    module = CveModule()
    module.run()
