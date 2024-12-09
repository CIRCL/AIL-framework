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
import sys

from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib.objects.Items import Item

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

        config_loader = ConfigLoader()

        self.faup = Faup()

        # Protocol file path
        protocolsfile_path = os.path.join(os.environ['AIL_HOME'],
                                          config_loader.get_config_str("Directories", "protocolsfile"))
        # Get all uri from protocolsfile (Used for Curve)
        uri_scheme = ""
        with open(protocolsfile_path, 'r') as scheme_file:
            for scheme in scheme_file:
                uri_scheme += scheme[:-1]+"|"
        uri_scheme = uri_scheme[:-1]

        self.url_regex = "((?i:"+uri_scheme + \
            ")\://(?:[a-zA-Z0-9\.\-]+(?:\:[a-zA-Z0-9\.&%\$\-]+)*@)*(?:(?:25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(?:25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(?:25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(?:25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|(?:[a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(?:[a-zA-Z]{2,15}))(?:\:[0-9]+)*(?:/?(?:[a-zA-Z0-9\.\,\?'\\+&%\$#\=~_\-]+))*)"

        # Send module state to logs
        self.logger.info(f"Module {self.module_name} initialized")

    def compute(self, message):
        """
        Search for Web links from given message
        """
        score = message

        item = self.get_obj()
        item_content = item.get_content()

        # TODO Handle invalid URL
        l_urls = self.regex_findall(self.url_regex, item.get_id(), item_content)
        for url in l_urls:
            self.faup.decode(url)
            url_decoded = self.faup.get()
            # decode URL
            try:
                url = url_decoded['url'].decode()
            except AttributeError:
                url = url_decoded['url']

            print(url, self.obj.get_global_id())
            self.add_message_to_queue(message=str(url), queue='Url')
            self.logger.debug(f"url_parsed: {url}")

        if len(l_urls) > 0:
            to_print = f'Urls;{item.get_source()};{item.get_date()};{item.get_basename()};'
            print(to_print)


if __name__ == '__main__':
    module = Urls()
    module.run()
