#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The CreditCards Module
======================

This module is consuming the Redis-list created by the Categ module.

It apply credit card regexes on paste content and warn if above a threshold.

"""

##################################
# Import External packages
##################################
import pprint
import time
from pubsublogger import publisher
import re
import sys

##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from packages import Paste
from packages import lib_refine
from Helper import Process


class CreditCards(AbstractModule):
    """
    CreditCards module for AIL framework
    """

    def __init__(self):
        super(CreditCards, self).__init__()

        # Source: http://www.richardsramblings.com/regex/credit-card-numbers/
        cards = [
            r'\b4\d{3}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}\b',  # 16-digit VISA, with separators
            r'\b5[1-5]\d{2}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}\b',  # 16 digits MasterCard
            r'\b6(?:011|22(?:(?=[\ \-]?(?:2[6-9]|[3-9]))|[2-8]|9(?=[\ \-]?(?:[01]|2[0-5])))|4[4-9]\d|5\d\d)(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}\b',  # Discover Card
            r'\b35(?:2[89]|[3-8]\d)(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}(?:[\ \-]?)\d{4}\b',  # Japan Credit Bureau (JCB)
            r'\b3[47]\d\d(?:[\ \-]?)\d{6}(?:[\ \-]?)\d{5}\b',  # American Express
            r'\b(?:5[0678]\d\d|6304|6390|67\d\d)\d{8,15}\b',  # Maestro
            ]

        self.regex = re.compile('|'.join(cards))

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 10

        # Send module state to logs
        self.redis_logger.info(f"Module {self.module_name} initialized")


    def compute(self, message):
        filename, score = message.split()
        paste = Paste.Paste(filename)
        content = paste.get_p_content()
        all_cards = re.findall(self.regex, content)

        if len(all_cards) > 0:
            self.redis_logger.debug('All matching', all_cards)
            creditcard_set = set([])

            for card in all_cards:
                clean_card = re.sub('[^0-9]', '', card)
                # TODO purpose of this assignation ?
                clean_card = clean_card
                if lib_refine.is_luhn_valid(clean_card):
                    self.redis_logger.debug(clean_card, 'is valid')
                    creditcard_set.add(clean_card)

            pprint.pprint(creditcard_set)
            to_print = f'CreditCard;{paste.p_source};{paste.p_date};{paste.p_name};'

            if (len(creditcard_set) > 0):
                self.redis_logger.warning(f'{to_print}Checked {len(creditcard_set)} valid number(s);{paste.p_rel_path}')

                #Send to duplicate
                self.process.populate_set_out(filename, 'Duplicate')

                msg = f'infoleak:automatic-detection="credit-card";{filename}'
                self.process.populate_set_out(msg, 'Tags')
            else:
                self.redis_logger.info(f'{to_print}CreditCard related;{paste.p_rel_path}')

if __name__ == '__main__':
    
    module = CreditCards()
    module.run()
