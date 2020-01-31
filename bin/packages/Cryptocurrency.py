#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

from hashlib import sha256

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
from Correlation import Correlation
import Item

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


class Cryptocurrency(Correlation):
    def __init__(self):
        super().__init__('cryptocurrency', ['bitcoin', 'ethereum', 'bitcoin-cash', 'litecoin', 'monero', 'zcash', 'dash'])

cryptocurrency = Cryptocurrency()

# http://rosettacode.org/wiki/Bitcoin/address_validation#Python
def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return n.to_bytes(length, 'big')

# http://rosettacode.org/wiki/Bitcoin/address_validation#Python
def check_base58_address(bc):
    try:
        bcbytes = decode_base58(bc, 25)
        return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]
    except Exception:
        return False

def verify_cryptocurrency_address(cryptocurrency_type, cryptocurrency_address):
    if cryptocurrency_type in ('bitcoin', 'litecoin', 'dash'):
        return check_base58_address(cryptocurrency_address)
    else:
        return True


def get_cryptocurrency(request_dict, cryptocurrency_type):
    # basic verification
    res = cryptocurrency.verify_correlation_field_request(request_dict, cryptocurrency_type)
    if res:
        return res
    # cerify address
    field_name = request_dict.get(cryptocurrency_type)
    if not verify_cryptocurrency_address(cryptocurrency_type, field_name):
        return ( {'status': 'error', 'reason': 'Invalid Cryptocurrency address'}, 400 )

    return cryptocurrency.get_correlation(request_dict, cryptocurrency_type, field_name)

# # TODO: refractor/move me in Correlation
def save_cryptocurrency_data(cryptocurrency_name, date, item_path, cryptocurrency_address):
    # create basic medata
    if not r_serv_metadata.exists('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address)):
        r_serv_metadata.hset('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'first_seen', date)
        r_serv_metadata.hset('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'last_seen', date)
    else:
        last_seen = r_serv_metadata.hget('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'last_seen')
        if not last_seen:
            r_serv_metadata.hset('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'last_seen', date)
        else:
            if int(last_seen) < int(date):
                r_serv_metadata.hset('cryptocurrency_metadata_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), 'last_seen', date)

    ## global set
    # item
    r_serv_metadata.sadd('set_cryptocurrency_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), item_path)

    # daily
    r_serv_metadata.hincrby('cryptocurrency:{}:{}'.format(cryptocurrency_name, date), cryptocurrency_address, 1)

    # all type
    r_serv_metadata.zincrby('cryptocurrency_all:{}'.format(cryptocurrency_name), cryptocurrency_address, 1)

    ## object_metadata
    # item
    r_serv_metadata.sadd('item_cryptocurrency_{}:{}'.format(cryptocurrency_name, item_path), cryptocurrency_address)

    # domain
    if Item.is_crawled(item_path): # # TODO:  use save_domain_correlation
        domain = Item.get_item_domain(item_path)
        r_serv_metadata.sadd('domain_cryptocurrency_{}:{}'.format(cryptocurrency_name, domain), cryptocurrency_address)
        r_serv_metadata.sadd('set_domain_cryptocurrency_{}:{}'.format(cryptocurrency_name, cryptocurrency_address), domain)

def get_cryptocurrency_symbol(crypto_type):
    if type=='bitcoin':
        return 'BTC'
    else:
        return ''
