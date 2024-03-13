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

    def __init__(self, queue=True):
        super(CreditCards, self).__init__(queue=queue)

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
        self.re_clean_card = r'[^0-9]'

        # Waiting time in seconds between to message processed
        self.pending_seconds = 10

        # Send module state to logs
        self.logger.info(f"Module {self.module_name} initialized")

    def get_valid_card(self, card):
        clean_card = re.sub(self.re_clean_card, '', card)
        if lib_refine.is_luhn_valid(clean_card):
            return clean_card

    def extract(self, obj_id, content, tag):
        extracted = []
        cards = self.regex_finditer(self.regex, obj_id, content)
        for card in cards:
            start, end, value = card
            if self.get_valid_card(value):
                extracted.append([start, end, value, f'tag:{tag}'])
        return extracted

    def compute(self, message, r_result=False):
        score = message
        item = self.get_obj()
        content = item.get_content()
        all_cards = self.regex_findall(self.regex, item.id, content)

        if len(all_cards) > 0:
            # self.logger.debug(f'All matching {all_cards}')
            creditcard_set = set()
            all_cards = set(all_cards)
            for card in all_cards:
                print(card)
                valid_card = self.get_valid_card(card)
                if valid_card:
                    creditcard_set.add(valid_card)

            # print(creditcard_set)
            to_print = f'CreditCard;{item.get_source()};{item.get_date()};{item.get_basename()};'
            if creditcard_set:
                mess = f'{to_print}Checked {len(creditcard_set)} valid number(s);{self.obj.get_global_id()}'
                print(mess)
                self.redis_logger.warning(mess)

                tag = 'infoleak:automatic-detection="credit-card"'
                self.add_message_to_queue(message=tag, queue='Tags')

                if r_result:
                    return creditcard_set
            else:
                self.redis_logger.info(f'{to_print}CreditCard related;{self.obj.get_global_id()}')


if __name__ == '__main__':
    module = CreditCards()
    module.run()
