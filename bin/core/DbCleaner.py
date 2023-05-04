#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The DbCleaner Module
===================

"""
import os
import sys
import time
import datetime

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################

from pubsublogger import publisher

if __name__ == "__main__":

    publisher.port = 6380
    publisher.channel = "Script"
    publisher.info("DbCleaner started")

    # low priority
    time.sleep(180)

    daily_cleaner = True
    current_date = datetime.datetime.now().strftime("%Y%m%d")

    while True:

        if daily_cleaner:

            daily_cleaner = False
        else:
            sys.exit(0)
            time.sleep(600)

        new_date = datetime.datetime.now().strftime("%Y%m%d")
        if new_date != current_date:
            current_date = new_date
            daily_cleaner = True
