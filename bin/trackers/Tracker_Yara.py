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
from lib.objects import ail_objects
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
        self.rules = Tracker.get_tracked_yara_rules()
        self.last_refresh = time.time()

        self.obj = None

        # Exporter
        self.exporters = {'mail': MailExporterTracker(),
                          'webhook': WebHookExporterTracker()}

        self.logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        # refresh YARA list
        if self.last_refresh < Tracker.get_tracker_last_updated_by_type('yara'):
            self.rules = Tracker.get_tracked_yara_rules()
            self.last_refresh = time.time()
            print('Tracked set refreshed')

        self.obj = self.get_obj()
        obj_type = self.obj.get_type()

        # Object Filter
        if obj_type not in self.rules:
            return None

        content = self.obj.get_content(r_type='bytes')
        if not content:
            return None

        try:
            yara_match = self.rules[obj_type].match(data=content, callback=self.yara_rules_match,
                                                    which_callbacks=yara.CALLBACK_MATCHES, timeout=60)
            if yara_match:
                print(f'{self.obj.get_global_id()}: {yara_match}')
        except yara.TimeoutError:
            print(f'{self.obj.get_id()}: yara scanning timed out')

    def convert_byte_offset_to_string(self, b_content, offset):
        byte_chunk = b_content[:offset + 1]
        try:
            string_chunk = byte_chunk.decode()
            offset = len(string_chunk) - 1
            return offset
        except UnicodeDecodeError:
            return self.convert_byte_offset_to_string(b_content, offset - 1)

    def extract_matches(self, data, limit=500, lines=5):
        matches = []
        content = self.obj.get_content()
        l_content = len(content)
        b_content = content.encode()
        for string_match in data.get('strings'):
            for string_match_instance in string_match.instances:
                start = string_match_instance.offset
                value = string_match_instance.matched_data.decode()
                end = start + string_match_instance.matched_length
                # str
                start = self.convert_byte_offset_to_string(b_content, start)
                end = self.convert_byte_offset_to_string(b_content, end)

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

    def yara_rules_match(self, data):
        tracker_name = data['namespace']
        matches = None
        obj_id = self.obj.get_id()
        for tracker_uuid in Tracker.get_trackers_by_tracked_obj_type('yara', self.obj.get_type(), tracker_name):
            tracker = Tracker.Tracker(tracker_uuid)

            # Filter Object
            filters = tracker.get_filters()
            if ail_objects.is_filtered(self.obj, filters):
                continue

            tracker.add(self.obj.get_type(), self.obj.get_subtype(r_str=True), obj_id)

            # Tags
            for tag in tracker.get_tags():
                if self.obj.get_type() == 'item':
                    self.add_message_to_queue(message=tag, queue='Tags')
                else:
                    self.obj.add_tag(tag)

            # Mails
            if tracker.mail_export():
                if not matches:
                    matches = self.extract_matches(data)
                self.exporters['mail'].export(tracker, self.obj, matches)

            # Webhook
            if tracker.webhook_export():
                if not matches:
                    matches = self.extract_matches(data)
                self.exporters['webhook'].export(tracker, self.obj, matches)

        return yara.CALLBACK_CONTINUE


if __name__ == '__main__':
    module = Tracker_Yara()
    module.run()
