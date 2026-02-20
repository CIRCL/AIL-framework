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


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
# from lib.ConfigLoader import ConfigLoader
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
        # config_loader = ConfigLoader()
        self.is_enabled_meilisearch = search_engine.is_meilisearch_enabled()
        if self.is_enabled_meilisearch:
            search_engine.Engine.init()

    # TODO send timestamp in queue ???? -> item
    # TODO UPDATE ONLY LAST SEEN ON UPDATE ->     # title  # filename
    def compute(self, message):  # crawled item - message - titles - file-name
        if self.is_enabled_meilisearch and self.obj:
            if self.obj.type == 'message':
                # index Message + Chat + UserAccount
                search_engine.Engine.index_chat_message(self.obj)

            elif self.obj.type == 'item':
                if self.obj.is_crawled():
                    search_engine.index_crawled_item(self.obj)

            elif self.obj.type == 'file-name':
                search_engine.index_file_name(self.obj)

            elif self.obj.type == 'title':
                search_engine.index_title(self.obj)


if __name__ == '__main__':
    module = Indexer()
    module.run()
