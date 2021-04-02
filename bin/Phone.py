#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Phone Module
================

This module is consuming the Redis-list created by the Categ module.

It apply phone number regexes on paste content and warn if above a threshold.

"""

##################################
# Import External packages
##################################
import time
import re
import phonenumbers


##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from packages import Paste
from pubsublogger import publisher
from Helper import Process


class Phone(AbstractModule):
    """
    Phone module for AIL framework
    """

    # regex to find phone numbers, may raise many false positives (shalt thou seek optimization, upgrading is required)
    # reg_phone = re.compile(r'(\+\d{1,4}(\(\d\))?\d?|0\d?)(\d{6,8}|([-/\. ]{1}\d{2,3}){3,4})')
    REG_PHONE = re.compile(r'(\+\d{1,4}(\(\d\))?\d?|0\d?)(\d{6,8}|([-/\. ]{1}\(?\d{2,4}\)?){3,4})')


    def __init__(self):
        super(Phone, self).__init__()

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 1


    def compute(self, message):
        paste = Paste.Paste(message)
        content = paste.get_p_content()
        # List of the regex results in the Paste, may be null
        results = self.REG_PHONE.findall(content)

        # If the list is greater than 4, we consider the Paste may contain a list of phone numbers
        if len(results) > 4:
            self.redis_logger.debug(results)
            self.redis_logger.warning('{} contains PID (phone numbers)'.format(paste.p_name))

            msg = 'infoleak:automatic-detection="phone-number";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')

            # Send to duplicate
            self.process.populate_set_out(message, 'Duplicate')

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
                    self.redis_logger.warning('{} contains Phone numbers with country code {}'.format(paste.p_name, country_code))


if __name__ == '__main__':
    
    module = Phone()
    module.run()
