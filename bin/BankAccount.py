#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The BankAccount Module
======================

It apply IBAN regexes on item content and warn if above a threshold.

"""

import redis
import time
import datetime
import re
import string
from itertools import chain

from packages import Item
from pubsublogger import publisher

from Helper import Process

import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

_LETTERS_IBAN = chain(enumerate(string.digits + string.ascii_uppercase),
                 enumerate(string.ascii_lowercase, 10))
LETTERS_IBAN = {ord(d): str(i) for i, d in _LETTERS_IBAN}

def iban_number(iban):
    return (iban[4:] + iban[:4]).translate(LETTERS_IBAN)

def is_valid_iban(iban):
    iban_numb = iban_number(iban)
    iban_numb_check = iban_number(iban[:2] + '00' + iban[4:])
    check_digit = '{:0>2}'.format(98 - (int(iban_numb_check) % 97))
    if check_digit == iban[2:4] and int(iban_numb) % 97 == 1:
        # valid iban
        print('valid iban')
        return True
    return False

def check_all_iban(l_iban, obj_id):
    nb_valid_iban = 0
    for iban in l_iban:
        iban = iban[0]+iban[1]+iban[2]
        iban = ''.join(e for e in iban if e.isalnum())
        #iban = iban.upper()
        res = iban_regex_verify.findall(iban)
        date = datetime.datetime.now().strftime("%Y%m")
        if res:
            print('checking '+iban)
            if is_valid_iban(iban):
                print('------')
                nb_valid_iban = nb_valid_iban + 1
                server_statistics.hincrby('iban_by_country:'+date, iban[0:2], 1)

    if(nb_valid_iban > 0):
        to_print = 'Iban;{};{};{};'.format(Item.get_source(obj_id), Item.get_item_date(obj_id), Item.get_basename(obj_id))
        publisher.warning('{}Checked found {} IBAN;{}'.format(
            to_print, nb_valid_iban, obj_id))
        msg = 'infoleak:automatic-detection="iban";{}'.format(obj_id)
        p.populate_set_out(msg, 'Tags')

        #Send to duplicate
        p.populate_set_out(obj_id, 'Duplicate')

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'BankAccount'

    p = Process(config_section)
    max_execution_time = p.config.getint("BankAccount", "max_execution_time")

    # ARDB #
    server_statistics = redis.StrictRedis(
        host=p.config.get("ARDB_Statistics", "host"),
        port=p.config.getint("ARDB_Statistics", "port"),
        db=p.config.getint("ARDB_Statistics", "db"),
        decode_responses=True)

    publisher.info("BankAccount started")

    #iban_regex = re.compile(r'\b[A-Za-z]{2}[0-9]{2}(?:[ ]?[0-9]{4}){4}(?:[ ]?[0-9]{1,2})?\b')
    iban_regex = re.compile(r'\b([A-Za-z]{2}[ \-]?[0-9]{2})(?=(?:[ \-]?[A-Za-z0-9]){9,30})((?:[ \-]?[A-Za-z0-9]{3,5}){2,6})([ \-]?[A-Za-z0-9]{1,3})\b')
    iban_regex_verify = re.compile(r'^([A-Z]{2})([0-9]{2})([A-Z0-9]{9,30})$')


    while True:

        message = p.get_from_set()

        if message is not None:

            obj_id = Item.get_item_id(message)

            content = Item.get_item_content(obj_id)

            signal.alarm(max_execution_time)
            try:
                l_iban = iban_regex.findall(content)
            except TimeoutException:
                 print ("{0} processing timeout".format(obj_id))
                 continue
            else:
                signal.alarm(0)

            if(len(l_iban) > 0):
                check_all_iban(l_iban, obj_id)

        else:
            publisher.debug("Script BankAccount is Idling 10s")
            time.sleep(10)
