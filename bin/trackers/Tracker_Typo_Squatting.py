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
from lib.objects import ail_objects
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
        self.tracked_typosquattings = Tracker.get_tracked_typosquatting()
        self.last_refresh_typosquatting = time.time()

        # Exporter
        self.exporters = {'mail': MailExporterTracker(),
                          'webhook': WebHookExporterTracker()}

        self.logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        # refresh Tracked typo
        if self.last_refresh_typosquatting < Tracker.get_tracker_last_updated_by_type('typosquatting'):
            self.tracked_typosquattings = Tracker.get_tracked_typosquatting()
            self.last_refresh_typosquatting = time.time()
            print('Tracked typosquatting refreshed')

        host = message
        obj = self.get_obj()
        obj_type = obj.get_type()

        # Object Filter
        if obj_type not in self.tracked_typosquattings:
            return None

        for typo in self.tracked_typosquattings[obj_type]:
            if host in typo['domains']:
                self.new_tracker_found(typo['tracked'], 'typosquatting', obj)

    def new_tracker_found(self, tracked, tracker_type, obj):
        obj_id = obj.get_id()
        for tracker_uuid in Tracker.get_trackers_by_tracked_obj_type(tracker_type, obj.get_type(), tracked):
            tracker = Tracker.Tracker(tracker_uuid)

            # Filter Object
            filters = tracker.get_filters()
            if ail_objects.is_filtered(obj, filters):
                continue

            print(f'new tracked typosquatting found: {tracked} in {self.obj.get_global_id()}')

            tracker.add(obj.get_type(), obj.get_subtype(r_str=True), obj_id)

            # Tags
            for tag in tracker.get_tags():
                if obj.get_type() == 'item':
                    msg = f'{tag};{obj_id}'
                    self.add_message_to_queue(message=tag, queue='Tags')
                else:
                    obj.add_tag(tag)

            if tracker.mail_export():
                self.exporters['mail'].export(tracker, obj)

            if tracker.webhook_export():
                self.exporters['webhook'].export(tracker, obj)


if __name__ == '__main__':
    module = Tracker_Typo_Squatting()
    module.run()
    # module.compute('g00gle.com tests/2020/01/01/test.gz')
