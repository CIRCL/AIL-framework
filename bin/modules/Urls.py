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

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import psl_faup

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
        urls = self.regex_findall(self.url_regex, item.get_id(), item_content)
        if urls:
            urls = set(urls)
            for url in urls:
                url = psl_faup.get_url(url)
                if url:
                    # decode URL
                    try:
                        url = url.decode()
                    except AttributeError:
                        pass

                    print(url, self.obj.get_global_id())
                    self.add_message_to_queue(message=str(url), queue='Url')
                    self.logger.debug(f"url_parsed: {url}")


if __name__ == '__main__':
    module = Urls()
    module.run()
