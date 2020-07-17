#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The TermTracker Module
===================

"""
import os
import sys
import time
import signal

from Helper import Process
from pubsublogger import publisher

import NotificationHelper

from packages import Item
from packages import Term

from lib import Tracker

full_item_url = "/showsavedpaste/?paste="

mail_body_template = "AIL Framework,\nNew occurrence for term tracked term: {}\nitem id: {}\nurl: {}{}"

# loads tracked words
list_tracked_words = Term.get_tracked_words_list()
last_refresh_word = time.time()
set_tracked_words_list = Term.get_set_tracked_words_list()
last_refresh_set = time.time()

class TimeoutException(Exception):
    pass
def timeout_handler(signum, frame):
    raise TimeoutException
signal.signal(signal.SIGALRM, timeout_handler)

def new_term_found(term, term_type, item_id, item_date):
    uuid_list = Term.get_term_uuid_list(term, term_type)
    print('new tracked term found: {} in {}'.format(term, item_id))

    for term_uuid in uuid_list:
        Term.add_tracked_item(term_uuid, item_id, item_date)

        tags_to_add = Term.get_term_tags(term_uuid)
        for tag in tags_to_add:
            msg = '{};{}'.format(tag, item_id)
            p.populate_set_out(msg, 'Tags')

        mail_to_notify = Term.get_term_mails(term_uuid)
        if mail_to_notify:
            mail_subject = Tracker.get_email_subject(term_uuid)
            mail_body = mail_body_template.format(term, item_id, full_item_url, item_id)
        for mail in mail_to_notify:
            NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)


if __name__ == "__main__":

    publisher.port = 6380
    publisher.channel = "Script"
    publisher.info("Script TermTrackerMod started")

    config_section = 'TermTrackerMod'
    p = Process(config_section)
    max_execution_time = p.config.getint(config_section, "max_execution_time")

    full_item_url = p.config.get("Notifications", "ail_domain") + full_item_url

    while True:

        item_id = p.get_from_set()

        if item_id is not None:

            item_date = Item.get_item_date(item_id)
            item_content = Item.get_item_content(item_id)

            signal.alarm(max_execution_time)
            try:
                dict_words_freq = Term.get_text_word_frequency(item_content)
            except TimeoutException:
                print ("{0} processing timeout".format(paste.p_rel_path))
                continue
            else:
                signal.alarm(0)

            # create token statistics
            #for word in dict_words_freq:
            #    Term.create_token_statistics(item_date, word, dict_words_freq[word])

            # check solo words
            for word in list_tracked_words:
                if word in dict_words_freq:
                    new_term_found(word, 'word', item_id, item_date)

            # check words set
            for elem in set_tracked_words_list:
                list_words = elem[0]
                nb_words_threshold = elem[1]
                word_set = elem[2]
                nb_uniq_word = 0

                for word in list_words:
                    if word in dict_words_freq:
                        nb_uniq_word += 1
                if nb_uniq_word >= nb_words_threshold:
                    new_term_found(word_set, 'set', item_id, item_date)

        else:
            time.sleep(5)


        # refresh Tracked term
        if last_refresh_word < Term.get_tracked_term_last_updated_by_type('word'):
            list_tracked_words = Term.get_tracked_words_list()
            last_refresh_word = time.time()
            print('Tracked word refreshed')

        if last_refresh_set < Term.get_tracked_term_last_updated_by_type('set'):
            set_tracked_words_list = Term.get_set_tracked_words_list()
            last_refresh_set = time.time()
            print('Tracked set refreshed')
