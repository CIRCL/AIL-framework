#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The Browse_warning_paste module
====================

This module saved signaled paste (logged as 'warning') in redis for further usage
like browsing by category

Its input comes from other modules, namely:
    Credential, CreditCard, SQLinjection, CVE, Keys, Mail and Phone

"""

import redis
import time
from datetime import datetime, timedelta
from packages import Paste
from pubsublogger import publisher
from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'alertHandler'

    p = Process(config_section)

    # port generated automatically depending on the date
    curYear = datetime.now().year
    server = redis.StrictRedis(
                host=p.config.get("Redis_Level_DB", "host"),
                port=curYear,
                db=p.config.get("Redis_Level_DB", "db"))

    # FUNCTIONS #
    publisher.info("Script duplicate started")

    while True:
            message = p.get_from_set()
            if message is not None:
                module_name, p_path = message.split(';')
                #PST = Paste.Paste(p_path)
            else:
                publisher.debug("Script Attribute is idling 10s")
                time.sleep(10)
                continue

            # Add in redis for browseWarningPaste
            # Format in set: WARNING_moduleName -> p_path
            key = "WARNING_" + module_name
            server.sadd(key, p_path)

            publisher.info('Saved warning paste {}'.format(p_path))

