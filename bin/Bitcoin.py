#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Bitcoin Module
============================

It trying to extract Bitcoin address and secret key from paste

    ..seealso:: Paste method (get_regex)

Requirements
------------

*Need running Redis instances. (Redis).

"""

from packages import Paste
from Helper import Process
from pubsublogger import publisher

import re
import time
import redis

from hashlib import sha256


#### thank http://rosettacode.org/wiki/Bitcoin/address_validation#Python for this 2 functions

def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return n.to_bytes(length, 'big')

def check_bc(bc):
    try:
        bcbytes = decode_base58(bc, 25)
        return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]
    except Exception:
        return False
########################################################

def search_key(content, message, paste):
    bitcoin_address = re.findall(regex_bitcoin_public_address, content)
    bitcoin_private_key = re.findall(regex_bitcoin_private_key, content)
    date = str(paste._get_p_date())
    validate_address = False
    key = False
    if(len(bitcoin_address) >0):
        #print(message)
        for address in bitcoin_address:
            if(check_bc(address)):
                validate_address = True
                print('Bitcoin address found : {}'.format(address))
                if(len(bitcoin_private_key) > 0):
                    for private_key in bitcoin_private_key:
                        print('Bitcoin private key found : {}'.format(private_key))
                        key = True
                # build bitcoin correlation
                save_cryptocurrency_data('bitcoin', date, message, address)

        if(validate_address):
            p.populate_set_out(message, 'Duplicate')
            to_print = 'Bitcoin found: {} address and {} private Keys'.format(len(bitcoin_address), len(bitcoin_private_key))
            print(to_print)
            publisher.warning(to_print)

            msg = 'infoleak:automatic-detection="bitcoin-address";{}'.format(message)
            p.populate_set_out(msg, 'Tags')

            if(key):
                msg = 'infoleak:automatic-detection="bitcoin-private-key";{}'.format(message)
                p.populate_set_out(msg, 'Tags')

                to_print = 'Bitcoin;{};{};{};'.format(paste.p_source, paste.p_date,
                                                    paste.p_name)
                publisher.warning('{}Detected {} Bitcoin private key;{}'.format(
                    to_print, len(bitcoin_private_key),paste.p_rel_path))

def save_cryptocurrency_data(cryptocurrency_name, date, item_path, cryptocurrency_address):
    # create basic medata
    if not serv_metadata.exists('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address)):
        serv_metadata.hset('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'first_seen', date)
        serv_metadata.hset('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'last_seen', date)
    else:
        last_seen = serv_metadata.hget('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'last_seen')
        if not last_seen:
            serv_metadata.hset('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'last_seen', date)
        else:
            if int(last_seen) < int(date):
                serv_metadata.hset('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'last_seen', date)

    # global set
    serv_metadata.sadd('set_cryptocurrency_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), item_path)

    # daily
    serv_metadata.hincrby('cryptocurrency:{}:{}'.format(cryptocurrency_name, date), cryptocurrency_address, 1)

    # all type
    serv_metadata.zincrby('cryptocurrency_all:{}'.format(cryptocurrency_name), cryptocurrency_address, 1)

    # item_metadata
    serv_metadata.sadd('item_cryptocurrency_{}:{}'.format(cryptocurrency_name, item_path), cryptocurrency_address)

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Bitcoin'

    # Setup the I/O queues
    p = Process(config_section)

    serv_metadata = redis.StrictRedis(
        host=p.config.get("ARDB_Metadata", "host"),
        port=p.config.getint("ARDB_Metadata", "port"),
        db=p.config.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    # Sent to the logging a description of the module
    publisher.info("Run Keys module ")

    digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

    regex_bitcoin_public_address = re.compile(r'(?<![a-km-zA-HJ-NP-Z0-9])[13][a-km-zA-HJ-NP-Z0-9]{26,33}(?![a-km-zA-HJ-NP-Z0-9])')
    regex_bitcoin_private_key = re.compile(r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}')

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        paste = Paste.Paste(message)
        content = paste.get_p_content()
        search_key(content, message, paste)
