#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Tracker_Typo_Squatting Module
===================

"""

##################################
# Import External packages
##################################
import os
import sys
import time
import requests


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
import NotificationHelper
from packages.Item import Item
from lib import Tracker

class Tracker_Typo_Squatting(AbstractModule):
    mail_body_template = "AIL Framework,\nNew occurrence for tracked Typo: {}\nitem id: {}\nurl: {}{}"

    """
    Tracker_Typo_Squatting module for AIL framework
    """

    def __init__(self):
        super(Tracker_Typo_Squatting, self).__init__()

        self.pending_seconds = 5

        self.full_item_url = self.process.config.get("Notifications", "ail_domain") + "/object/item?id="

        # loads typosquatting
        self.typosquat_tracked_words_list = Tracker.get_typosquatting_tracked_words_list()
        self.last_refresh_typosquat = time.time()

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        # refresh Tracked typo
        if self.last_refresh_typosquat < Tracker.get_tracker_last_updated_by_type('typosquatting'):
            self.typosquat_tracked_words_list = Tracker.get_typosquatting_tracked_words_list()
            self.last_refresh_typosquat = time.time()
            self.redis_logger.debug('Tracked typosquatting refreshed')
            print('Tracked typosquatting refreshed')

        host, id = message.split()
        item = Item(id)

        # Cast message as Item
        for key in self.typosquat_tracked_words_list:
            #print(key)
            if host in self.typosquat_tracked_words_list[key]:
                self.new_tracker_found(key, 'typosquatting', item)

    def new_tracker_found(self, tracker, tracker_type, item):
        item_id = item.get_id()
        item_date = item.get_date()
        item_source = item.get_source()
        #self.redis_logger.info(f'new tracked typo found: {tracker} in {item_id}')
        print(f'new tracked typosquatting found: {tracker} in {item_id}')

        print(Tracker.get_tracker_uuid_list(tracker, tracker_type))
        for tracker_uuid in Tracker.get_tracker_uuid_list(tracker, tracker_type):
            # Source Filtering
            tracker_sources = Tracker.get_tracker_uuid_sources(tracker)
            if tracker_sources and item_source not in tracker_sources:
                continue

            Tracker.add_tracked_item(tracker_uuid, item_id)

            # Tags
            tags_to_add = Tracker.get_tracker_tags(tracker_uuid)
            for tag in tags_to_add:
                msg = f'{tag};{item_id}'
                self.send_message_to_queue(msg, 'Tags')

            mail_to_notify = Tracker.get_tracker_mails(tracker_uuid)
            if mail_to_notify:
                mail_subject = Tracker.get_email_subject(tracker_uuid)
                mail_body = Tracker_Typo_Squatting.mail_body_template.format(tracker, item_id, self.full_item_url, item_id)
            for mail in mail_to_notify:
                NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)

            # Webhook
            webhook_to_post = Tracker.get_tracker_webhook(tracker_uuid)
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



if __name__ == '__main__':
    module = Tracker_Typo_Squatting()
    module.run()
    #module.compute('g00gle.com tests/2020/01/01/test.gz')
