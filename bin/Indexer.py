#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The ZMQ_Sub_Indexer Module
============================

The ZMQ_Sub_Indexer modules is fetching the list of files to be processed
and index each file with a full-text indexer (Whoosh until now).

"""
##################################
# Import External packages
##################################
import time
import shutil
import os
from os.path import join, getsize
from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID


##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from packages import Paste
from Helper import Process


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

        # Indexer configuration - index dir and schema setup
        self.baseindexpath = join(os.environ['AIL_HOME'],
                                  self.process.config.get("Indexer", "path"))
        self.indexRegister_path = join(os.environ['AIL_HOME'],
                                       self.process.config.get("Indexer", "register"))
        self.indexertype = self.process.config.get("Indexer", "type")
        self.INDEX_SIZE_THRESHOLD = self.process.config.getint(
            "Indexer", "index_max_size")

        self.indexname = None
        self.schema = None
        self.ix = None

        if self.indexertype == "whoosh":
            self.schema = Schema(title=TEXT(stored=True), path=ID(stored=True,
                                                             unique=True),
                            content=TEXT)
            if not os.path.exists(self.baseindexpath):
                os.mkdir(self.baseindexpath)

            # create the index register if not present
            time_now = int(time.time())
            if not os.path.isfile(self.indexRegister_path):  # index are not organised
                self.redis_logger.debug("Indexes are not organized")
                self.redis_logger.debug(
                    "moving all files in folder 'old_index' ")
                # move all files to old_index folder
                self.move_index_into_old_index_folder()
                self.redis_logger.debug("Creating new index")
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
        try:
            PST = Paste.Paste(message)
            docpath = message.split(" ", -1)[-1]
            paste = PST.get_p_content()
            self.redis_logger.debug(f"Indexing - {self.indexname}: {docpath}")

            # Avoid calculating the index's size at each message
            if(time.time() - self.last_refresh > self.TIME_WAIT):
                self.last_refresh = time.time()
                if self.check_index_size() >= self.INDEX_SIZE_THRESHOLD*(1000*1000):
                    timestamp = int(time.time())
                    self.redis_logger.debug(f"Creating new index {timestamp}")
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
                    content=paste)
                indexwriter.commit()

        except IOError:
            self.redis_logger.debug(f"CRC Checksum Failed on: {PST.p_path}")
            self.redis_logger.error('Duplicate;{};{};{};CRC Checksum Failed'.format(
                PST.p_source, PST.p_date, PST.p_name))

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
