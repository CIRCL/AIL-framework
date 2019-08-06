#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The TermTracker Module
===================

"""
import os
import sys
import time

from packages import Paste
from packages import Term

sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'modules'))
import Flask_config

r_serv_term = Flask_config.r_serv_term

# loads tracked words
list_tracked_words = Term.get_tracked_words_list()
set_tracked_words_list = Term.get_set_tracked_words_list()

def new_term_found(term, term_type):
    uuid_list = get_term_uuid_list()
    email_notification = []
    tags = []

    for term_uuid in uuid_list:
        pass


if __name__ == "__main__":

    item_id = 'submitted/2019/08/02/cc1900ed-6051-473a-ba7a-850a17d0cc02.gz'
    #item_id = 'submitted/2019/08/02/0a52d82d-a89d-4004-9535-8a0bc9c1ce49.gz'
    paste = Paste.Paste(item_id)
    res = Term.parse_tracked_term_to_add('test zorro meroio apple weert', 'word')

    '''
    dict_words_freq = Term.get_text_word_frequency(paste.get_p_content())

    # check solo words
    for word in list_tracked_words:
        if word in dict_words_freq:
            pass
            # tag + get uuids ...

    # check words set
    for list_words, nb_words_threshold in set_tracked_words_list:
        nb_uniq_word = 0
        for word in list_words:
            if word in dict_words_freq:
                nb_uniq_word += 1
        if nb_uniq_word > nb_words_threshold:
            # tag + get uuid
            pass
    '''
