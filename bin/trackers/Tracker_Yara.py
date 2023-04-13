#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Tracker_Yara trackers module
===================

"""

##################################
# Import External packages
##################################
import os
import sys
import time
import yara

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item
from lib import Tracker

from exporter.MailExporter import MailExporterTracker
from exporter.WebHookExporter import WebHookExporterTracker


class Tracker_Yara(AbstractModule):
    """
    Tracker_Yara module for AIL framework
    """
    def __init__(self, queue=True):
        super(Tracker_Yara, self).__init__(queue=queue)
        self.pending_seconds = 5

        # Load Yara rules
        self.rules = Tracker.reload_yara_rules()
        self.last_refresh = time.time()

        self.item = None

        # Exporter
        self.exporters = {'mail': MailExporterTracker(),
                          'webhook': WebHookExporterTracker()}

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, item_id, item_content=None):
        # refresh YARA list
        if self.last_refresh < Tracker.get_tracker_last_updated_by_type('yara'):
            self.rules = Tracker.reload_yara_rules()
            self.last_refresh = time.time()
            self.redis_logger.debug('Tracked set refreshed')
            print('Tracked set refreshed')

        self.item = Item(item_id)
        if not item_content:
            item_content = self.item.get_content()

        try:
            yara_match = self.rules.match(data=item_content, callback=self.yara_rules_match,
                                          which_callbacks=yara.CALLBACK_MATCHES, timeout=60)
            if yara_match:
                self.redis_logger.warning(f'tracker yara: new match {self.item.get_id()}: {yara_match}')
                print(f'{self.item.get_id()}: {yara_match}')
        except yara.TimeoutError:
            print(f'{self.item.get_id()}: yara scanning timed out')
            self.redis_logger.info(f'{self.item.get_id()}: yara scanning timed out')

    def yara_rules_match(self, data):
        tracker_uuid = data['namespace']
        item_id = self.item.get_id()

        item = Item(item_id)
        item_source = self.item.get_source()

        tracker = Tracker.Tracker(tracker_uuid)

        # Source Filtering
        tracker_sources = tracker.get_sources()
        if tracker_sources and item_source not in tracker_sources:
            print(f'Source Filtering: {data["rule"]}')
            return yara.CALLBACK_CONTINUE

        Tracker.add_tracked_item(tracker_uuid, item_id)  # TODO

        # Tags
        for tag in tracker.get_tags():
            msg = f'{tag};{item_id}'
            self.add_message_to_queue(msg, 'Tags')

        # Mails
        if tracker.mail_export():
            # TODO add matches + custom subjects
            self.exporters['mail'].export(tracker, item)

        # Webhook
        if tracker.webhook_export():
            self.exporters['webhook'].export(tracker, item)

        return yara.CALLBACK_CONTINUE


if __name__ == '__main__':
    module = Tracker_Yara()
    module.run()
