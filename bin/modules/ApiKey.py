#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The ApiKey Module
======================

This module is consuming the Redis-list created by the Categ module.

Search for API keys on an item content.

"""

import os
import re
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item

class ApiKey(AbstractModule):
    """ApiKey module for AIL framework"""

    def __init__(self):
        super(ApiKey, self).__init__()

        # # TODO: ENUM or dict

        # TODO improve REGEX
        # r'(?<![A-Z0-9])=[A-Z0-9]{20}(?![A-Z0-9])'
        # r'(?<!=[A-Za-z0-9+])=[A-Za-z0-9+]{40}(?![A-Za-z0-9+])'
        self.re_aws_access_key = r'AKIA[0-9A-Z]{16}'
        self.re_aws_secret_key = r'[0-9a-zA-Z/+]{40}'
        re.compile(self.re_aws_access_key)
        re.compile(self.re_aws_secret_key)

        # r'=AIza[0-9a-zA-Z-_]{35}' keep equal ????
        # AIza[0-9A-Za-z\\-_]{35}
        self.re_google_api_key = r'AIza[0-9a-zA-Z-_]{35}'
        re.compile(self.re_google_api_key)

        # Send module state to logs
        self.redis_logger.info(f"Module {self.module_name} initialized")

    def compute(self, message, r_result=False):
        item_id, score = message.split()
        item = Item(item_id)
        item_content = item.get_content()

        google_api_key = self.regex_findall(self.re_google_api_key, item.get_id(), item_content)
        aws_access_key = self.regex_findall(self.re_aws_access_key, item.get_id(), item_content)
        if aws_access_key:
            aws_secret_key = self.regex_findall(self.re_aws_secret_key, item.get_id(), item_content)

        if aws_access_key or google_api_key:
            to_print = f'ApiKey;{item.get_source()};{item.get_date()};{item.get_basename()};'

            if google_api_key:
                print(f'found google api key: {to_print}')
                self.redis_logger.warning(f'{to_print}Checked {len(google_api_key)} found Google API Key;{item.get_id()}')

                msg = f'infoleak:automatic-detection="google-api-key";{item.get_id()}'
                self.send_message_to_queue(msg, 'Tags')

            # # TODO: # FIXME: AWS regex/validate/sanitize KEY + SECRET KEY
            if aws_access_key:
                print(f'found AWS key: {to_print}')
                self.redis_logger.warning(f'{to_print}Checked {len(aws_access_key)} found AWS Key;{item.get_id()}')
                if aws_secret_key:
                    print(f'found AWS secret key')
                    self.redis_logger.warning(f'{to_print}Checked {len(aws_secret_key)} found AWS secret Key;{item.get_id()}')

                msg = 'infoleak:automatic-detection="aws-key";{}'.format(item.get_id())
                self.send_message_to_queue(msg, 'Tags')

            # Tags
            msg = f'infoleak:automatic-detection="api-key";{item.get_id()}'
            self.send_message_to_queue(msg, 'Tags')

            if r_result:
                return google_api_key, aws_access_key, aws_secret_key


if __name__ == "__main__":
    module = ApiKey()
    module.run()
