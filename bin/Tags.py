#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Tags Module
================================

This module create tags.

"""
import time

from pubsublogger import publisher
from Helper import Process
from packages import Tag

if __name__ == '__main__':

    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'Tags'

    # Setup the I/O queues
    p = Process(config_section)

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
            print(message)
            tag, item_id = message.split(';')

            Tag.add_tag("item", tag, item_id)

            p.populate_set_out(message, 'MISP_The_Hive_feeder')
