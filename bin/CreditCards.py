#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The CreditCards Module
======================

This module is consuming the Redis-list created by the Categ module.

It apply credit card regexes on paste content and warn if above a threshold.

"""


import pprint
import time
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher
import re
import sys

from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'CreditCards'

    p = Process(config_section)

    # FUNCTIONS #
    publisher.info("CreditCards script started")

    creditcard_regex = "4[0-9]{12}(?:[0-9]{3})?"

    # Source: http://www.richardsramblings.com/regex/credit-card-numbers/
    cards = [
        r'\b4\d{3}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}\b',  # 16-digit VISA, with separators
        r'\b5[1-5]\d{2}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}\b',  # 16 digits MasterCard
        r'\b6(?:011|22(?:(?=[\ \-]?(?:2[6-9]|[3-9]))|[2-8]|9(?=[\ \-]?(?:[01]|2[0-5])))|4[4-9]\d|5\d\d)(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}\b',  # Discover Card
        r'\b35(?:2[89]|[3-8]\d)(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}\b',  # Japan Credit Bureau (JCB)
        r'\b3[47]\d\d(?:[\ \-]?)\d{6}(?:[\ \-]?)\d{5}\b',  # American Express
        r'\b(?:5[0678]\d\d|6304|6390|67\d\d)\d{8,15}\b',  # Maestro
        ]

    regex = re.compile('|'.join(cards))

    while True:
        message = p.get_from_set()
        if message is not None:
            filename, score = message.split()
            paste = Paste.Paste(filename)
            content = paste.get_p_content()
            all_cards = re.findall(regex, content)
            if len(all_cards) > 0:
                print('All matching', all_cards)
                creditcard_set = set([])

                for card in all_cards:
                    clean_card = re.sub('[^0-9]', '', card)
                    clean_card = clean_card
                    if lib_refine.is_luhn_valid(clean_card):
                        print(clean_card, 'is valid')
                        creditcard_set.add(clean_card)

                pprint.pprint(creditcard_set)
                to_print = 'CreditCard;{};{};{};'.format(
                    paste.p_source, paste.p_date, paste.p_name)
                if (len(creditcard_set) > 0):
                    publisher.warning('{}Checked {} valid number(s);{}'.format(
                        to_print, len(creditcard_set), paste.p_rel_path))
                    print('{}Checked {} valid number(s);{}'.format(
                        to_print, len(creditcard_set), paste.p_rel_path))
                    #Send to duplicate
                    p.populate_set_out(filename, 'Duplicate')

                    msg = 'infoleak:automatic-detection="credit-card";{}'.format(filename)
                    p.populate_set_out(msg, 'Tags')
                else:
                    publisher.info('{}CreditCard related;{}'.format(to_print, paste.p_rel_path))
        else:
            publisher.debug("Script creditcard is idling 1m")
            time.sleep(10)
