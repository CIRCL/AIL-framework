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
from lib.objects import ail_objects
from lib.ConfigLoader import ConfigLoader
from lib import Tracker

from exporter.MailExporter import MailExporterTracker
from exporter.WebHookExporter import WebHookExporterTracker

class Tracker_Regex(AbstractModule):
    """
    Tracker_Regex module for AIL framework
    """
    def __init__(self, queue=True):
        super(Tracker_Regex, self).__init__(queue=queue)

        config_loader = ConfigLoader()

        self.pending_seconds = 5

        self.max_execution_time = config_loader.get_config_int(self.module_name, "max_execution_time")

        # refresh Tracked Regex
        self.tracked_regexs = Tracker.get_tracked_regexs()
        self.last_refresh = time.time()

        # Exporter
        self.exporters = {'mail': MailExporterTracker(),
                          'webhook': WebHookExporterTracker()}

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, obj_id, obj_type='item', subtype=''):
        # refresh Tracked regex
        if self.last_refresh < Tracker.get_tracker_last_updated_by_type('regex'):
            self.tracked_regexs = Tracker.get_tracked_regexs()
            self.last_refresh = time.time()
            self.redis_logger.debug('Tracked regex refreshed')
            print('Tracked regex refreshed')

        obj = ail_objects.get_object(obj_type, subtype, obj_id)
        obj_id = obj.get_id()
        obj_type = obj.get_type()

        # Object Filter
        if obj_type not in self.tracked_regexs:
            return None

        content = obj.get_content(r_str=True)

        for dict_regex in self.tracked_regexs[obj_type]:
            matched = self.regex_findall(dict_regex['regex'], obj_id, content)
            if matched:
                self.new_tracker_found(dict_regex['tracked'], 'regex', obj)

    def new_tracker_found(self, tracker_name, tracker_type, obj):
        obj_id = obj.get_id()
        for tracker_uuid in Tracker.get_trackers_by_tracked_obj_type(tracker_type, obj.get_type(), tracker_name):
            tracker = Tracker.Tracker(tracker_uuid)

            # Filter Object
            filters = tracker.get_filters()
            if ail_objects.is_filtered(obj, filters):
                continue

            print(f'new tracked regex found: {tracker_name} in {obj_id}')
            self.redis_logger.warning(f'new tracked regex found: {tracker_name} in {obj_id}')

            tracker.add(obj.get_type(), obj.get_subtype(r_str=True), obj_id)

            for tag in tracker.get_tags():
                if obj.get_type() == 'item':
                    msg = f'{tag};{obj_id}'
                    self.add_message_to_queue(msg, 'Tags')
                else:
                    obj.add_tag(tag)

            if tracker.mail_export():
                # TODO add matches + custom subjects
                self.exporters['mail'].export(tracker, obj)

            if tracker.webhook_export():
                self.exporters['webhook'].export(tracker, obj)


if __name__ == "__main__":
    module = Tracker_Regex()
    module.run()
    # module.compute('submitted/2023/05/02/submitted_b1e518f1-703b-40f6-8238-d1c22888197e.gz')
