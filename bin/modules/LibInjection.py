#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The LibInjection Module
================================

This module is consuming the Redis-list created by the Urls module.

It tries to identify SQL Injections with libinjection.

"""

import os
import sys
import pylibinjection

from datetime import datetime
from pyfaup.faup import Faup
from urllib.parse import unquote


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule

class LibInjection(AbstractModule):
    """docstring for LibInjection module."""

    def __init__(self):
        super(LibInjection, self).__init__()

        self.faup = Faup()

        self.logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        url = message

        self.faup.decode(url)
        url_parsed = self.faup.get()
        # # TODO: # FIXME: remove me
        try:
            resource_path = url_parsed['resource_path'].encode()
        except:
            resource_path = url_parsed['resource_path']

        # # TODO: # FIXME: remove me
        try:
            query_string = url_parsed['query_string'].encode()
        except:
            query_string = url_parsed['query_string']

        result_path = {'sqli': False}
        result_query = {'sqli': False}

        if resource_path is not None:
            result_path = pylibinjection.detect_sqli(resource_path)
            # print(f'path is sqli : {result_path}')

        if query_string is not None:
            result_query = pylibinjection.detect_sqli(query_string)
            # print(f'query is sqli : {result_query}')

        if result_path['sqli'] is True or result_query['sqli'] is True:

            self.logger.info(f'Detected SQL in URL;{self.obj.get_global_id()}')
            print(unquote(url))

            # Add tag
            tag = 'infoleak:automatic-detection="sql-injection"'
            self.add_message_to_queue(message=tag, queue='Tags')

            # statistics
            # # # TODO: # FIXME: remove me
            # try:
            #     tld = url_parsed['tld'].decode()
            # except:
            #     tld = url_parsed['tld']
            # if tld is not None:
            #     date = datetime.now().strftime("%Y%m")
            #     Statistics.add_module_tld_stats_by_date(self.module_name, date, tld, 1)


if __name__ == "__main__":
    module = LibInjection()
    module.run()
