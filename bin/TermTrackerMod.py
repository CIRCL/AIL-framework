#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The TermTracker Module
===================

"""

##################################
# Import External packages
##################################
import os
import sys
import time
import signal

##################################
# Import Project packages
##################################
from Helper import Process
from pubsublogger import publisher
from module.abstract_module import AbstractModule
import NotificationHelper
from packages import Item
from packages import Term
from lib import Tracker


class TimeoutException(Exception):
    pass
def timeout_handler(signum, frame):
    raise TimeoutException
signal.signal(signal.SIGALRM, timeout_handler)


class TermTrackerMod(AbstractModule):

    mail_body_template = "AIL Framework,\nNew occurrence for term tracked term: {}\nitem id: {}\nurl: {}{}"

    """
    TermTrackerMod module for AIL framework
    """
    def __init__(self):
        super(TermTrackerMod, self).__init__()

        self.pending_seconds = 5

        self.max_execution_time = self.process.config.getint('TermTrackerMod', "max_execution_time")

        self.full_item_url = self.process.config.get("Notifications", "ail_domain") + "/object/item?id="

        # loads tracked words
        self.list_tracked_words = Term.get_tracked_words_list()
        self.last_refresh_word = time.time()
        self.set_tracked_words_list = Term.get_set_tracked_words_list()
        self.last_refresh_set = time.time()

        # Send module state to logs
        self.redis_logger.info("Module %s initialized"%(self._module_name()))


    def compute(self, item_id):
        # refresh Tracked term
        if self.last_refresh_word < Term.get_tracked_term_last_updated_by_type('word'):
            self.list_tracked_words = Term.get_tracked_words_list()
            self.last_refresh_word = time.time()
            self.redis_logger.debug('Tracked word refreshed')

        if self.last_refresh_set < Term.get_tracked_term_last_updated_by_type('set'):
            self.set_tracked_words_list = Term.get_set_tracked_words_list()
            self.last_refresh_set = time.time()
            self.redis_logger.debug('Tracked set refreshed')

        # Cast message as Item
        item_date = Item.get_item_date(item_id)
        item_content = Item.get_item_content(item_id)

        signal.alarm(self.max_execution_time)

        dict_words_freq = None
        try:
            dict_words_freq = Term.get_text_word_frequency(item_content)
        except TimeoutException:
            self.redis_logger.warning("{0} processing timeout".format(item_id))
        else:
            signal.alarm(0)

        if dict_words_freq:
            # create token statistics
            #for word in dict_words_freq:
            #    Term.create_token_statistics(item_date, word, dict_words_freq[word])

            # check solo words
            for word in self.list_tracked_words:
                if word in dict_words_freq:
                    self.new_term_found(word, 'word', item_id, item_date)

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
                        self.new_term_found(word_set, 'set', item_id, item_date)

    def new_term_found(self, term, term_type, item_id, item_date):
        uuid_list = Term.get_term_uuid_list(term, term_type)
        self.redis_logger.info('new tracked term found: {} in {}'.format(term, item_id))

        for term_uuid in uuid_list:
            Term.add_tracked_item(term_uuid, item_id, item_date)

            tags_to_add = Term.get_term_tags(term_uuid)
            for tag in tags_to_add:
                msg = '{};{}'.format(tag, item_id)
                self.process.populate_set_out(msg, 'Tags')

            mail_to_notify = Term.get_term_mails(term_uuid)
            if mail_to_notify:
                mail_subject = Tracker.get_email_subject(term_uuid)
                mail_body = TermTrackerMod.mail_body_template.format(term, item_id, self.full_item_url, item_id)
            for mail in mail_to_notify:
                self.redis_logger.debug('Send Mail {}'.format(mail_subject))
                NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)


if __name__ == '__main__':

    module = TermTrackerMod()
    module.run()
