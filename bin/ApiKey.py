#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The ApiKey Module
======================

This module is consuming the Redis-list created by the Categ module.

It apply API_key regexes on paste content and warn if above a threshold.

"""

import redis
import pprint
import time
import re

from packages import Paste
from packages import lib_refine
from pubsublogger import publisher

from Helper import Process


def search_api_key(message):
    filename, score = message.split()
    paste = Paste.Paste(filename)
    content = paste.get_p_content()

    aws_access_key = regex_aws_access_key.findall(content)
    aws_secret_key = regex_aws_secret_key.findall(content)
    google_api_key = regex_google_api_key.findall(content)

    if(len(aws_access_key) > 0 or len(aws_secret_key) > 0 or len(google_api_key) > 0):

        to_print = 'ApiKey;{};{};{};'.format(
            paste.p_source, paste.p_date, paste.p_name)
        if(len(google_api_key) > 0):
            print('found google api key')
            print(to_print)
            publisher.warning('{}Checked {} found Google API Key;{}'.format(
                to_print, len(google_api_key), paste.p_rel_path))
            msg = 'infoleak:automatic-detection="google-api-key";{}'.format(filename)
            p.populate_set_out(msg, 'Tags')

        if(len(aws_access_key) > 0 or len(aws_secret_key) > 0):
            print('found AWS key')
            print(to_print)
            total = len(aws_access_key) + len(aws_secret_key)
            publisher.warning('{}Checked {} found AWS Key;{}'.format(
                to_print, total, paste.p_rel_path))
            msg = 'infoleak:automatic-detection="aws-key";{}'.format(filename)
            p.populate_set_out(msg, 'Tags')


        msg = 'infoleak:automatic-detection="api-key";{}'.format(filename)
        p.populate_set_out(msg, 'Tags')

        #Send to duplicate
        p.populate_set_out(filename, 'Duplicate')

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'ApiKey'

    p = Process(config_section)

    publisher.info("ApiKey started")

    message = p.get_from_set()

    # TODO improve REGEX
    regex_aws_access_key = re.compile(r'(?<![A-Z0-9])=[A-Z0-9]{20}(?![A-Z0-9])')
    regex_aws_secret_key = re.compile(r'(?<!=[A-Za-z0-9+])=[A-Za-z0-9+]{40}(?![A-Za-z0-9+])')

    regex_google_api_key = re.compile(r'=AIza[0-9a-zA-Z-_]{35}')

    while True:

        message = p.get_from_set()

        if message is not None:

            search_api_key(message)

        else:
            publisher.debug("Script ApiKey is Idling 10s")
            time.sleep(10)
