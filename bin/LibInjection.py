#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The LibInjection Module
================================

This module is consuming the Redis-list created by the Web module.

It tries to identify SQL Injections with libinjection.

"""

import time
import datetime
import redis
import string
import urllib.request
import re
import pylibinjection
import pprint

from pubsublogger import publisher
from Helper import Process
from packages import Paste
from pyfaup.faup import Faup

def analyse(url, path):
    faup.decode(url)
    url_parsed = faup.get()
    pprint.pprint(url_parsed)
    ## TODO: # FIXME: remove me
    try:
        resource_path = url_parsed['resource_path'].encode()
    except:
        resource_path = url_parsed['resource_path']

    ## TODO: # FIXME: remove me
    try:
        query_string = url_parsed['query_string'].encode()
    except:
        query_string = url_parsed['query_string']

    result_path = {'sqli' : False}
    result_query = {'sqli' : False}

    if resource_path is not None:
        result_path = pylibinjection.detect_sqli(resource_path)
        print("path is sqli : {0}".format(result_path))

    if query_string is not None:
        result_query = pylibinjection.detect_sqli(query_string)
        print("query is sqli : {0}".format(result_query))

    if result_path['sqli'] is True or result_query['sqli'] is True:
        paste = Paste.Paste(path)
        print("Detected (libinjection) SQL in URL: ")
        print(urllib.request.unquote(url))
        to_print = 'LibInjection;{};{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, "Detected SQL in URL", paste.p_rel_path)
        publisher.warning(to_print)
        #Send to duplicate
        p.populate_set_out(path, 'Duplicate')

        msg = 'infoleak:automatic-detection="sql-injection";{}'.format(path)
        p.populate_set_out(msg, 'Tags')

        #statistics
        ## TODO: # FIXME: remove me
        try:
            tld = url_parsed['tld'].decode()
        except:
            tld = url_parsed['tld']
        if tld is not None:
            date = datetime.datetime.now().strftime("%Y%m")
            server_statistics.hincrby('SQLInjection_by_tld:'+date, tld, 1)

if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'LibInjection'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Try to detect SQL injection with LibInjection")

    server_statistics = redis.StrictRedis(
        host=p.config.get("ARDB_Statistics", "host"),
        port=p.config.getint("ARDB_Statistics", "port"),
        db=p.config.getint("ARDB_Statistics", "db"),
        decode_responses=True)

    faup = Faup()

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()

        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(10)
            continue

        else:
            # Do something with the message from the queue
            url, date, path = message.split()
            analyse(url, path)
