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

        self.obj = None

        # Exporter
        self.exporters = {'mail': MailExporterTracker(),
                          'webhook': WebHookExporterTracker()}

        self.logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        # refresh Tracked regex
        if self.last_refresh < Tracker.get_tracker_last_updated_by_type('regex'):
            self.tracked_regexs = Tracker.get_tracked_regexs()
            self.last_refresh = time.time()
            print('Tracked regex refreshed')

        obj = self.get_obj()
        obj_id = obj.get_id()
        obj_type = obj.get_type()

        # Object Filter
        if obj_type not in self.tracked_regexs:
            return None

        content = obj.get_content()

        for dict_regex in self.tracked_regexs[obj_type]:
            matches = self.regex_finditer(dict_regex['regex'], obj_id, content)
            if matches:
                self.new_tracker_found(dict_regex['tracked'], 'regex', obj, matches)

    def extract_matches(self, re_matches, limit=500, lines=5):
        matches = []
        content = self.obj.get_content()
        l_content = len(content)
        for match in re_matches:
            start = match[0]
            value = match[2]
            end = match[1]

            # Start
            if start > limit:
                i_start = start - limit
            else:
                i_start = 0
            str_start = content[i_start:start].splitlines()
            if len(str_start) > lines:
                str_start = '\n'.join(str_start[-lines + 1:])
            else:
                str_start = content[i_start:start]

            # End
            if end + limit > l_content:
                i_end = l_content
            else:
                i_end = end + limit
            str_end = content[end:i_end].splitlines()
            if len(str_end) > lines:
                str_end = '\n'.join(str_end[:lines + 1])
            else:
                str_end = content[end:i_end]
            matches.append((value, f'{str_start}{value}{str_end}'))
        return matches

    def new_tracker_found(self, tracker_name, tracker_type, obj, re_matches):
        obj_id = obj.get_id()
        matches = None
        for tracker_uuid in Tracker.get_trackers_by_tracked_obj_type(tracker_type, obj.get_type(), tracker_name):
            tracker = Tracker.Tracker(tracker_uuid)

            # Filter Object
            filters = tracker.get_filters()
            if ail_objects.is_filtered(obj, filters):
                continue

            print(f'new tracked regex found: {tracker_name} in {self.obj.get_global_id()}')

            tracker.add(obj.get_type(), obj.get_subtype(r_str=True), obj_id)

            for tag in tracker.get_tags():
                if obj.get_type() == 'item':
                    self.add_message_to_queue(message=tag, queue='Tags')
                else:
                    obj.add_tag(tag)

            if tracker.mail_export():
                if not matches:
                    matches = self.extract_matches(re_matches)
                self.exporters['mail'].export(tracker, obj, matches)

            if tracker.webhook_export():
                if not matches:
                    matches = self.extract_matches(re_matches)
                self.exporters['webhook'].export(tracker, obj, matches)


if __name__ == "__main__":
    module = Tracker_Regex()
    module.run()
