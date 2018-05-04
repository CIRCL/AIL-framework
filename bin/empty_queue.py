#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Empty queue module
====================

This simple module can be used to clean all queues.

Requirements:
-------------


"""
import redis
import os
import time
from packages import Paste
from pubsublogger import publisher
from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = ['Global', 'Duplicates', 'Indexer', 'Attributes', 'Lines', 'DomClassifier', 'Tokenize', 'Curve', 'Categ', 'CreditCards', 'Mail', 'Onion', 'DumpValidOnion', 'Web',  'WebStats', 'Release', 'Credential', 'Cve', 'Phone', 'SourceCode', 'Keys']
    config_section = ['Curve']

    for queue in config_section:
        print('dropping: ' + queue)
        p = Process(queue)
        while True:
            message = p.get_from_set()
            if message is None:
                break
