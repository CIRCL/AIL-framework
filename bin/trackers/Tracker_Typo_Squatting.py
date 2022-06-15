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
import signal
import requests


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
import NotificationHelper
from packages.Item import Item
from packages import Term
from lib import Tracker

class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException


signal.signal(signal.SIGALRM, timeout_handler)


class Tracker_Typo_Squatting(AbstractModule):
    mail_body_template = "AIL Framework,\nNew occurrence for tracked Typo: {}\nitem id: {}\nurl: {}{}"

    """
    Tracker_Typo_Squatting module for AIL framework
    """

    def __init__(self):
        super(Tracker_Typo_Squatting, self).__init__()

        self.pending_seconds = 5

        #self.max_execution_time = self.process.config.getint('Tracker_Typo_Squatting', "max_execution_time")

        self.full_item_url = self.process.config.get("Notifications", "ail_domain") + "/object/item?id="

        # loads tracked words
        self.typosquat_tracked_words_list = Tracker.get_typosquatting_tracked_words_list()
        self.last_refresh_typosquat = time.time()

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        # refresh Tracked typo
        if self.last_refresh_typosquat < Term.get_tracked_term_last_updated_by_type('typosquatting'):
            self.typosquat_tracked_words_list = Tracker.get_typosquatting_tracked_words_list()
            self.last_refresh_typosquat = time.time()
            self.redis_logger.debug('Tracked typosquatting refreshed')
            print('Tracked typosquatting refreshed')

        host, id = message.split()
        item = Item(id)
        
        # Cast message as Item
        for key in self.typosquat_tracked_words_list.keys():
            #print(key)
            if host in self.typosquat_tracked_words_list[key]:
                self.new_term_found(key, 'typosquatting', item)

    def new_term_found(self, term, term_type, item):
        uuid_list = Term.get_term_uuid_list(term, term_type)

        item_id = item.get_id()
        item_date = item.get_date()
        item_source = item.get_source()
        self.redis_logger.info(f'new tracked typo found: {term} in {item_id}')
        print(f'new tracked typo found: {term} in {item_id}')
        for term_uuid in uuid_list:
            tracker_sources = Tracker.get_tracker_uuid_sources(term_uuid)
            if not tracker_sources or item_source in tracker_sources:
                Tracker.add_tracked_item(term_uuid, item_id)

                tags_to_add = Term.get_term_tags(term_uuid)
                for tag in tags_to_add:
                    msg = '{};{}'.format(tag, item_id)
                    self.send_message_to_queue(msg, 'Tags')

                mail_to_notify = Term.get_term_mails(term_uuid)
                if mail_to_notify:
                    mail_subject = Tracker.get_email_subject(term_uuid)
                    mail_body = Tracker_Typo_Squatting.mail_body_template.format(term, item_id, self.full_item_url, item_id)
                for mail in mail_to_notify:
                    self.redis_logger.debug(f'Send Mail {mail_subject}')
                    print(f'S        print(item_content)end Mail {mail_subject}')
                    NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)

                # Webhook
                webhook_to_post = Term.get_term_webhook(term_uuid)
                if webhook_to_post:
                    json_request = {"trackerId": term_uuid,
                                    "itemId": item_id,
                                    "itemURL": self.full_item_url + item_id,
                                    "term": term,
                                    "itemSource": item_source,
                                    "itemDate": item_date,
                                    "tags": tags_to_add,
                                    "emailNotification": f'{mail_to_notify}',
                                    "trackerType": term_type
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
