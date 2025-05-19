#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Indexer Module
============================

AIL Indexer

"""
##################################
# Import External packages
##################################
import os
import sys
import time


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import search_engine


class Indexer(AbstractModule):
    """
    Indexer module for AIL framework
    """

    def __init__(self):
        """
        Init Instance
        """
        super(Indexer, self).__init__()

        config_loader = ConfigLoader()

        self.is_enabled_meilisearch = search_engine.is_meilisearch_enabled()

    def compute(self, message):
        obj = self.get_obj()
        if self.is_enabled_meilisearch and obj:
            if self.obj.type == 'message':
                search_engine.index_message(obj)


if __name__ == '__main__':
    module = Indexer()
    module.run()
