#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Cryptocurrency Module
============================

It trying to extract Bitcoin address and secret key from paste

    ..seealso:: Paste method (get_regex)

Requirements
------------

*Need running Redis instances. (Redis).

"""

from Helper import Process
from pubsublogger import publisher

import os
import re
import sys
import time
import redis
import signal

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item
import Cryptocurrency


class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)


def search_crytocurrency(item_id, item_content):


    is_cryptocurrency_found = False

    for crypto_name in cryptocurrency_dict:
        crypto_dict = cryptocurrency_dict[crypto_name]

        signal.alarm(crypto_dict['max_execution_time'])
        try:
            crypto_addr = re.findall(crypto_dict['regex'], item_content)
        except TimeoutException:
            crypto_addr = []
            p.incr_module_timeout_statistic() # add encoder type
            print ("{0} processing timeout".format(item_id))
            continue
        else:
            signal.alarm(0)

        if crypto_addr:
            is_valid_crypto_addr = False
            # validate cryptocurrency address
            for address in crypto_addr:
                if(Cryptocurrency.verify_cryptocurrency_address(crypto_name, address)):
                    is_valid_crypto_addr = True
                    print('{} address found : {}'.format(crypto_name, address))
                    # build bitcoin correlation
                    Cryptocurrency.cryptocurrency.save_item_correlation(crypto_name, address, item_id, Item.get_item_date(item_id))

            # At least one valid cryptocurrency address was found
            if(is_valid_crypto_addr):
                # valid cryptocurrency found in this item
                is_cryptocurrency_found = True

                # Tag Item
                msg = '{};{}'.format(crypto_dict['tag'], item_id)
                p.populate_set_out(msg, 'Tags')

                # search cryptocurrency private key
                if crypto_dict.get('private_key'):
                    signal.alarm(crypto_dict['private_key']['max_execution_time'])
                    try:
                        addr_private_key = re.findall(crypto_dict['private_key']['regex'], item_content)
                    except TimeoutException:
                        addr_private_key = []
                        p.incr_module_timeout_statistic() # add encoder type
                        print ("{0} processing timeout".format(item_id))
                        continue
                    else:
                        signal.alarm(0)

                    if addr_private_key:
                        # Tag Item
                        msg = '{};{}'.format(crypto_dict['private_key']['tag'], item_id)
                        p.populate_set_out(msg, 'Tags')

                        # debug
                        print(addr_private_key)
                        to_print = '{} found: {} address and {} private Keys'.format(crypto_name, len(crypto_addr), len(addr_private_key))
                        print(to_print)
                        publisher.warning(to_print)

                        to_print = 'Cryptocurrency;{};{};{};'.format(Item.get_source(item_id), Item.get_item_date(item_id), Item.get_item_basename(item_id))
                        publisher.warning('{}Detected {} {} private key;{}'.format(
                            to_print, len(addr_private_key), crypto_name, item_id))


    if is_cryptocurrency_found:
        # send to duplicate module
        p.populate_set_out(item_id, 'Duplicate')




default_max_execution_time = 30

cryptocurrency_dict = {
    'bitcoin': {
                    'name': 'bitcoin',      # e.g. 1NbEPRwbBZrFDsx1QW19iDs8jQLevzzcms
                    'regex': r'\b(?<![+/=])[13][A-Za-z0-9]{26,33}(?![+/=])\b',
                    'max_execution_time': default_max_execution_time,
                    'tag': 'infoleak:automatic-detection="bitcoin-address"',
                    'private_key': {
                        'regex': r'\b(?<![+/=])[5KL][1-9A-HJ-NP-Za-km-z]{50,51}(?![+/=])\b',
                        'max_execution_time': default_max_execution_time,
                        'tag': 'infoleak:automatic-detection="bitcoin-private-key"',
                    },
    },
    'ethereum': {
                    'name': 'ethereum',     # e.g. 0x8466b50B53c521d0B4B163d186596F94fB8466f1
                    'regex': r'\b(?<![+/=])0x[A-Za-z0-9]{40}(?![+/=])\b',
                    'max_execution_time': default_max_execution_time,
                    'tag': 'infoleak:automatic-detection="ethereum-address"',
    },
    'bitcoin-cash': {
                    'name': 'bitcoin-cash', # e.g. bitcoincash:pp8skudq3x5hzw8ew7vzsw8tn4k8wxsqsv0lt0mf3g
                    'regex': r'bitcoincash:[a-za0-9]{42}(?![+/=])\b',
                    'max_execution_time': default_max_execution_time,
                    'tag': 'infoleak:automatic-detection="bitcoin-cash-address"',
    },
    'litecoin': {
                    'name': 'litecoin',     # e.g. MV5rN5EcX1imDS2gEh5jPJXeiW5QN8YrK3
                    'regex': r'\b(?<![+/=])[ML][A-Za-z0-9]{33}(?![+/=])\b',
                    'max_execution_time': default_max_execution_time,
                    'tag': 'infoleak:automatic-detection="litecoin-address"',
    },
    'monero': {
                    'name': 'monero',       # e.g. 47JLdZWteNPFQPaGGNsqLBAU3qmTcWbRda4yJvaPTCB8JbY18MNrcmfCcxrfDF61Dm7pJc4bHbBW57URjwTWzTRH2RfsUB4
                    'regex': r'\b(?<![+/=()])4[A-Za-z0-9]{94}(?![+/=()])\b',
                    'max_execution_time': default_max_execution_time,
                    'tag': 'infoleak:automatic-detection="monero-address"',
    },
    'zcash': {
                    'name': 'zcash',        # e.g. t1WvvNmFuKkUipcoEADNFvqamRrBec8rpUn
                    'regex': r'\b(?<![+/=()])t[12][A-Za-z0-9]{33}(?![+/=()])\b',
                    'max_execution_time': default_max_execution_time,
                    'tag': 'infoleak:automatic-detection="zcash-address"',
    },
    'dash': {
                    'name': 'dash',         # e.g. XmNfXq2kDmrNBTiDTofohRemwGur1WmgTT
                    'regex': r'\b(?<![+/=])X[A-Za-z0-9]{33}(?![+/=])\b',
                    'max_execution_time': default_max_execution_time,
                    'tag': 'infoleak:automatic-detection="dash-address"',
    }
}


if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Bitcoin'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Run Cryptocurrency module ")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        item_id = p.get_from_set()
        if item_id is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        item_content = Item.get_item_content(item_id)
        search_crytocurrency(item_id, item_content)
