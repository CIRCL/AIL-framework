#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The Phone Module
================

This module is consuming the Redis-list created by the Categ module.

It apply phone number regexes on paste content and warn if above a threshold.

"""

import time
import re
from packages import Paste
from pubsublogger import publisher
from Helper import Process


def search_phone(message):
    paste = Paste.Paste(message)
    content = paste.get_p_content()
    # regex to find phone numbers, may raise many false positives (shalt thou seek optimization, upgrading is required)
    reg_phone = re.compile(r'(\+\d{1,4}(\(\d\))?\d?|0\d?)(\d{6,8}|([-/\. ]{1}\d{2,3}){3,4})')
    reg_phone = re.compile(r'(\+\d{1,4}(\(\d\))?\d?|0\d?)(\d{6,8}|([-/\. ]{1}\(?\d{2,4}\)?){3,4})')
    # list of the regex results in the Paste, may be null
    results = reg_phone.findall(content)

    # if the list is greater than 4, we consider the Paste may contain a list of phone numbers
    if len(results) > 4:
        print results
        publisher.warning('{} contains PID (phone numbers)'.format(paste.p_name))
        #send to Browse_warning_paste
        p.populate_set_out('phone;{}'.format(message), 'BrowseWarningPaste')
        #Send to duplicate
        p.populate_set_out(message, 'Duplicate')

if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'Phone'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Run Phone module")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        search_phone(message)
