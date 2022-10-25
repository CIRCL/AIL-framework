#!/usr/bin/env python3
# -*-coding:UTF-8 -*
##################################
# The Tracker_Yara trackers module
##################################

##################################
# Import External packages
##################################
import os
import sys
import time
import yara
import requests

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from packages import Term
from lib.objects.Items import Item
from lib import Tracker

import NotificationHelper  # # TODO: refactor

class Tracker_Yara(AbstractModule):

    mail_body_template = "AIL Framework,\nNew YARA match: {}\nitem id: {}\nurl: {}{}"

    """
    Tracker_Yara module for AIL framework
    """
    def __init__(self):
        super(Tracker_Yara, self).__init__()
        self.pending_seconds = 5

        self.full_item_url = self.process.config.get("Notifications", "ail_domain") + "/object/item?id="

        # Load Yara rules
        self.rules = Tracker.reload_yara_rules()
        self.last_refresh = time.time()

        self.item = None

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, item_id):
        # refresh YARA list
        if self.last_refresh < Tracker.get_tracker_last_updated_by_type('yara'):
            self.rules = Tracker.reload_yara_rules()
            self.last_refresh = time.time()
            self.redis_logger.debug('Tracked set refreshed')
            print('Tracked set refreshed')

        self.item = Item(item_id)
        item_content = self.item.get_content()
        try:
            yara_match = self.rules.match(data=item_content, callback=self.yara_rules_match,
                                          which_callbacks=yara.CALLBACK_MATCHES, timeout=60)
            if yara_match:
                self.redis_logger.info(f'{self.item.get_id()}: {yara_match}')
                print(f'{self.item.get_id()}: {yara_match}')
        except yara.TimeoutError as e:
            print(f'{self.item.get_id()}: yara scanning timed out')
            self.redis_logger.info(f'{self.item.get_id()}: yara scanning timed out')

    def yara_rules_match(self, data):
        tracker_uuid = data['namespace']
        item_id = self.item.get_id()
        item_source = self.item.get_source()
        item_date = self.item.get_date()

        # Source Filtering
        tracker_sources = Tracker.get_tracker_uuid_sources(tracker_uuid)
        if tracker_sources and item_source not in tracker_sources:
            print(f'Source Filtering: {data["rule"]}')
            return yara.CALLBACK_CONTINUE

        Tracker.add_tracked_item(tracker_uuid, item_id)

        # Tags
        tags_to_add = Tracker.get_tracker_tags(tracker_uuid)
        for tag in tags_to_add:
            msg = '{};{}'.format(tag, item_id)
            self.send_message_to_queue(msg, 'Tags')

        # Mails
        mail_to_notify = Tracker.get_tracker_mails(tracker_uuid)
        if mail_to_notify:
            mail_subject = Tracker.get_email_subject(tracker_uuid)
            mail_body = Tracker_Yara.mail_body_template.format(data['rule'], item_id, self.full_item_url, item_id)
            for mail in mail_to_notify:
                self.redis_logger.debug(f'Send Mail {mail_subject}')
                print(f'Send Mail {mail_subject}')
                NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)

        # Webhook
        webhook_to_post = Term.get_term_webhook(tracker_uuid)
        if webhook_to_post:
            json_request = {"trackerId": tracker_uuid,
                            "itemId": item_id,
                            "itemURL": self.full_item_url + item_id,
                            "dataRule": data["rule"],
                            "itemSource": item_source,
                            "itemDate": item_date,
                            "tags": tags_to_add,
                            "emailNotification": f'{mail_to_notify}',
                            "trackerType": "yara"
                            }
            try:
                response = requests.post(webhook_to_post, json=json_request)
                if response.status_code >= 400:
                    self.redis_logger.error(f"Webhook request failed for {webhook_to_post}\nReason: {response.reason}")
            except:
                self.redis_logger.error(f"Webhook request failed for {webhook_to_post}\nReason: Something went wrong")

        return yara.CALLBACK_CONTINUE


if __name__ == '__main__':
    module = Tracker_Yara()
    module.run()
