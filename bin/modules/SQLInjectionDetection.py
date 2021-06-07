#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The SQLInjectionDetection Module
================================

This module is consuming the Redis-list created by the Urls module.

It test different possibility to makes some sqlInjection.

"""

import os
import sys
import re
import redis
import urllib.request

from datetime import datetime
from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from packages.Item import Item

class SQLInjectionDetection(AbstractModule):
    """docstring for SQLInjectionDetection module."""

    # # TODO: IMPROVE ME
    # Reference: https://github.com/stamparm/maltrail/blob/master/core/settings.py
    SQLI_REGEX = r"information_schema|sysdatabases|sysusers|floor\(rand\(|ORDER BY \d+|\bUNION\s+(ALL\s+)?SELECT\b|\b(UPDATEXML|EXTRACTVALUE)\(|\bCASE[^\w]+WHEN.*THEN\b|\bWAITFOR[^\w]+DELAY\b|\bCONVERT\(|VARCHAR\(|\bCOUNT\(\*\)|\b(pg_)?sleep\(|\bSELECT\b.*\bFROM\b.*\b(WHERE|GROUP|ORDER)\b|\bSELECT \w+ FROM \w+|\b(AND|OR|SELECT)\b.*/\*.*\*/|/\*.*\*/.*\b(AND|OR|SELECT)\b|\b(AND|OR)[^\w]+\d+['\") ]?[=><]['\"( ]?\d+|ODBC;DRIVER|\bINTO\s+(OUT|DUMP)FILE"

    def __init__(self):
        super(SQLInjectionDetection, self).__init__()

        self.faup = Faup()

        config_loader = ConfigLoader()
        self.server_statistics = config_loader.get_redis_conn("ARDB_Statistics")

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        url, id = message.split()

        if self.is_sql_injection(url):
            self.faup.decode(url)
            url_parsed = self.faup.get()

            item = Item(id)
            item_id = item.get_id()
            print(f"Detected SQL in URL: {item_id}")
            print(urllib.request.unquote(url))
            to_print = f'SQLInjection;{item.get_source()};{item.get_date()};{item.get_basename()};Detected SQL in URL;{item_id}'
            self.redis_logger.warning(to_print)

            # Send to duplicate
            self.send_message_to_queue(item_id, 'Duplicate')

            # Tag
            msg = f'infoleak:automatic-detection="sql-injection";{item_id}'
            self.send_message_to_queue(msg, 'Tags')

            # statistics
            tld = url_parsed['tld']
            if tld is not None:
                ## TODO: # FIXME: remove me
                try:
                    tld = tld.decode()
                except:
                    pass
                date = datetime.now().strftime("%Y%m")
                self.server_statistics.hincrby(f'SQLInjection_by_tld:{date}', tld, 1)

    # Try to detect if the url passed might be an sql injection by appliying the regex
    # defined above on it.
    def is_sql_injection(self, url_parsed):
        line = urllib.request.unquote(url_parsed)

        return re.search(SQLInjectionDetection.SQLI_REGEX, line, re.I) is not None


if __name__ == "__main__":

    module = SQLInjectionDetection()
    module.run()
