#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Tags Module
================================

This module create tags on pastes.

"""
import redis

import time
import datetime

from pubsublogger import publisher
from Helper import Process
from packages import Paste

if __name__ == '__main__':

    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'Tags'

    # Setup the I/O queues
    p = Process(config_section)

    server = redis.StrictRedis(
                host=p.config.get("ARDB_Tags", "host"),
                port=p.config.get("ARDB_Tags", "port"),
                db=p.config.get("ARDB_Tags", "db"),
                decode_responses=True)

    server_metadata = redis.StrictRedis(
                host=p.config.get("ARDB_Metadata", "host"),
                port=p.config.get("ARDB_Metadata", "port"),
                db=p.config.get("ARDB_Metadata", "db"),
                decode_responses=True)

    serv_statistics = redis.StrictRedis(
        host=p.config.get('ARDB_Statistics', 'host'),
        port=p.config.get('ARDB_Statistics', 'port'),
        db=p.config.get('ARDB_Statistics', 'db'),
        decode_responses=True)

    # Sent to the logging a description of the module
    publisher.info("Tags module started")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()

        if message is None:
            publisher.debug("{} queue is empty, waiting 10s".format(config_section))
            time.sleep(10)
            continue

        else:
            tag, path = message.split(';')
            # add the tag to the tags word_list
            res = server.sadd('list_tags', tag)
            if res == 1:
                print("new tags added : {}".format(tag))
            # add the path to the tag set
            res = server.sadd(tag, path)
            if res == 1:
                print("new paste: {}".format(path))
                print("   tagged: {}".format(tag))
            server_metadata.sadd('tag:'+path, tag)

            curr_date = datetime.date.today()
            serv_statistics.hincrby(curr_date.strftime("%Y%m%d"),'paste_tagged:'+tag, 1)
            p.populate_set_out(message, 'MISP_The_Hive_feeder')
