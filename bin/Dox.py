#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Dox Module
======================

This module is consuming the Redis-list created by the Categ module.

"""


import pprint
import time
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher
import re
import sys

from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Dox'

    p = Process(config_section)

    # FUNCTIONS #
    publisher.info("Dox module")

    channel = 'dox_categ'

    regex = re.compile('name|age', re.IGNORECASE)

    while True:
        message = p.get_from_set()


        if message is not None:
            filepath, count = message.split(' ')
            filename, score = message.split()
            paste = Paste.Paste(filename)
            content = paste.get_p_content()

            count = 0

            tmp = paste._get_word('name')
            if (len(tmp) > 0):
                print(tmp)
                count += tmp[1]
            tmp = paste._get_word('Name')
            if (len(tmp) > 0):
                print(tmp)
                count += tmp[1]
            tmp = paste._get_word('NAME')
            if (len(tmp) > 0):
                print(tmp)
                count += tmp[1]
            tmp = paste._get_word('age')
            if (len(tmp) > 0):
                count += tmp[1]
            tmp = paste._get_word('Age')
            if (len(tmp) > 0):
                count += tmp[1]
            tmp = paste._get_word('AGE')
            if (len(tmp) > 0):
                count += tmp[1]
            tmp = paste._get_word('address')
            if (len(tmp) > 0):
                count += tmp[1]
            tmp = paste._get_word('Address')
            if (len(tmp) > 0):
                count += tmp[1]
            tmp = paste._get_word('ADDRESS')
            if (len(tmp) > 0):
                count += tmp[1]

            #dox_list = re.findall(regex, content)
            if(count > 0):

                #Send to duplicate
                p.populate_set_out(filepath, 'Duplicate')
                #Send to alertHandler
                msg = 'dox;{}'.format(filepath)
                p.populate_set_out(msg, 'alertHandler')

                print(filename)
                print(content)
                print('--------------------------------------------------------------------------------------')

        else:
            publisher.debug("Script creditcard is idling 1m")
            time.sleep(10)
