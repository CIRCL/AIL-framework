#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The ZMQ_Sub_Indexer Module
============================

The ZMQ_Sub_Indexer modules is fetching the list of files to be processed
and index each file with a full-text indexer (Whoosh until now).

"""
import redis, zmq, ConfigParser, time
from packages import Paste as P
from packages import ZMQ_PubSub
from pubsublogger import publisher

from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import *
import os

configfile = './packages/config.cfg'

def main():
    """Main Function"""

    # CONFIG #
    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    # Redis
    r_serv1 = redis.StrictRedis(
        host = cfg.get("Redis_Queues", "host"),
        port = cfg.getint("Redis_Queues", "port"),
        db = cfg.getint("Redis_Queues", "db"))

    # Indexer configuration - index dir and schema setup
    indexpath = cfg.get("Indexer", "path")
    indexertype = cfg.get("Indexer", "type")
    if indexertype == "whoosh":
        schema = Schema(title=TEXT(stored=True), path=ID(stored=True,unique=True), content=TEXT)

        if not os.path.exists(indexpath):
            os.mkdir(indexpath)

        if not exists_in(indexpath):
            ix = create_in(indexpath, schema)
        else:
            ix = open_dir(indexpath)

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    #Subscriber
    channel = cfg.get("PubSub_Global", "channel")
    subscriber_name = "indexer"
    subscriber_config_section = "PubSub_Global"

    Sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, channel, subscriber_name)

    # FUNCTIONS #
    publisher.info("""ZMQ Indexer is Running""")

    while True:
	try:
            message = Sub.get_msg_from_queue(r_serv1)

            if message != None:
                PST = P.Paste(message.split(" ",-1)[-1])
            else:
                if r_serv1.sismember("SHUTDOWN_FLAGS", "Indexer"):
                    r_serv1.srem("SHUTDOWN_FLAGS", "Indexer")
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                publisher.debug("Script Indexer is idling 10s")
                time.sleep(1)
                continue
            docpath = message.split(" ",-1)[-1]
            paste = PST.get_p_content()
            print "Indexing :", docpath
            if indexertype == "whoosh":
                indexwriter = ix.writer()
                indexwriter.update_document(title=unicode(docpath, errors='ignore'),path=unicode(docpath, errors='ignore'),content=unicode(paste, errors='ignore'))
                indexwriter.commit()
        except IOError:
           print "CRC Checksum Failed on :", PST.p_path
           publisher.error('{0};{1};{2};{3};{4}'.format("Duplicate", PST.p_source, PST.p_date, PST.p_name, "CRC Checksum Failed" ))
           pass


if __name__ == "__main__":
    main()
