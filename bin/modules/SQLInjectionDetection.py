#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The SQLInjectionDetection Module
================================

This module is consuming the Redis-list created by the Urls module.

Test different possibility to makes some sqlInjection.

"""

import os
import sys
import urllib.request

from urllib.parse import unquote

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
# from lib.ConfigLoader import ConfigLoader
# from lib import Statistics

class SQLInjectionDetection(AbstractModule):
    """docstring for SQLInjectionDetection module."""

    MAX_URL_LENGTH = 16384

    # # TODO: IMPROVE ME
    # Reference: https://github.com/stamparm/maltrail/blob/master/core/settings.py
    SQLI_REGEX = r"(?i:information_schema|sysdatabases|sysusers|floor\(rand\(|ORDER BY \d+|\bUNION\s+(ALL\s+)?SELECT\b|\b(UPDATEXML|EXTRACTVALUE)\(|\bCASE[^\w]+WHEN.{0,2048}THEN\b|\bWAITFOR[^\w]+DELAY\b|\bCONVERT\(|VARCHAR\(|\bCOUNT\(\*\)|\b(pg_)?sleep\(|\bSELECT\b.{0,2048}\bFROM\b.{0,2048}\b(WHERE|GROUP|ORDER)\b|\bSELECT \w+ FROM \w+|\b(AND|OR|SELECT)\b.{0,2048}/\*.{0,2048}\*/|/\*.{0,2048}\*/.{0,2048}\b(AND|OR|SELECT)\b|\b(AND|OR)[^\w]+\d+['\") ]?[=><]['\"( ]?\d+|ODBC;DRIVER|\bINTO\s+(OUT|DUMP)FILE)"

    def __init__(self):
        super(SQLInjectionDetection, self).__init__()

        self.logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        url = message

        if self.is_sql_injection(url):
            print(f"Detected SQL in URL: {self.obj.get_global_id()}")
            print(urllib.request.unquote(url))

            # Tag
            tag = f'infoleak:automatic-detection="sql-injection"'
            self.add_message_to_queue(message=tag, queue='Tags')

            # statistics
            # tld = url_parsed['tld']
            # if tld is not None:
            #     # # TODO: # FIXME: remove me
            #     try:
            #         tld = tld.decode()
            #     except:
            #         pass
            #     date = datetime.now().strftime("%Y%m")
            #     Statistics.add_module_tld_stats_by_date(self.module_name, date, tld, 1)

    # Try to detect if the url passed might be a sql injection by applying the regex
    # defined above on it.
    def is_sql_injection(self, url_parsed):
        if len(url_parsed) > self.MAX_URL_LENGTH:
            self.logger.warning('Skipping SQL injection detection for oversized URL')
            return False
        line = unquote(url_parsed)
        if len(line) > self.MAX_URL_LENGTH:
            self.logger.warning('Skipping SQL injection detection for oversized decoded URL')
            return False
        return self.regex_search(self.SQLI_REGEX, self.obj.get_id(), line)


if __name__ == "__main__":
    module = SQLInjectionDetection()
    module.run()
