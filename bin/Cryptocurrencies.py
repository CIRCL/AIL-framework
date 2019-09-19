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
import Cryptocurrency
import Item


class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)


def search_crytocurrency(item_id, item_content):

    # bitcoin_private_key = re.findall(regex_bitcoin_private_key, content)

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
                    Cryptocurrency.save_cryptocurrency_data(crypto_name, Item.get_item_date(item_id), item_id, address)

            # # TODO: add private key validation
            #if(len(bitcoin_private_key) > 0):
            #    for private_key in bitcoin_private_key:
            #        print('Bitcoin private key found : {}'.format(private_key))
            #        to_print = 'Bitcoin found: {} address and {} private Keys'.format(len(bitcoin_address), len(bitcoin_private_key))
            #        print(to_print)
            #        publisher.warning(to_print)
            #        msg = 'infoleak:automatic-detection="bitcoin-private-key";{}'.format(message)
            #        p.populate_set_out(msg, 'Tags')
            #            to_print = 'Bitcoin;{};{};{};'.format(paste.p_source, paste.p_date,
            #                                            paste.p_name)
            #        publisher.warning('{}Detected {} Bitcoin private key;{}'.format(
            #            to_print, len(bitcoin_private_key),paste.p_rel_path))

            if(is_valid_crypto_addr):
                # valid cryptocurrency found in this item
                is_cryptocurrency_found = True

                # Tag Item
                msg = '{};{}'.format(crypto_dict['tag'], item_id)
                p.populate_set_out(msg, 'Tags')

    if is_cryptocurrency_found:
        # send to duplicate module
        p.populate_set_out(item_id, 'Duplicate')




default_max_execution_time = 30
regex_bitcoin_public_address = r'(?<![a-km-zA-HJ-NP-Z0-9])[13][a-km-zA-HJ-NP-Z0-9]{26,33}(?![a-km-zA-HJ-NP-Z0-9])'

cryptocurrency_dict = {'bitcoin': {
                            'name': 'bitcoin',
                            'regex': regex_bitcoin_public_address,
                            'max_execution_time': default_max_execution_time,
                            'tag': 'infoleak:automatic-detection="bitcoin-address"',
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


    regex_bitcoin_private_key = re.compile(r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}')

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
