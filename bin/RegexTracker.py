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

from Helper import Process
from pubsublogger import publisher

import NotificationHelper

from packages import Item
from packages import Term

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import Tracker
import regex_helper

full_item_url = "/showsavedpaste/?paste="
mail_body_template = "AIL Framework,\nNew occurrence for term tracked regex: {}\nitem id: {}\nurl: {}{}"

dict_regex_tracked = Term.get_regex_tracked_words_dict()
last_refresh = time.time()

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
            mail_subject = Tracker.get_email_subject(term_uuid)
            mail_body = mail_body_template.format(term, item_id, full_item_url, item_id)
        for mail in mail_to_notify:
            NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"
    publisher.info("Script RegexTracker started")

    config_section = 'RegexTracker'
    module_name = "RegexTracker"
    p = Process(config_section)
    max_execution_time = p.config.getint(config_section, "max_execution_time")

    full_item_url = p.config.get("Notifications", "ail_domain") + full_item_url

    redis_cache_key = regex_helper.generate_redis_cache_key(module_name)

    # Regex Frequency
    while True:

        item_id = p.get_from_set()

        if item_id is not None:

            item_date = Item.get_item_date(item_id)
            item_content = Item.get_item_content(item_id)

            for regex in dict_regex_tracked:
                matched = regex_helper.regex_search(module_name, redis_cache_key, dict_regex_tracked[regex], item_id, item_content, max_time=max_execution_time)
                if matched:
                    new_term_found(regex, 'regex', item_id, item_date)

        else:
            time.sleep(5)

        # refresh Tracked term
        if last_refresh < Term.get_tracked_term_last_updated_by_type('regex'):
            dict_regex_tracked = Term.get_regex_tracked_words_dict()
            last_refresh = time.time()
            print('Tracked set refreshed')
