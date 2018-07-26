#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The ApiKey Module
======================

This module is consuming the Redis-list created by the Categ module.

It apply API_key regexes on paste content and warn if above a threshold.

"""

import redis
import time
import re
import string

from packages import Paste
from pubsublogger import publisher

from Helper import Process

import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

LETTERS_IBAN = {ord(d): str(i) for i, d in enumerate(string.digits + string.ascii_uppercase)}

def iban_number(iban):
    return (iban[4:] + iban[:4].translate(LETTERS_IBAN))

def is_valid_iban(iban):
    iban = iban.replace(' ', '')
    iban_numb = iban_number(iban)
    iban_numb_check = iban_number(iban[:2] + '00' + iban[4:])
    check_digit = '{:0>2}'.format(98 - (int(iban_numb_check) % 97))
    if check_digit == iban[2:4] and int(iban_numb) % 97 == 1:
        # valid iban
        print('valid iban')
        print(iban)
        return True
    return False

def check_all_iban(l_iban, paste, filename):
    nb_valid_iban = 0
    for iban in l_iban:
        print('checking '+iban)
        if is_valid_iban(iban):
            print('------')
            nb_valid_iban = nb_valid_iban + 1
    if(nb_valid_iban > 0):
        to_print = 'Iban;{};{};{};'.format(paste.p_source, paste.p_date, paste.p_name)
        publisher.warning('{}Checked found {} IBAN;{}'.format(
            to_print, nb_valid_iban, paste.p_path))
        msg = 'infoleak:automatic-detection="iban";{}'.format(filename)
        p.populate_set_out(msg, 'Tags')

        #Send to duplicate
        p.populate_set_out(filename, 'Duplicate')

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'BankAccount'

    p = Process(config_section)
    max_execution_time = p.config.getint("BankAccount", "max_execution_time")

    publisher.info("BankAccount started")

    message = p.get_from_set()

    iban_regex = re.compile(r'\b[A-Za-z]{2}[0-9]{2}(?:[ ]?[0-9]{4}){4}(?:[ ]?[0-9]{1,2})?\b')

    while True:

        message = p.get_from_set()

        if message is not None:

            filename = message
            paste = Paste.Paste(filename)
            content = paste.get_p_content()

            signal.alarm(max_execution_time)
            try:
                l_iban = iban_regex.findall(content)
            except TimeoutException:
                 print ("{0} processing timeout".format(paste.p_path))
                 continue
            else:
                signal.alarm(0)

            if(len(l_iban) > 0):
                check_all_iban(l_iban, paste, filename)

        else:
            publisher.debug("Script ApiKey is Idling 10s")
            time.sleep(10)
