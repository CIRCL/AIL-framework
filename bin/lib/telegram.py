#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys

from urllib.parse import urlparse

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_obj = config_loader.get_db_conn("Kvrocks_Objects")
config_loader = None

REGEX_USERNAME = re.compile(r'[0-9a-zA-z_]+')
REGEX_JOIN_HASH = re.compile(r'[0-9a-zA-z-]+')
USERNAME_CHARS = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")

##  ##

def save_telegram_invite_hash(invite_hash, obj_global_id):
    r_obj.sadd('telegram:invite_code', f'{invite_hash};{obj_global_id}')

def get_data_from_telegram_url(base_url, url_path):
    dict_url = {}
    url_path = url_path.split('/')

    # username len > 5, a-z A-Z _
    if len(url_path) == 1:
        username = url_path[0].lower()
        username = REGEX_USERNAME.search(username)
        if username:
            username = username[0].replace('\\', '')
            if len(username) > 5:
                dict_url['username'] = username
    elif url_path[0] == 'joinchat':
        invite_hash = REGEX_JOIN_HASH.search(url_path[1])
        if invite_hash:
            invite_hash = invite_hash[0]
            dict_url['invite_hash'] = invite_hash
    return dict_url

# # TODO:
#   Add openmessafe
#   Add passport ?
#   Add confirmphone
#   Add user
def get_data_from_tg_url(tg_link):
    dict_url = {}

    url = urlparse(tg_link)
    # username len > 5, a-z A-Z _
    if url.netloc == 'resolve' and len(url.query) > 7:
        if url.query[:7] == 'domain=':
            # remove domain=
            username = url.query[7:]
            username = REGEX_USERNAME.search(username)
            if username:
                username = username[0].replace('\\', '')
                if len(username) > 5:
                    dict_url['username'] = username

    elif url.netloc == 'join' and len(url.query) > 7:
        if url.query[:7] == 'invite=':
            invite_hash = url.query[7:]
            invite_hash = REGEX_JOIN_HASH.search(invite_hash)
            if invite_hash:
                invite_hash = invite_hash[0]
                dict_url['invite_hash'] = invite_hash

    elif url.netloc == 'login' and len(url.query) > 5:
        login_code = url.query[5:]
        if login_code:
            dict_url['login_code'] = login_code
    else:
        # # TODO: log invalid URL ???????
        print(url)

    return dict_url
