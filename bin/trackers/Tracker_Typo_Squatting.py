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

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item
from lib import Tracker

from exporter.MailExporter import MailExporterTracker
from exporter.WebHookExporter import WebHookExporterTracker

class Tracker_Typo_Squatting(AbstractModule):
    """
    Tracker_Typo_Squatting module for AIL framework
    """

    def __init__(self):
        super(Tracker_Typo_Squatting, self).__init__()

        self.pending_seconds = 5

        # Refresh typo squatting
        self.typosquat_tracked_words_list = Tracker.get_typosquatting_tracked_words_list()
        self.last_refresh_typosquat = time.time()

        # Exporter
        self.exporters = {'mail': MailExporterTracker(),
                          'webhook': WebHookExporterTracker()}

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        # refresh Tracked typo
        if self.last_refresh_typosquat < Tracker.get_tracker_last_updated_by_type('typosquatting'):
            self.typosquat_tracked_words_list = Tracker.get_typosquatting_tracked_words_list()
            self.last_refresh_typosquat = time.time()
            self.redis_logger.debug('Tracked typosquatting refreshed')
            print('Tracked typosquatting refreshed')

        host, item_id = message.split()

        # Cast message as Item
        for tracker in self.typosquat_tracked_words_list:
            if host in self.typosquat_tracked_words_list[tracker]:
                item = Item(item_id)
                self.new_tracker_found(tracker, 'typosquatting', item)

    def new_tracker_found(self, tracker, tracker_type, item):
        item_id = item.get_id()
        item_source = item.get_source()
        print(f'new tracked typosquatting found: {tracker} in {item_id}')
        self.redis_logger.warning(f'tracker typosquatting: {tracker} in {item_id}')

        for tracker_uuid in Tracker.get_tracker_uuid_list(tracker, tracker_type):
            tracker = Tracker.Tracker(tracker_uuid)

            # Source Filtering
            tracker_sources = tracker.get_sources()
            if tracker_sources and item_source not in tracker_sources:
                continue

            Tracker.add_tracked_item(tracker_uuid, item_id)

            for tag in tracker.get_tags():
                msg = f'{tag};{item_id}'
                self.add_message_to_queue(msg, 'Tags')

            if tracker.mail_export():
                self.exporters['mail'].export(tracker, item)

            if tracker.webhook_export():
                self.exporters['webhook'].export(tracker, item)


if __name__ == '__main__':
    module = Tracker_Typo_Squatting()
    module.run()
    #module.compute('g00gle.com tests/2020/01/01/test.gz')
