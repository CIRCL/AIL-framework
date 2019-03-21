#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Phone Module
================

This module is consuming the Redis-list created by the Categ module.

It apply phone number regexes on paste content and warn if above a threshold.

"""

import time
import re
import phonenumbers
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
        print(results)
        publisher.warning('{} contains PID (phone numbers)'.format(paste.p_name))

        msg = 'infoleak:automatic-detection="phone-number";{}'.format(message)
        p.populate_set_out(msg, 'Tags')

        #Send to duplicate
        p.populate_set_out(message, 'Duplicate')
        stats = {}
        for phone_number in results:
            try:
                x = phonenumbers.parse(phone_number, None)
                country_code = x.country_code
                if stats.get(country_code) is None:
                    stats[country_code] = 1
                else:
                    stats[country_code] = stats[country_code] + 1
            except:
                pass
        for country_code in stats:
            if stats[country_code] > 4:
                publisher.warning('{} contains Phone numbers with country code {}'.format(paste.p_name, country_code))

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
