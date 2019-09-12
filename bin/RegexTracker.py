#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
This Module is used for regex tracking.
It processes every paste coming from the global module and test the regexs
supplied in  the term webpage.

"""
import os
import re
import sys
import time
import signal

from Helper import Process
from pubsublogger import publisher

import NotificationHelper

from packages import Item
from packages import Term

full_item_url = "/showsavedpaste/?paste="
mail_body_template = "AIL Framework,\nNew occurrence for term tracked regex: {}\nitem id: {}\nurl: {}{}"

dict_regex_tracked = Term.get_regex_tracked_words_dict()
last_refresh = time.time()

class TimeoutException(Exception):
    pass
def timeout_handler(signum, frame):
    raise TimeoutException
signal.signal(signal.SIGALRM, timeout_handler)

def new_term_found(term, term_type, item_id, item_date):
    uuid_list = Term.get_term_uuid_list(term, 'regex')
    print('new tracked term found: {} in {}'.format(term, item_id))

    for term_uuid in uuid_list:
        Term.add_tracked_item(term_uuid, item_id, item_date)

        tags_to_add = Term.get_term_tags(term_uuid)
        for tag in tags_to_add:
            msg = '{};{}'.format(tag, item_id)
            p.populate_set_out(msg, 'Tags')

        mail_to_notify = Term.get_term_mails(term_uuid)
        if mail_to_notify:
            mail_body = mail_body_template.format(term, item_id, full_item_url, item_id)
        for mail in mail_to_notify:
            NotificationHelper.sendEmailNotification(mail, 'Term Tracker', mail_body)

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"
    publisher.info("Script RegexTracker started")

    config_section = 'RegexTracker'
    p = Process(config_section)
    max_execution_time = p.config.getint(config_section, "max_execution_time")

    ull_item_url = p.config.get("Notifications", "ail_domain") + full_item_url

    # Regex Frequency
    while True:

        item_id = p.get_from_set()

        if item_id is not None:

            item_date = Item.get_item_date(item_id)
            item_content = Item.get_item_content(item_id)

            for regex in dict_regex_tracked:

                signal.alarm(max_execution_time)
                try:
                    matched = dict_regex_tracked[regex].search(item_content)
                except TimeoutException:
                    print ("{0} processing timeout".format(paste.p_rel_path))
                    continue
                else:
                    signal.alarm(0)

                if matched:
                    new_term_found(regex, 'regex', item_id, item_date)


        else:
            time.sleep(5)

        # refresh Tracked term
        if last_refresh < Term.get_tracked_term_last_updated_by_type('regex'):
            dict_regex_tracked = Term.get_regex_tracked_words_dict()
            last_refresh = time.time()
            print('Tracked set refreshed')
