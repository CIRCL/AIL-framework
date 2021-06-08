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
from packages import Date
from packages import Item
from packages import Term

from pubsublogger import publisher

def clean_term_db_stat_token():
    all_stat_date = Term.get_all_token_stat_history()

    list_date_to_keep = Date.get_date_range(31)
    for date in all_stat_date:
        if date not in list_date_to_keep:
            # remove history
            Term.delete_token_statistics_by_date(date)

    print('Term Stats Cleaned')


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
            clean_term_db_stat_token()
            daily_cleaner = False
        else:
            sys.exit(0)
            time.sleep(600)

        new_date = datetime.datetime.now().strftime("%Y%m%d")
        if new_date != current_date:
            current_date = new_date
            daily_cleaner = True
