#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import d4_pyclient

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None

def get_ail_uuid():
    return r_serv_db.get('ail:uuid')

def get_d4_client_config_dir():
    return os.path.join(os.environ['AIL_HOME'], 'configs', 'd4client_passiveDNS_conf')

def create_d4_config_file(filename, content):
    if not os.path.isfile(filename):
        with open(filename, 'a') as f:
            f.write(content)

def get_d4_client_config():
    d4_client_config = get_d4_client_config_dir()
    filename = os.path.join(d4_client_config, 'uuid')
    if not os.path.isfile(filename):
        create_d4_config_file(filename, get_ail_uuid())
    return d4_client_config

def is_passive_dns_enabled(cache=True):
    if cache:
        res = r_cache.get('d4:passivedns:enabled')
        if res is None:
            res = r_serv_db.hget('d4:passivedns', 'enabled') == 'True'
            r_cache.set('d4:passivedns:enabled', res)
            return res
        else:
            return res == 'True'
    else:
        return r_serv_db.hget('d4:passivedns', 'enabled') == 'True'

def change_passive_dns_state(new_state):
    old_state = is_passive_dns_enabled(cache=False)
    if old_state != new_state:
        r_serv_db.hset('d4:passivedns', 'enabled', bool(new_state))
        r_cache.set('d4:passivedns:enabled', bool(new_state))
        update_time = time.time()
        r_serv_db.hset('d4:passivedns', 'update_time', update_time)
        r_cache.set('d4:passivedns:last_update_time', update_time)
        return True
    return False

def get_config_last_update_time():
    last_update_time = r_cache.get('d4:passivedns:last_update_time')
    if not last_update_time:
        last_update_time = r_serv_db.hget('d4:passivedns', 'update_time')
        if not last_update_time:
            last_update_time = 0
        last_update_time = float(last_update_time)
        r_cache.set('d4:passivedns:last_update_time', last_update_time)
    return float(last_update_time)

def create_d4_client():
    if is_passive_dns_enabled():
        d4_client = d4_pyclient.D4Client(get_d4_client_config(), False)
        return d4_client
    else:
        return None
