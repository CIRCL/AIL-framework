#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The TermTracker Module
===================

"""
import os
import sys
import time

from Helper import Process
from pubsublogger import publisher

import NotificationHelper

from packages import Paste
from packages import Term

sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'modules'))
import Flask_config

full_item_url = "/showsavedpaste/?paste="

mail_body_template = "AIL Framework,\nNew occurrence for term tracked term: {}\nitem id: {}\nurl: {}{}"

# loads tracked words
list_tracked_words = Term.get_tracked_words_list()
set_tracked_words_list = Term.get_set_tracked_words_list()

def new_term_found(term, term_type, item_id):
    uuid_list = Term.get_term_uuid_list(term)

    for term_uuid in uuid_list:
        Term.add_tracked_item(term_uuid, item_id)

        tags_to_add = Term.get_term_tags(term_uuid)
        for tag in tags_to_add:
            msg = '{};{}'.format(tag, item_id)
            p.populate_set_out(msg, 'Tags')

        mail_to_notify = Term.get_term_mails(term_uuid)
        if mail_to_notify:
            mail_body = mail_body_template.format(term, item_id, full_item_url, item_id)
        for mail in mail_to_notify:
            NotificationHelper.sendEmailNotification(mail, 'Term Tracker', mail_body)


if __name__ == "__main__":

    publisher.port = 6380
    publisher.channel = "Script"
    publisher.info("Script TermTrackerMod started")

    #config_section = 'TermTrackerMod'
    config_section = 'Curve'
    p = Process(config_section)

    full_item_url = p.config.get("Notifications", "ail_domain") + full_item_url

    while True:

        item_id = p.get_from_set()
        item_id = 'submitted/2019/08/02/cc1900ed-6051-473a-ba7a-850a17d0cc02.gz'
        #item_id = 'submitted/2019/08/02/0a52d82d-a89d-4004-9535-8a0bc9c1ce49.gz'

        if message is not None:

            paste = Paste.Paste(item_id)

            dict_words_freq = Term.get_text_word_frequency(paste.get_p_content())

            # check solo words
            for word in list_tracked_words:
                if word in dict_words_freq:
                    new_term_found(word, 'word', item_id)

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
                    new_term_found(word_set, 'set', item_id)

        else:
            time.sleep(5)
