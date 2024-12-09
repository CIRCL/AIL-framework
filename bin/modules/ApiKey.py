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
        self.logger.info(f"Module {self.module_name} initialized")

    def compute(self, message, r_result=False):
        score = message
        obj = self.get_obj()
        content = obj.get_content()

        google_api_key = self.regex_findall(self.re_google_api_key, obj.get_id(), content, r_set=True)
        aws_access_key = self.regex_findall(self.re_aws_access_key, obj.get_id(), content, r_set=True)
        if aws_access_key:
            aws_secret_key = self.regex_findall(self.re_aws_secret_key, obj.get_id(), content, r_set=True)

        if aws_access_key or google_api_key:
            to_print = obj.get_global_id()

            if google_api_key:
                print(f'found google api key: {to_print}')

                tag = 'infoleak:automatic-detection="google-api-key"'
                self.add_message_to_queue(message=tag, queue='Tags')

            # # TODO: # FIXME: AWS regex/validate/sanitize KEY + SECRET KEY
            if aws_access_key:
                print(f'found AWS key: {to_print}')
                if aws_secret_key:
                    print(f'found AWS secret key')

                tag = 'infoleak:automatic-detection="aws-key"'
                self.add_message_to_queue(message=tag, queue='Tags')

            # Tags
            tag = 'infoleak:automatic-detection="api-key"'
            self.add_message_to_queue(message=tag, queue='Tags')

            if r_result:
                return google_api_key, aws_access_key, aws_secret_key


if __name__ == "__main__":
    module = ApiKey()
    module.run()
