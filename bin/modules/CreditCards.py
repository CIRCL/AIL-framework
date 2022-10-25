#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The CreditCards Module
======================

This module is consuming the Redis-list created by the Categ module.

It apply credit card regexes on item content and warn if a valid card number is found.

"""

##################################
# Import External packages
##################################
import os
import re
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item
from packages import lib_refine

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

    def compute(self, message, r_result=False):
        item_id, score = message.split()
        item = Item(item_id)
        content = item.get_content()
        all_cards = re.findall(self.regex, content)

        if len(all_cards) > 0:
            # self.redis_logger.debug(f'All matching {all_cards}')
            creditcard_set = set([])

            for card in all_cards:
                clean_card = re.sub('[^0-9]', '', card)
                if lib_refine.is_luhn_valid(clean_card):
                    self.redis_logger.debug(f'{clean_card} is valid')
                    creditcard_set.add(clean_card)

            # pprint.pprint(creditcard_set)
            to_print = f'CreditCard;{item.get_source()};{item.get_date()};{item.get_basename()};'
            if len(creditcard_set) > 0:
                self.redis_logger.warning(f'{to_print}Checked {len(creditcard_set)} valid number(s);{item.get_id()}')

                msg = f'infoleak:automatic-detection="credit-card";{item.get_id()}'
                self.send_message_to_queue(msg, 'Tags')

                if r_result:
                    return creditcard_set
            else:
                self.redis_logger.info(f'{to_print}CreditCard related;{item.get_id()}')


if __name__ == '__main__':
    module = CreditCards()
    module.run()
