#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

from hashlib import sha256

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import correlation

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

cryptocurrency = correlation.Correlation('cryptocurrency', ['bitcoin', 'ethereum', 'bitcoin-cash', 'litecoin', 'monero', 'zcash', 'dash'])

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


def get_cryptocurrency_symbol(crypto_type):
    if crypto_type=='bitcoin':
        return 'BTC'
    elif crypto_type=='ethereum':
        return 'ETH'
    elif crypto_type=='bitcoin-cash':
        return 'BCH'
    elif crypto_type=='litecoin':
        return 'LTC'
    elif crypto_type=='monero':
        return 'XMR'
    elif crypto_type=='zcash':
        return 'ZEC'
    elif crypto_type=='dash':
        return 'DASH'
    return None

def get_cryptocurrency_type(crypto_symbol):
    if crypto_type=='BTC':
        return 'bitcoin'
    elif crypto_type=='ETH':
        return 'ethereum'
    elif crypto_type=='BCH':
        return 'bitcoin-cash'
    elif crypto_type=='LTC':
        return 'litecoin'
    elif crypto_type=='XMR':
        return 'monero'
    elif crypto_type=='ZEC':
        return 'zcash'
    elif crypto_type=='DASH':
        return 'dash'
    return None
