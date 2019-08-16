#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import redis

from hashlib import sha256

import Flask_config
from Correlation import Correlation

r_serv_metadata = Flask_config.r_serv_metadata

pgpdump = Correlation('pgpdump')


def get_pgp(request_dict, pgp_type):
    # basic verification
    res = pgpdump.verify_correlation_field_request(request_dict, pgp_type)
    if res:
        return res
    # cerify address
    field_name = request_dict.get(pgp_type)

    return pgpdump.get_correlation(request_dict, pgp_type, field_name)
