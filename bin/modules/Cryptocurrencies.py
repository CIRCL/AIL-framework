#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Cryptocurrency Module
============================

It trying to extract cryptocurrencies address and secret key from items

    ..seealso:: Paste method (get_regex)

Requirements
------------

*Need running Redis instances. (Redis).

"""

##################################
# Import External packages
##################################
import os
import sys
from abc import ABC

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.CryptoCurrencies import CryptoCurrency

##################################
##################################
default_max_execution_time = 30
CURRENCIES = {
    'bitcoin': {
        'name': 'bitcoin',  # e.g. 1NbEPRwbBZrFDsx1QW19iDs8jQLevzzcms
        'regex': r'\b(?<![+/=])[13][A-Za-z0-9]{26,33}(?![+/=])\b',
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="bitcoin-address"',
        'private_key': {
            'regex': r'\b(?<![+/=])[5KL][1-9A-HJ-NP-Za-km-z]{50,51}(?![+/=])\b',
            'max_execution_time': default_max_execution_time,
            'tag': 'infoleak:automatic-detection="bitcoin-private-key"',
        },
    },
    'bitcoin-bech32': {
        'name': 'bitcoin',  # e.g. bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq
        'regex': r'\bbc(?:0(?:[ac-hj-np-z02-9]{39}|[ac-hj-np-z02-9]{59})|1[ac-hj-np-z02-9]{8,87})\b',
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="bitcoin-address"',
        'private_key': {
            'regex': r'\b(?<![+/=])[5KL][1-9A-HJ-NP-Za-km-z]{50,51}(?![+/=])\b',
            'max_execution_time': default_max_execution_time,
            'tag': 'infoleak:automatic-detection="bitcoin-private-key"',
        },
    },
    'ethereum': {
        'name': 'ethereum',  # e.g. 0x8466b50B53c521d0B4B163d186596F94fB8466f1
        'regex': r'\b(?<![+/=])0x[A-Za-z0-9]{40}(?![+/=])\b',
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="ethereum-address"',
    },
    'bitcoin-cash': {
        'name': 'bitcoin-cash',  # e.g. bitcoincash:pp8skudq3x5hzw8ew7vzsw8tn4k8wxsqsv0lt0mf3g
        'regex': r'bitcoincash:[a-za0-9]{42}(?![+/=])\b',
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="bitcoin-cash-address"',
    },
    'litecoin': {
        'name': 'litecoin',  # e.g. MV5rN5EcX1imDS2gEh5jPJXeiW5QN8YrK3
        'regex': r'\b(?<![+/=])[ML][A-Za-z0-9]{33}(?![+/=])\b',
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="litecoin-address"',
    },
    'monero': {
        'name': 'monero',
        # e.g. 47JLdZWteNPFQPaGGNsqLBAU3qmTcWbRda4yJvaPTCB8JbY18MNrcmfCcxrfDF61Dm7pJc4bHbBW57URjwTWzTRH2RfsUB4
        'regex': r'\b(?<![+/=()])4[A-Za-z0-9]{94}(?![+/=()])\b',
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="monero-address"',
    },
    'zcash': {
        'name': 'zcash',  # e.g. t1WvvNmFuKkUipcoEADNFvqamRrBec8rpUn
        'regex': r'\b(?<![+/=()])t[12][A-Za-z0-9]{33}(?![+/=()])\b',
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="zcash-address"',
    },
    'dash': {
        'name': 'dash',  # e.g. XmNfXq2kDmrNBTiDTofohRemwGur1WmgTT
        'regex': r'\b(?<![+/=])X[A-Za-z0-9]{33}(?![+/=])\b',
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dash-address"',
    },
    'tron': {
            'name': 'tron',  # e.g. TYdds9VLDjUshf9tbsXSfGUZNzJSbbBeat
            'regex': r'\b(?<![+/=])T[0-9a-zA-Z]{33}(?![+/=])\b',
            'max_execution_time': default_max_execution_time,
            'tag': 'infoleak:automatic-detection="tron-address"',
    },
    'ripple': {
            'name': 'ripple',  # e.g.
            'regex': r'\b(?<![+/=])r[0-9a-zA-Z]{24,34}(?![+/=])\b',
            'max_execution_time': default_max_execution_time,
            'tag': 'infoleak:automatic-detection="ripple-address"',
    },
}
##################################
##################################

class Cryptocurrencies(AbstractModule, ABC):
    """
    Cve module for AIL framework
    """

    def __init__(self):
        super(Cryptocurrencies, self).__init__()

        # regexs

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        item = self.get_obj()
        item_id = item.get_id()
        date = item.get_date()
        content = item.get_content()

        for curr in CURRENCIES:
            currency = CURRENCIES[curr]
            addresses = self.regex_findall(currency['regex'], item_id, content)
            if addresses:
                is_valid_address = False
                for address in addresses:
                    crypto = CryptoCurrency(address, currency['name'])
                    # Verify Address
                    if crypto.is_valid_address():
                        # print(address)
                        is_valid_address = True
                        crypto.add(date, item)

                # Check private key
                if is_valid_address:
                    msg = f'{currency["tag"]}'
                    self.add_message_to_queue(message=msg, queue='Tags')

                    if currency.get('private_key'):
                        private_keys = self.regex_findall(currency['private_key']['regex'], item_id, content)
                        if private_keys:
                            msg = f'{currency["private_key"]["tag"]}'
                            self.add_message_to_queue(message=msg, queue='Tags')

                            # debug
                            print(private_keys)
                    else:
                        private_keys = []

                    print(f"{currency['name']} found: {len(addresses)} address and {len(private_keys)} private Keys {self.obj.get_global_id()}")


if __name__ == '__main__':
    module = Cryptocurrencies()
    module.run()
