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

    config_section = 'Browse_warning_paste'

    p = Process(config_section)

    server = redis.StrictRedis(
                host=p.config.get("Redis_Level_DB", "host"),
                port=p.config.get("Redis_Level_DB", "port"),
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

            # Add in redis
            # Format in set: WARNING_moduleName -> p_path
            key = "WARNING_" + module_name
            print key + ' -> ' + p_path
            server.sadd(key, p_path)

            publisher.info('Saved in warning paste {}'.format(p_path))
            #print 'Saved in warning paste {}'.format(p_path)

