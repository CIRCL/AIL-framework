#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Tracker_Term Module
===================

"""

##################################
# Import External packages
##################################
import os
import sys
import time
import signal


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib.objects import ail_objects
from lib import Tracker

from exporter.MailExporter import MailExporterTracker
from exporter.WebHookExporter import WebHookExporterTracker

class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException


signal.signal(signal.SIGALRM, timeout_handler)


class Tracker_Term(AbstractModule):
    """
    Tracker_Term module for AIL framework
    """

    def __init__(self, queue=True):
        super(Tracker_Term, self).__init__(queue=queue)

        config_loader = ConfigLoader()

        self.pending_seconds = 5

        self.max_execution_time = config_loader.get_config_int('Tracker_Term', "max_execution_time")

        # loads tracked words
        self.tracked_words = Tracker.get_tracked_words()
        self.last_refresh_word = time.time()
        self.tracked_sets = Tracker.get_tracked_sets()
        self.last_refresh_set = time.time()

        # Exporter
        self.exporters = {'mail': MailExporterTracker(),
                          'webhook': WebHookExporterTracker()}

        self.logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        # refresh Tracked term
        if self.last_refresh_word < Tracker.get_tracker_last_updated_by_type('word'):
            self.tracked_words = Tracker.get_tracked_words()
            self.last_refresh_word = time.time()
            print('Tracked word refreshed')

        if self.last_refresh_set < Tracker.get_tracker_last_updated_by_type('set'):
            self.tracked_sets = Tracker.get_tracked_sets()
            self.last_refresh_set = time.time()
            print('Tracked set refreshed')

        obj = self.get_obj()
        obj_type = obj.get_type()

        # Object Filter
        if obj_type not in self.tracked_words and obj_type not in self.tracked_sets:
            return None

        content = obj.get_content()

        signal.alarm(self.max_execution_time)

        dict_words_freq = None
        try:
            dict_words_freq = Tracker.get_text_word_frequency(content)
        except TimeoutException:
            self.logger.warning(f"{self.obj.get_global_id()} processing timeout")
        else:
            signal.alarm(0)

        if dict_words_freq:

            # check solo words
            for word in self.tracked_words[obj_type]:
                if word in dict_words_freq:
                    self.new_tracker_found(word, 'word', obj)

            # check words set
            for tracked_set in self.tracked_sets[obj_type]:
                nb_uniq_word = 0
                for word in tracked_set['words']:
                    if word in dict_words_freq:
                        nb_uniq_word += 1
                if nb_uniq_word >= tracked_set['nb']:
                    self.new_tracker_found(tracked_set['tracked'], 'set', obj)

    def new_tracker_found(self, tracker_name, tracker_type, obj):  # TODO FILTER
        obj_id = obj.get_id()

        for tracker_uuid in Tracker.get_trackers_by_tracked_obj_type(tracker_type, obj.get_type(), tracker_name):
            tracker = Tracker.Tracker(tracker_uuid)

            # Filter Object
            filters = tracker.get_filters()
            if ail_objects.is_filtered(obj, filters):
                continue

            print(f'new tracked term {tracker_uuid} found: {tracker_name} in {self.obj.get_global_id()}')

            tracker.add(obj.get_type(), obj.get_subtype(), obj_id)

            # Tags
            for tag in tracker.get_tags():
                if obj.get_type() == 'item':
                    self.add_message_to_queue(message=tag, queue='Tags')
                else:
                    obj.add_tag(tag)

            # Mail
            if tracker.mail_export():
                # TODO add matches + custom subjects
                self.exporters['mail'].export(tracker, obj)

            # Webhook
            if tracker.webhook_export():
                self.exporters['webhook'].export(tracker, obj)


if __name__ == '__main__':
    module = Tracker_Term()
    module.run()
    # module.compute('submitted/2023/05/02/submitted_b1e518f1-703b-40f6-8238-d1c22888197e.gz')
