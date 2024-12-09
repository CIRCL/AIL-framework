#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Iban Module
================================

This module add tags to an item.

"""

##################################
# Import External packages
##################################
import datetime
import os
import re
import string
import sys
from itertools import chain

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
# from lib.ConfigLoader import ConfigLoader
# from lib import Statistics

class Iban(AbstractModule):
    """
    Iban module for AIL framework
    """

    _LETTERS_IBAN = chain(enumerate(string.digits + string.ascii_uppercase),
                          enumerate(string.ascii_lowercase, 10))
    LETTERS_IBAN = {ord(d): str(i) for i, d in _LETTERS_IBAN}

    def __init__(self, queue=True):
        super(Iban, self).__init__(queue=queue)

        # Waiting time in seconds between to message processed
        self.pending_seconds = 10

        self.regex_timeout = 30
        # iban_regex = re.compile(r'\b[A-Za-z]{2}[0-9]{2}(?:[ ]?[0-9]{4}){4}(?:[ ]?[0-9]{1,2})?\b')
        self.iban_regex = re.compile(r'\b([A-Za-z]{2}[ \-]?[0-9]{2})(?=(?:[ \-]?[A-Za-z0-9]){9,30})((?:[ \-]?[A-Za-z0-9]{3,5}){2,6})([ \-]?[A-Za-z0-9]{1,3})\b')
        self.iban_regex_verify = re.compile(r'^([A-Z]{2})([0-9]{2})([A-Z0-9]{9,30})$')

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def get_iban_number(self, iban):
        return (iban[4:] + iban[:4]).translate(Iban.LETTERS_IBAN)

    def is_valid_iban(self, iban):
        iban_numb = self.get_iban_number(iban)
        iban_numb_check = self.get_iban_number(iban[:2] + '00' + iban[4:])
        check_digit = '{:0>2}'.format(98 - (int(iban_numb_check) % 97))
        if check_digit == iban[2:4] and int(iban_numb) % 97 == 1:
            return True
        return False

    def extract(self, obj, content, tag):
        extracted = []
        ibans = self.regex_finditer(self.iban_regex, obj.get_global_id(), content)
        for iban in ibans:
            start, end, value = iban
            value = ''.join(e for e in value if e.isalnum())
            if self.is_valid_iban(value):
                extracted.append([start, end, value, f'tag:{tag}'])
        return extracted

    def compute(self, message):
        obj = self.get_obj()
        obj_id = obj.get_id()

        ibans = self.regex_findall(self.iban_regex, obj_id, obj.get_content())
        if ibans:
            valid_ibans = set()
            for iban in ibans:
                iban = iban[1:-1].replace("'", "").split(',')
                iban = iban[0]+iban[1]+iban[2]
                iban = ''.join(e for e in iban if e.isalnum())
                if self.regex_findall(self.iban_regex_verify, obj_id, iban):
                    print(f'checking {iban}')
                    if self.is_valid_iban(iban):
                        valid_ibans.add(iban)

            if valid_ibans:
                print(f'{valid_ibans} ibans {self.obj.get_global_id()}')
                # date = datetime.datetime.now().strftime("%Y%m")
                # for iban in valid_ibans:
                #     Statistics.add_module_tld_stats_by_date('iban', date, iban[0:2], 1)

                # Tags
                tag = 'infoleak:automatic-detection="iban"'
                self.add_message_to_queue(message=tag, queue='Tags')


if __name__ == '__main__':

    module = Iban()
    module.run()
