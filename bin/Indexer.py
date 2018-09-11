#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The ZMQ_Sub_Indexer Module
============================

The ZMQ_Sub_Indexer modules is fetching the list of files to be processed
and index each file with a full-text indexer (Whoosh until now).

"""
import time
from packages import Paste
from pubsublogger import publisher

from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID
import shutil
import os
from os.path import join, getsize

from Helper import Process

# Config variable
TIME_WAIT = 60*15 #sec

# return in bytes
def check_index_size(baseindexpath, indexname):
    the_index_name = join(baseindexpath, indexname)
    cur_sum = 0
    for root, dirs, files in os.walk(the_index_name):
        cur_sum += sum(getsize(join(root, name)) for name in files)
    return cur_sum

def move_index_into_old_index_folder(baseindexpath):
    for cur_file in os.listdir(baseindexpath):
        if not cur_file == "old_index":
            shutil.move(join(baseindexpath, cur_file), join(join(baseindexpath, "old_index"), cur_file))


if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Indexer'

    p = Process(config_section)

    # Indexer configuration - index dir and schema setup
    baseindexpath = join(os.environ['AIL_HOME'],
                             p.config.get("Indexer", "path"))
    indexRegister_path = join(os.environ['AIL_HOME'],
                             p.config.get("Indexer", "register"))
    indexertype = p.config.get("Indexer", "type")
    INDEX_SIZE_THRESHOLD = int(p.config.get("Indexer", "index_max_size"))
    if indexertype == "whoosh":
        schema = Schema(title=TEXT(stored=True), path=ID(stored=True,
                                                         unique=True),
                        content=TEXT)
        if not os.path.exists(baseindexpath):
            os.mkdir(baseindexpath)

        # create the index register if not present
        time_now = int(time.time())
        if not os.path.isfile(indexRegister_path): #index are not organised
            print("Indexes are not organized")
            print("moving all files in folder 'old_index' ")
            #move all files to old_index folder
            move_index_into_old_index_folder(baseindexpath)
            print("Creating new index")
            #create all_index.txt
            with open(indexRegister_path, 'w') as f:
                f.write(str(time_now))
            #create dir
            os.mkdir(join(baseindexpath, str(time_now)))

        with open(indexRegister_path, "r") as f:
            allIndex = f.read()
            allIndex = allIndex.split() # format [time1\ntime2]
            allIndex.sort()

            try:
                indexname = allIndex[-1].strip('\n\r')
            except IndexError as e:
                indexname = time_now

            indexpath = join(baseindexpath, str(indexname))
            if not exists_in(indexpath):
                ix = create_in(indexpath, schema)
            else:
                ix = open_dir(indexpath)

        last_refresh = time_now

    # LOGGING #
    publisher.info("ZMQ Indexer is Running")

    while True:
        try:
            message = p.get_from_set()

            if message is not None:
                PST = Paste.Paste(message)
            else:
                publisher.debug("Script Indexer is idling 1s")
                time.sleep(1)
                continue
            docpath = message.split(" ", -1)[-1]
            paste = PST.get_p_content()
            print("Indexing - " + indexname + " :", docpath)


            #avoid calculating the index's size at each message
            if( time.time() - last_refresh > TIME_WAIT):
                last_refresh = time.time()
                if check_index_size(baseindexpath, indexname) >= INDEX_SIZE_THRESHOLD*(1000*1000):
                    timestamp = int(time.time())
                    print("Creating new index", timestamp)
                    indexpath = join(baseindexpath, str(timestamp))
                    indexname = str(timestamp)
                    #update all_index
                    with open(indexRegister_path, "a") as f:
                        f.write('\n'+str(timestamp))
                    #create new dir
                    os.mkdir(indexpath)
                    ix = create_in(indexpath, schema)


            if indexertype == "whoosh":
                indexwriter = ix.writer()
                indexwriter.update_document(
                    title=docpath,
                    path=docpath,
                    content=paste)
                indexwriter.commit()
        except IOError:
            print("CRC Checksum Failed on :", PST.p_path)
            publisher.error('Duplicate;{};{};{};CRC Checksum Failed'.format(
                PST.p_source, PST.p_date, PST.p_name))
