#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Tracker_Regex trackers module
===================

This Module is used for regex tracking.
It processes every item coming from the global module and test the regexs

"""
import os
import re
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from packages.Item import Item
from packages import Term
from lib import Tracker
from lib import regex_helper

import NotificationHelper

class Tracker_Regex(AbstractModule):

    mail_body_template = "AIL Framework,\nNew occurrence for term tracked regex: {}\nitem id: {}\nurl: {}{}"

    """
    Tracker_Regex module for AIL framework
    """
    def __init__(self):
        super(Tracker_Regex, self).__init__()

        self.pending_seconds = 5

        self.max_execution_time = self.process.config.getint(self.module_name, "max_execution_time")

        self.full_item_url = self.process.config.get("Notifications", "ail_domain") + "/object/item?id="

        self.redis_cache_key = regex_helper.generate_redis_cache_key(self.module_name)

        # refresh Tracked term
        self.dict_regex_tracked = Term.get_regex_tracked_words_dict()
        self.last_refresh = time.time()

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, item_id):
        # refresh Tracked regex
        if self.last_refresh < Term.get_tracked_term_last_updated_by_type('regex'):
            self.dict_regex_tracked = Term.get_regex_tracked_words_dict()
            self.last_refresh = time.time()
            self.redis_logger.debug('Tracked word refreshed')
            print('Tracked set refreshed')

        item = Item(item_id)
        item_id = item.get_id()
        item_date = item.get_date()
        item_content = item.get_content()

        for regex in self.dict_regex_tracked:
            matched = regex_helper.regex_search(self.module_name, self.redis_cache_key, self.dict_regex_tracked[regex], item_id, item_content, max_time=self.max_execution_time)
            if matched:
                self.new_term_found(regex, 'regex', item_id, item_date)

    def new_term_found(self, term, tracker_type, item_id, item_date):
        uuid_list = Term.get_term_uuid_list(term, tracker_type)
        print('new tracked regex found: {} in {}'.format(term, item_id))

        for tracker_uuid in uuid_list:
            Term.add_tracked_item(tracker_uuid, item_id, item_date)

            tags_to_add = Term.get_term_tags(tracker_uuid)
            for tag in tags_to_add:
                msg = '{};{}'.format(tag, item_id)
                self.send_message_to_queue(msg, 'Tags')

            mail_to_notify = Term.get_term_mails(tracker_uuid)
            if mail_to_notify:
                mail_subject = Tracker.get_email_subject(tracker_uuid)
                mail_body = Tracker_Regex.mail_body_template.format(term, item_id, self.full_item_url, item_id)
            for mail in mail_to_notify:
                NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)

if __name__ == "__main__":

    module = Tracker_Regex()
    module.run()
