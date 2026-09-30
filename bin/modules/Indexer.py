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
from lib.exceptions import MeilisearchError
from lib import search_engine
from lib.objects import ForumThreads


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
        if self.is_enabled_meilisearch:
            self.is_up = search_engine.Engine.is_up()
            search_engine.Engine.init()
            print('indexer ready')

    # check before poping message if meilisearch is up
    def can_process_next_message(self):
        if self.is_enabled_meilisearch:
            if not self.is_up:
                self.is_up = search_engine.Engine.is_up()
                return self.is_up
            else:
                return True
        else:
            return True

    # TODO send timestamp in queue ???? -> item
    # TODO UPDATE ONLY LAST SEEN ON UPDATE ->     # title  # filename
    def compute(self, message):  # crawled item - message - titles - file-name
        if self.is_enabled_meilisearch and self.obj:
            try:
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

                elif self.obj.type == 'post':
                    search_engine.index_forum_post(self.obj)
                    thread_id = self.obj.get_thread_sub_id()
                    # TODO CACHE
                    if thread_id:
                        subtype, thread_id = thread_id.split(':', 1)
                        search_engine.index_forum_thread(ForumThreads.ForumThread(thread_id, subtype))

            except MeilisearchError:
                self.is_up = False
                print('meilisearch down, sending message back to queue')
                self.send_back_message_to_queue(message)


if __name__ == '__main__':
    module = Indexer()
    module.run()
