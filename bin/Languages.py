#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import cld3
import time

from packages import Item
from lib import Domain

from pubsublogger import publisher
from Helper import Process

if __name__ == '__main__':
    publisher.port = 6380
    publisher.channel = 'Script'
    # Section name in bin/packages/modules.cfg
    config_section = 'Languages'
    # Setup the I/O queues
    p = Process(config_section)

    while True:
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        item_id = Item.get_item_id(message)
        if Item.is_crawled(item_id):
            domain = Item.get_item_domain(item_id)
            Domain.add_domain_languages_by_item_id(domain, item_id)
