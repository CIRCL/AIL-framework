#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib import ail_users

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None


def check_token_format(token, search=re.compile(r'[^a-zA-Z0-9_-]').search): ####################################################
    return not bool(search(token))

def is_valid_token(token):
    return ail_users.exists_token(token)

def get_user_from_token(token):
    return ail_users.get_token_user(token)

def get_basic_user_meta(token):
    user_id = get_user_from_token(token)
    return ail_users.get_user_org(user_id), user_id, ail_users.get_user_role(user_id)

def is_user_in_role(role, token):   # verify_user_role
    # User without API
    if role == 'user_no_api':
        return False

    user_id = get_user_from_token(token)
    if user_id:
        return ail_users.is_in_role(user_id, role)
    else:
        return False

#### Brute Force Protection ####

def get_failed_login(ip_address):
    return r_cache.get(f'failed_login_ip_api:{ip_address}')

def incr_failed_login(ip_address):
    r_cache.incr(f'failed_login_ip_api:{ip_address}')
    r_cache.expire(f'failed_login_ip_api:{ip_address}', 300)

def get_brute_force_ttl(ip_address):
    return r_cache.ttl(f'failed_login_ip_api:{ip_address}')

def is_brute_force_protected(ip_address):
    failed_login = get_failed_login(ip_address)
    if failed_login:
        failed_login = int(failed_login)
        if failed_login >= 5:
            return True
        else:
            return False
    return False

#### --Brute Force Protection-- ####

def authenticate_user(token, ip_address):
    if is_brute_force_protected(ip_address):
        ip_ttl = get_brute_force_ttl(ip_address)
        return {'status': 'error', 'reason': f'Max Connection Attempts reached, Please wait {ip_ttl}s'}, 401

    try:
        if len(token) != 55:
            return {'status': 'error', 'reason': 'Invalid Token Length, required==55'}, 400
        if not check_token_format(token):
            return {'status': 'error', 'reason': 'Malformed Authentication String'}, 400

        if is_valid_token(token):
            ail_users.update_user_last_seen_api(get_user_from_token(token))
            return True, 200
        # Failed Login
        else:
            incr_failed_login(ip_address)
            return {'status': 'error', 'reason': 'Authentication failed'}, 401
    except Exception as e:
        print(e)  # TODO Logs
        return {'status': 'error', 'reason': 'Malformed Authentication String'}, 400
