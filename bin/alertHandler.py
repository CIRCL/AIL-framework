#!/usr/bin/env python3.5
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

from pymisp import PyMISP
import ailleakObject
import sys
sys.path.append('../')
try:
    from mispKEYS import misp_url, misp_key, misp_verifycert
    flag_misp = True
except:
    print('Misp keys not present')
    flag_misp = False

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'alertHandler'

    p = Process(config_section)
    if flag_misp:
        try:
            pymisp = PyMISP(misp_url, misp_key, misp_verifycert)
            print('Connected to MISP:', misp_url)
        except:
            flag_misp = False
            print('Not connected to MISP')

    if flag_misp:
        wrapper = ailleakObject.ObjectWrapper(pymisp)

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
                #decode because of pyhton3
                module_name, p_path = message.split(';')
                print("new alert : {}".format(module_name))
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

            # Create MISP AIL-leak object and push it
            if flag_misp:
                allowed_modules = ['credential', 'phone', 'creditcards']
                if module_name in allowed_modules:
                    wrapper.add_new_object(module_name, p_path)
                    wrapper.pushToMISP()
                else:
                    print('not pushing to MISP:', module_name, p_path)
