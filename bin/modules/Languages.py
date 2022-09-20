#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Domains import Domain
from lib.objects.Items import Item
#from lib.ConfigLoader import ConfigLoader

class Languages(AbstractModule):
    """
    Languages module for AIL framework
    """

    def __init__(self):
        super(Languages, self).__init__()

        # Send module state to logs
        self.redis_logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        item = Item(message)
        if item.is_crawled():
            domain = Domain(item.get_domain())
            for lang in item.get_languages(min_probability=0.8):
                domain.add_language(lang.language)

if __name__ == '__main__':
    module = Languages()
    module.run()
