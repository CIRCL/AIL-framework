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
from lib.objects.Items import Item
from packages import Term
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

    def __init__(self):
        super(Tracker_Term, self).__init__()

        self.pending_seconds = 5

        self.max_execution_time = self.process.config.getint('Tracker_Term', "max_execution_time")

        # loads tracked words
        self.list_tracked_words = Term.get_tracked_words_list()
        self.last_refresh_word = time.time()
        self.set_tracked_words_list = Term.get_set_tracked_words_list()
        self.last_refresh_set = time.time()

        # Exporter
        self.exporters = {'mail': MailExporterTracker(),
                          'webhook': WebHookExporterTracker()}

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    def compute(self, item_id, item_content=None):
        # refresh Tracked term
        if self.last_refresh_word < Term.get_tracked_term_last_updated_by_type('word'):
            self.list_tracked_words = Term.get_tracked_words_list()
            self.last_refresh_word = time.time()
            self.redis_logger.debug('Tracked word refreshed')
            print('Tracked word refreshed')

        if self.last_refresh_set < Term.get_tracked_term_last_updated_by_type('set'):
            self.set_tracked_words_list = Term.get_set_tracked_words_list()
            self.last_refresh_set = time.time()
            self.redis_logger.debug('Tracked set refreshed')
            print('Tracked set refreshed')

        # Cast message as Item
        item = Item(item_id)
        if not item_content:
            item_content = item.get_content()

        signal.alarm(self.max_execution_time)

        dict_words_freq = None
        try:
            dict_words_freq = Term.get_text_word_frequency(item_content)
        except TimeoutException:
            self.redis_logger.warning(f"{item.get_id()} processing timeout")
        else:
            signal.alarm(0)

        if dict_words_freq:
            # create token statistics
            # for word in dict_words_freq:
            #    Term.create_token_statistics(item_date, word, dict_words_freq[word])

            # check solo words
            # ###### # TODO: check if source needed #######
            for word in self.list_tracked_words:
                if word in dict_words_freq:
                    self.new_term_found(word, 'word', item)

            # check words set
            for elem in self.set_tracked_words_list:
                list_words = elem[0]
                nb_words_threshold = elem[1]
                word_set = elem[2]
                nb_uniq_word = 0

                for word in list_words:
                    if word in dict_words_freq:
                        nb_uniq_word += 1
                if nb_uniq_word >= nb_words_threshold:
                    self.new_term_found(word_set, 'set', item)

    def new_term_found(self, tracker_name, tracker_type, item):
        uuid_list = Tracker.get_tracker_uuid_list(tracker_name, tracker_type)

        item_id = item.get_id()
        item_source = item.get_source()

        for tracker_uuid in uuid_list:
            tracker = Tracker.Tracker(tracker_uuid)

            # Source Filtering
            tracker_sources = tracker.get_sources()
            if tracker_sources and item_source not in tracker_sources:
                continue

            print(f'new tracked term found: {tracker_name} in {item_id}')
            self.redis_logger.warning(f'new tracked term found: {tracker_name} in {item_id}')
            # TODO
            Tracker.add_tracked_item(tracker_uuid, item_id)

            # Tags
            for tag in tracker.get_tags():
                msg = f'{tag};{item_id}'
                self.send_message_to_queue(msg, 'Tags')

            # Mail
            if tracker.mail_export():
                # TODO add matches + custom subjects
                self.exporters['mail'].export(tracker, item)

            # Webhook
            if tracker.webhook_export():
                self.exporters['webhook'].export(tracker, item)


if __name__ == '__main__':
    module = Tracker_Term()
    module.run()
