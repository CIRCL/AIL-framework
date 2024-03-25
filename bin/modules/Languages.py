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
# from lib.ConfigLoader import ConfigLoader

class Languages(AbstractModule):
    """
    Languages module for AIL framework
    """

    def __init__(self):
        super(Languages, self).__init__()

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        obj = self.get_obj()
        
        if obj.type == 'item':
            if obj.is_crawled():
                domain = Domain(obj.get_domain())
                for lang in obj.get_languages(min_probability=0.8, force_gcld3=True):
                    print(lang)
                    domain.add_language(lang)
        # Detect Chat Message Language
        # elif obj.type == 'message':
        #     lang = obj.detect_language()
        #     print(self.obj.id, lang)


if __name__ == '__main__':
    module = Languages()
    module.run()
