#!/usr/bin/env python
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
import os

from Helper import Process


if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Indexer'

    p = Process(config_section)

    # Indexer configuration - index dir and schema setup
    indexpath = os.path.join(os.environ['AIL_HOME'],
                             p.config.get("Indexer", "path"))
    indexertype = p.config.get("Indexer", "type")
    if indexertype == "whoosh":
        schema = Schema(title=TEXT(stored=True), path=ID(stored=True,
                                                         unique=True),
                        content=TEXT)
        if not os.path.exists(indexpath):
            os.mkdir(indexpath)
        if not exists_in(indexpath):
            ix = create_in(indexpath, schema)
        else:
            ix = open_dir(indexpath)

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
            print "Indexing :", docpath
            if indexertype == "whoosh":
                indexwriter = ix.writer()
                indexwriter.update_document(
                    title=unicode(docpath, errors='ignore'),
                    path=unicode(docpath, errors='ignore'),
                    content=unicode(paste, errors='ignore'))
                indexwriter.commit()
        except IOError:
            print "CRC Checksum Failed on :", PST.p_path
            publisher.error('Duplicate;{};{};{};CRC Checksum Failed'.format(
                PST.p_source, PST.p_date, PST.p_name))
