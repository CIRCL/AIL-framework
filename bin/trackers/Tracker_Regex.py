#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Tracker_Regex trackers module
===================

This Module is used for regex tracking.
It processes every item coming from the global module and test the regex

"""
import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item
from packages import Term
from lib import Tracker

from exporter.MailExporter import MailExporterTracker
from exporter.WebHookExporter import WebHookExporterTracker

class Tracker_Regex(AbstractModule):
    """
    Tracker_Regex module for AIL framework
    """
    def __init__(self):
        super(Tracker_Regex, self).__init__()

        self.pending_seconds = 5

        self.max_execution_time = self.process.config.getint(self.module_name, "max_execution_time")

        # refresh Tracked Regex
        self.dict_regex_tracked = Term.get_regex_tracked_words_dict()
        self.last_refresh = time.time()

        # Exporter
        self.exporters = {'mail': MailExporterTracker(),
                          'webhook': WebHookExporterTracker()}

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, item_id, content=None):
        # refresh Tracked regex
        if self.last_refresh < Tracker.get_tracker_last_updated_by_type('regex'):
            self.dict_regex_tracked = Term.get_regex_tracked_words_dict()
            self.last_refresh = time.time()
            self.redis_logger.debug('Tracked regex refreshed')
            print('Tracked regex refreshed')

        item = Item(item_id)
        item_id = item.get_id()
        if not content:
            content = item.get_content()

        for regex in self.dict_regex_tracked:
            matched = self.regex_findall(self.dict_regex_tracked[regex], item_id, content)
            if matched:
                self.new_tracker_found(regex, 'regex', item)

    def new_tracker_found(self, tracker_name, tracker_type, item):
        uuid_list = Tracker.get_tracker_uuid_list(tracker_name, tracker_type)

        item_id = item.get_id()
        # date = item.get_date()
        item_source = item.get_source()

        for tracker_uuid in uuid_list:
            tracker = Tracker.Tracker(tracker_uuid)

            # Source Filtering
            tracker_sources = tracker.get_sources()
            if tracker_sources and item_source not in tracker_sources:
                continue

            print(f'new tracked regex found: {tracker_name} in {item_id}')
            self.redis_logger.warning(f'new tracked regex found: {tracker_name} in {item_id}')
            # TODO
            Tracker.add_tracked_item(tracker_uuid, item_id)

            for tag in tracker.get_tags():
                msg = f'{tag};{item_id}'
                self.send_message_to_queue(msg, 'Tags')

            if tracker.mail_export():
                # TODO add matches + custom subjects
                self.exporters['mail'].export(tracker, item)

            if tracker.webhook_export():
                self.exporters['webhook'].export(tracker, item)


if __name__ == "__main__":
    module = Tracker_Regex()
    module.run()
