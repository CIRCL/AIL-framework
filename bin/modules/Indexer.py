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
# from lib.ConfigLoader import ConfigLoader
from lib.exceptions import MeilisearchError
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
        self.is_up = False
        self.pending_seconds = 1
        self.retry_at = 0
        self.retry_batch = False
        self.batcher = search_engine.SearchBatcher(search_engine.Engine.update_batch, search_engine.get_pending_search_document) if self.is_enabled_meilisearch else None
        if self.is_enabled_meilisearch:
            self.is_up = search_engine.Engine.is_up()
            search_engine.Engine.init()
            print('indexer ready')

    # check before poping message if meilisearch is up
    def can_process_next_message(self):
        if self.is_enabled_meilisearch:
            if time.monotonic() < self.retry_at:
                return False
            if not self.is_up:
                self.is_up = search_engine.Engine.is_up()
                if not self.is_up:
                    self.retry_at = time.monotonic() + 10
                    return False
            try:
                self.batcher.flush_due(force=self.retry_batch)
                self.retry_batch = False
            except MeilisearchError as error:
                self.logger.warning(f'Meilisearch batch submission failed; retaining pending updates: {error}')
                self.is_up = False
                self.retry_batch = True
                self.retry_at = time.monotonic() + 10
                return False
        return True

    def compute(self, message):  # crawled item - message - titles - file-name
        if self.is_enabled_meilisearch and self.obj:
            search_engine.queue_indexer_object(self.batcher, self.obj, message)


if __name__ == '__main__':
    module = Indexer()
    module.run()
