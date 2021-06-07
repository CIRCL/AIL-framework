#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Urls Module
============================

This module extract URLs from an item and send them to others modules.

"""

##################################
# Import External packages
##################################
import os
import re
import sys

from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from packages.Item import Item
from lib import regex_helper

# # TODO: Faup packages: Add new binding: Check TLD

class Urls(AbstractModule):
    """
    Urls module for AIL framework
    """

    def __init__(self):
        """
        Init Urls
        """
        super(Urls, self).__init__()

        self.faup = Faup()
        self.redis_cache_key = regex_helper.generate_redis_cache_key(self.module_name)

        # Protocol file path
        protocolsfile_path = os.path.join(os.environ['AIL_HOME'],
                                          self.process.config.get("Directories", "protocolsfile"))
        # Get all uri from protocolsfile (Used for Curve)
        uri_scheme = ""
        with open(protocolsfile_path, 'r') as scheme_file:
            for scheme in scheme_file:
                uri_scheme += scheme[:-1]+"|"
        uri_scheme = uri_scheme[:-1]

        self.url_regex = "((?i:"+uri_scheme + \
            ")\://(?:[a-zA-Z0-9\.\-]+(?:\:[a-zA-Z0-9\.&%\$\-]+)*@)*(?:(?:25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(?:25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(?:25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(?:25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|(?:[a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(?:[a-zA-Z]{2,15}))(?:\:[0-9]+)*(?:/?(?:[a-zA-Z0-9\.\,\?'\\+&%\$#\=~_\-]+))*)"

        # Send module state to logs
        self.redis_logger.info(f"Module {self.module_name} initialized")


    def compute(self, message):
        """
        Search for Web links from given message
        """
        # Extract item
        id, score = message.split()

        item = Item(id)
        item_content = item.get_content()

        l_urls = regex_helper.regex_findall(self.module_name, self.redis_cache_key, self.url_regex, item.get_id(), item_content)
        for url in l_urls:
            self.faup.decode(url)
            unpack_url = self.faup.get()

            to_send = f"{url} {item.get_id()}"
            print(to_send)
            self.send_message_to_queue(to_send, 'Url')
            self.redis_logger.debug(f"url_parsed: {to_send}")

        if len(l_urls) > 0:
            to_print = f'Urls;{item.get_source()};{item.get_date()};{item.get_basename()};'
            self.redis_logger.info(f'{to_print}Detected {len(l_urls)} URL;{item.get_id()}')

if __name__ == '__main__':

    module = Urls()
    module.run()
