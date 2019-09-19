#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The SQLInjectionDetection Module
================================

This module is consuming the Redis-list created by the Web module.

It test different possibility to makes some sqlInjection.

"""

import time
import datetime
import redis
import urllib.request
import re
from pubsublogger import publisher
from Helper import Process
from packages import Paste
from pyfaup.faup import Faup

# Reference: https://github.com/stamparm/maltrail/blob/master/core/settings.py
SQLI_REGEX = r"information_schema|sysdatabases|sysusers|floor\(rand\(|ORDER BY \d+|\bUNION\s+(ALL\s+)?SELECT\b|\b(UPDATEXML|EXTRACTVALUE)\(|\bCASE[^\w]+WHEN.*THEN\b|\bWAITFOR[^\w]+DELAY\b|\bCONVERT\(|VARCHAR\(|\bCOUNT\(\*\)|\b(pg_)?sleep\(|\bSELECT\b.*\bFROM\b.*\b(WHERE|GROUP|ORDER)\b|\bSELECT \w+ FROM \w+|\b(AND|OR|SELECT)\b.*/\*.*\*/|/\*.*\*/.*\b(AND|OR|SELECT)\b|\b(AND|OR)[^\w]+\d+['\") ]?[=><]['\"( ]?\d+|ODBC;DRIVER|\bINTO\s+(OUT|DUMP)FILE"

def analyse(url, path):
    if is_sql_injection(url.decode()):
        faup.decode(url)
        url_parsed = faup.get()
        paste = Paste.Paste(path)
        print("Detected SQL in URL: ")
        print(urllib.request.unquote(url))
        to_print = 'SQLInjection;{};{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, "Detected SQL in URL", paste.p_rel_path)
        publisher.warning(to_print)
        #Send to duplicate
        p.populate_set_out(path, 'Duplicate')

        msg = 'infoleak:automatic-detection="sql-injection";{}'.format(path)
        p.populate_set_out(msg, 'Tags')

        #statistics
        tld = url_parsed['tld']
        if tld is not None:
            ## TODO: # FIXME: remove me
            try:
                tld = tld.decode()
            except:
                pass
            date = datetime.datetime.now().strftime("%Y%m")
            server_statistics.hincrby('SQLInjection_by_tld:'+date, tld, 1)

# Try to detect if the url passed might be an sql injection by appliying the regex
# defined above on it.
def is_sql_injection(url_parsed):
    line = urllib.request.unquote(url_parsed)
    line = str.upper(line)

    return re.search(SQLI_REGEX, url_parsed, re.I) is not None


if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'SQLInjectionDetection'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Try to detect SQL injection")

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
