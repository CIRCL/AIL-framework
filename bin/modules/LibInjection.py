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
from lib.ConfigLoader import ConfigLoader
from lib.objects.Items import Item
# from lib import Statistics

class LibInjection(AbstractModule):
    """docstring for LibInjection module."""

    def __init__(self):
        super(LibInjection, self).__init__()

        self.faup = Faup()

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        url, item_id = message.split()

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
            item = Item(item_id)
            item_id = item.get_id()
            print(f"Detected (libinjection) SQL in URL: {item_id}")
            print(unquote(url))

            to_print = f'LibInjection;{item.get_source()};{item.get_date()};{item.get_basename()};Detected SQL in URL;{item_id}'
            self.redis_logger.warning(to_print)

            # Add tag
            msg = f'infoleak:automatic-detection="sql-injection";{item_id}'
            self.add_message_to_queue(msg, 'Tags')

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
