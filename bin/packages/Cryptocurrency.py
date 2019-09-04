#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import redis

from hashlib import sha256

import Flask_config
from Correlation import Correlation

r_serv_metadata = Flask_config.r_serv_metadata

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

cryptocurrency = Correlation('cryptocurrency')

def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return n.to_bytes(length, 'big')

def check_bitcoin_address(bc):
    try:
        bcbytes = decode_base58(bc, 25)
        return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]
    except Exception:
        return False

def verify_cryptocurrency_address(cryptocurrency_type, cryptocurrency_address):
    if cryptocurrency_type == 'bitcoin':
        return check_bitcoin_address(cryptocurrency_address)
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
