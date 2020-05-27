#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Correlation

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

pgp = Correlation.Correlation('pgpdump', ['key', 'mail', 'name'])

def get_pgp(request_dict, pgp_type):
    # basic verification
    res = pgp.verify_correlation_field_request(request_dict, pgp_type)
    if res:
        return res
    # cerify address
    field_name = request_dict.get(pgp_type)

    return pgp.get_correlation(request_dict, pgp_type, field_name)
