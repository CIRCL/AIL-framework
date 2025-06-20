#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import d4_pyclient

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None


#### PASSIVE DNS ####

# TODO check 429 -> Too Many Requests
def set_default_passive_dns():
    r_db.hset('passive-dns', 'url', 'https://www.circl.lu/pdns')
    set_passive_dns_auth('ail-project', 'O/BDlUg4CZ2jusMeklqXc37lk/59Ch3qt1d4kYsyFSI=')
    enable_passive_dns()


# TODO CACHE IT
def is_passive_dns_enabled(): # TODO
    return r_db.hget('passive-dns', 'enabled') == 'True'

def enable_passive_dns():
    r_db.hset('passive-dns', 'enabled', 'True')

def disable_passive_dns():
    r_db.hset('passive-dns', 'enabled', 'False')

def get_passive_dns_url():
    return r_db.hget('passive-dns', 'url')

def _get_passive_dns_user():
    return r_db.hget('passive-dns', 'user')

def _get_passive_dns_api_password():
    return r_db.hget('passive-dns', 'password')

def set_passive_dns_auth(user, password):
    if not user:
        r_db.hdel('passive-dns', 'user')
    else:
        r_db.hset('passive-dns', 'user', user)
    if not password:
        r_db.hdel('passive-dns', 'password')
    else:
        r_db.hset('passive-dns', 'password', password)

def get_passive_dns_auth():
    user = _get_passive_dns_user()
    password = _get_passive_dns_api_password()
    if user and password:
        return user, password
    else:
        return None

def get_passive_dns_test():
    return r_db.hget('passive-dns', 'test')

def set_passive_dns_test(text, is_error=False):
    r_db.hset('passive-dns', 'test', text)
    if is_error:
        r_db.hset('passive-dns', 'error', 1)
    else:
        r_db.hset('passive-dns', 'error', 0)

def get_passive_dns_meta():
    return {'is_enabled': is_passive_dns_enabled(),
            'user': _get_passive_dns_user(),
            'password': _get_passive_dns_api_password(),
            'test': get_passive_dns_test()}

def get_passive_dns_session():
    s = requests.Session()
    passive_dns_auth = get_passive_dns_auth()
    if passive_dns_auth:
        s.auth = passive_dns_auth
    commit_id = git_status.get_last_commit_id_from_local()
    s.headers.update({'User-Agent': f'AIL-{commit_id}'})
    return s

def _get_passive_dns_result(path):
    s = get_passive_dns_session()
    res = s.get(f'{get_passive_dns_url()}{path}')
    if res.status_code != 200:
        # TODO LOG
        if res.status_code != 404:
            print(f" PassiveDNS requests error: {res.status_code}, {res.text}")
        # set_passive_dns_test(f"{res.status_code}: {res.text}", is_error=True)
        return res.text, res.status_code
    else:
        r = res.json()
        if r:
            return r, 200
    return None, 200

def get_passive_dns_query(query):
    res = _get_passive_dns_result(f'/query/{query}')
    if res[1] == 200:
        return res[0]
    else:
        return None

def api_edit_passive_dns(user, password):
    if user or password:
        set_passive_dns_auth(user, password)
    return None, 200
