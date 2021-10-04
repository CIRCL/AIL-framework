#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Tracker_Regex trackers module
===================

This Module is used for regex tracking.
It processes every item coming from the global module and test the regex

"""
import os
import re
import sys
import time
import requests

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

    mail_body_template = "AIL Framework,\nNew occurrence for tracked regex: {}\nitem id: {}\nurl: {}{}"

    """
    Tracker_Regex module for AIL framework
    """
    def __init__(self):
        super(Tracker_Regex, self).__init__()

        self.pending_seconds = 5

        self.max_execution_time = self.process.config.getint(self.module_name, "max_execution_time")

        self.full_item_url = self.process.config.get("Notifications", "ail_domain") + "/object/item?id="

        self.redis_cache_key = regex_helper.generate_redis_cache_key(self.module_name)

        # refresh Tracked Regex
        self.dict_regex_tracked = Term.get_regex_tracked_words_dict()
        self.last_refresh = time.time()

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, item_id):
        # refresh Tracked regex
        if self.last_refresh < Tracker.get_tracker_last_updated_by_type('regex'):
            self.dict_regex_tracked = Term.get_regex_tracked_words_dict()
            self.last_refresh = time.time()
            self.redis_logger.debug('Tracked regex refreshed')
            print('Tracked regex refreshed')

        item = Item(item_id)
        item_id = item.get_id()
        item_content = item.get_content()

        for regex in self.dict_regex_tracked:
            matched = regex_helper.regex_search(self.module_name, self.redis_cache_key, self.dict_regex_tracked[regex], item_id, item_content, max_time=self.max_execution_time)
            if matched:
                self.new_tracker_found(regex, 'regex', item)

    def new_tracker_found(self, tracker, tracker_type, item):
        uuid_list = Tracker.get_tracker_uuid_list(tracker, tracker_type)

        item_id = item.get_id()
        print(f'new tracked regex found: {tracker} in {item_id}')

        for tracker_uuid in uuid_list:
            # Source Filtering
            item_source =  item.get_source()
            item_date =    item.get_date()

            tracker_sources = Tracker.get_tracker_uuid_sources(tracker_uuid)
            if tracker_sources and item_source not in tracker_sources:
                continue

            Tracker.add_tracked_item(tracker_uuid, item_id)

            tags_to_add = Tracker.get_tracker_tags(tracker_uuid)
            for tag in tags_to_add:
                msg = f'{tag};{item_id}'
                self.send_message_to_queue(msg, 'Tags')

            mail_to_notify = Tracker.get_tracker_mails(tracker_uuid)
            if mail_to_notify:
                mail_subject = Tracker.get_email_subject(tracker_uuid)
                mail_body = Tracker_Regex.mail_body_template.format(tracker, item_id, self.full_item_url, item_id)
            for mail in mail_to_notify:
                NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)

            # Webhook
            webhook_to_post = Term.get_term_webhook(tracker_uuid)
            if webhook_to_post:
                json_request = {"trackerId": tracker_uuid,
                                "itemId": item_id,
                                "itemURL": self.full_item_url + item_id,
                                "tracker": tracker,
                                "itemSource": item_source,
                                "itemDate": item_date,
                                "tags": tags_to_add,
                                "emailNotification": f'{mail_to_notify}',
                                "trackerType": tracker_type
                                }
                try:
                    response = requests.post(webhook_to_post, json=json_request)
                    if response.status_code >= 400:
                        self.redis_logger.error(f"Webhook request failed for {webhook_to_post}\nReason: {response.reason}")
                except:
                    self.redis_logger.error(f"Webhook request failed for {webhook_to_post}\nReason: Something went wrong")


if __name__ == "__main__":
    module = Tracker_Regex()
    module.run()
