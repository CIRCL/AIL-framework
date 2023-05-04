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

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, obj_id, obj_type='item', subtype=''):
        # refresh YARA list
        if self.last_refresh < Tracker.get_tracker_last_updated_by_type('yara'):
            self.rules = Tracker.get_tracked_yara_rules()
            self.last_refresh = time.time()
            self.redis_logger.debug('Tracked set refreshed')
            print('Tracked set refreshed')

        self.obj = ail_objects.get_object(obj_type, subtype, obj_id)
        obj_type = self.obj.get_type()

        # Object Filter
        if obj_type not in self.rules:
            return None

        content = self.obj.get_content(r_str=True)

        try:
            yara_match = self.rules[obj_type].match(data=content, callback=self.yara_rules_match,
                                                    which_callbacks=yara.CALLBACK_MATCHES, timeout=60)
            if yara_match:
                self.redis_logger.warning(f'tracker yara: new match {self.obj.get_id()}: {yara_match}')
                print(f'{self.obj.get_id()}: {yara_match}')
        except yara.TimeoutError:
            print(f'{self.obj.get_id()}: yara scanning timed out')
            self.redis_logger.info(f'{self.obj.get_id()}: yara scanning timed out')

    def yara_rules_match(self, data):
        tracker_name = data['namespace']
        obj_id = self.obj.get_id()
        for tracker_uuid in Tracker.get_trackers_by_tracked_obj_type('yara', self.obj.get_type(), tracker_name):
            tracker = Tracker.Tracker(tracker_uuid)

            # Filter Object
            filters = tracker.get_filters()
            if ail_objects.is_filtered(self.obj, filters):
                continue

            if self.obj.get_type() == 'item':
                date = self.obj.get_date()
            else:
                date = None

            tracker.add(self.obj.get_type(), self.obj.get_subtype(r_str=True), obj_id, date=date)

            # Tags
            for tag in tracker.get_tags():
                if self.obj.get_type() == 'item':
                    msg = f'{tag};{obj_id}'
                    self.add_message_to_queue(msg, 'Tags')
                else:
                    self.obj.add_tag(tag)

            # Mails
            if tracker.mail_export():
                # TODO add matches + custom subjects
                self.exporters['mail'].export(tracker, self.obj)

            # Webhook
            if tracker.webhook_export():
                self.exporters['webhook'].export(tracker, self.obj)

        return yara.CALLBACK_CONTINUE


if __name__ == '__main__':
    module = Tracker_Yara()
    module.run()
    # module.compute('archive/gist.github.com/2023/04/13/chipzoller_d8d6d2d737d02ad4fe9d30a897170761.gz')
