#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Indexer Module
============================

each file with a full-text indexer (Whoosh until now).

"""
##################################
# Import External packages
##################################
import time
import shutil
import os
import sys
from os.path import join, getsize
from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib.objects.Items import Item


class Indexer(AbstractModule):
    """
    Indexer module for AIL framework
    """

    # Time to wait in seconds between two index's size variable compute
    TIME_WAIT = 60*15  # sec

    def __init__(self):
        """
        Init Instance
        """
        super(Indexer, self).__init__()

        config_loader = ConfigLoader()

        # Indexer configuration - index dir and schema setup
        self.baseindexpath = join(os.environ['AIL_HOME'], config_loader.get_config_str("Indexer", "path"))
        self.indexRegister_path = join(os.environ['AIL_HOME'], config_loader.get_config_str("Indexer", "register"))
        self.indexertype = config_loader.get_config_str("Indexer", "type")
        self.INDEX_SIZE_THRESHOLD = config_loader.get_config_int("Indexer", "index_max_size")

        self.indexname = None
        self.schema = None
        self.ix = None

        if self.indexertype == "whoosh":
            self.schema = Schema(title=TEXT(stored=True), path=ID(stored=True, unique=True), content=TEXT)
            if not os.path.exists(self.baseindexpath):
                os.mkdir(self.baseindexpath)

            # create the index register if not present
            time_now = int(time.time())
            if not os.path.isfile(self.indexRegister_path):  # index are not organised
                self.logger.debug("Indexes are not organized")
                self.logger.debug("moving all files in folder 'old_index' ")
                # move all files to old_index folder
                self.move_index_into_old_index_folder()
                self.logger.debug("Creating new index")
                # create all_index.txt
                with open(self.indexRegister_path, 'w') as f:
                    f.write(str(time_now))
                # create dir
                os.mkdir(join(self.baseindexpath, str(time_now)))

            with open(self.indexRegister_path, "r") as f:
                allIndex = f.read()
                allIndex = allIndex.split()  # format [time1\ntime2]
                allIndex.sort()

                try:
                    self.indexname = allIndex[-1].strip('\n\r')
                except IndexError as e:
                    self.indexname = time_now

                self.indexpath = join(self.baseindexpath, str(self.indexname))
                if not exists_in(self.indexpath):
                    self.ix = create_in(self.indexpath, self.schema)
                else:
                    self.ix = open_dir(self.indexpath)

            self.last_refresh = time_now

    def compute(self, message):
        item = self.get_obj()
        item_id = item.get_id()
        item_content = item.get_content()

        docpath = item_id

        self.logger.debug(f"Indexing - {self.indexname}: {docpath}")
        print(f"Indexing - {self.indexname}: {docpath}")

        try:
            # Avoid calculating the index's size at each message
            if time.time() - self.last_refresh > self.TIME_WAIT:
                self.last_refresh = time.time()
                if self.check_index_size() >= self.INDEX_SIZE_THRESHOLD*(1000*1000):
                    timestamp = int(time.time())
                    self.logger.debug(f"Creating new index {timestamp}")
                    print(f"Creating new index {timestamp}")
                    self.indexpath = join(self.baseindexpath, str(timestamp))
                    self.indexname = str(timestamp)
                    # update all_index
                    with open(self.indexRegister_path, "a") as f:
                        f.write('\n'+str(timestamp))
                    # create new dir
                    os.mkdir(self.indexpath)
                    self.ix = create_in(self.indexpath, self.schema)

            if self.indexertype == "whoosh":
                indexwriter = self.ix.writer()
                indexwriter.update_document(
                    title=docpath,
                    path=docpath,
                    content=item_content)
                indexwriter.commit()

        except IOError:
            self.logger.debug(f"CRC Checksum Failed on: {item_id}")
            print(f"CRC Checksum Failed on: {item_id}")
            self.logger.error(f'{item_id} CRC Checksum Failed')

    def check_index_size(self):
        """
        return in bytes
        """
        the_index_name = join(self.baseindexpath, self.indexname)
        cur_sum = 0
        for root, dirs, files in os.walk(the_index_name):
            cur_sum += sum(getsize(join(root, name)) for name in files)
        return cur_sum

    def move_index_into_old_index_folder(self):
        for cur_file in os.listdir(self.baseindexpath):
            if not cur_file == "old_index":
                shutil.move(join(self.baseindexpath, cur_file), join(
                    join(self.baseindexpath, "old_index"), cur_file))


if __name__ == '__main__':

    module = Indexer()
    module.run()
