#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import redis
import bcrypt

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

from functools import wraps
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from flask import request, make_response, current_app

login_manager = LoginManager()
login_manager.login_view = 'root.role'

# CONFIG #
config_loader = ConfigLoader.ConfigLoader()

r_serv_db = config_loader.get_redis_conn("ARDB_DB")
config_loader = None

default_passwd_file = os.path.join(os.environ['AIL_HOME'], 'DEFAULT_PASSWORD')

regex_password = r'^(?=(.*\d){2})(?=.*[a-z])(?=.*[A-Z]).{10,100}$'
regex_password = re.compile(regex_password)

###############################################################
###############          FLASK CACHE         ##################
###############################################################
def no_cache(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        resp = make_response(func(*args, **kwargs))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        return resp
    return decorated_view
###############################################################
###############################################################
###############################################################

###############################################################
###############       CHECK ROLE ACCESS      ##################
###############################################################

def login_admin(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif (not current_user.is_in_role('admin')):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

def login_analyst(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif (not current_user.is_in_role('analyst')):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

def login_user(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif (not current_user.is_in_role('user')):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

def login_user_no_api(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif (not current_user.is_in_role('user_no_api')):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

def login_read_only(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif (not current_user.is_in_role('read_only')):
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

###############################################################
###############################################################
###############################################################

def gen_password(length=30, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_!@#$%^&*()"):
    random_bytes = os.urandom(length)
    len_charset = len(charset)
    indices = [int(len_charset * (byte / 256.0)) for byte in random_bytes]
    return "".join([charset[index] for index in indices])

def gen_token(length=41, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"):
    random_bytes = os.urandom(length)
    len_charset = len(charset)
    indices = [int(len_charset * (byte / 256.0)) for byte in random_bytes]
    return "".join([charset[index] for index in indices])

def generate_new_token(user_id):
    # create user token
    current_token = r_serv_db.hget('user_metadata:{}'.format(user_id), 'token')
    r_serv_db.hdel('user:tokens', current_token)
    token = gen_token(41)
    r_serv_db.hset('user:tokens', token, user_id)
    r_serv_db.hset('user_metadata:{}'.format(user_id), 'token', token)

def get_default_admin_token():
    if r_serv_db.exists('user_metadata:admin@admin.test'):
        return r_serv_db.hget('user_metadata:admin@admin.test', 'token')
    else:
        return ''

def create_user_db(username_id , password, default=False, role=None, update=False):
    password = password.encode()
    password_hash = hashing_password(password)

    # create user token
    generate_new_token(username_id)

    if not role:
        role = 'read_only'

    if update:
        r_serv_db.hdel('user_metadata:{}'.format(username_id), 'change_passwd')
        # remove default user password file
        if username_id=='admin@admin.test':
            os.remove(default_passwd_file)
        r_serv_db.hset('user:all', username_id, password_hash)
    else:
        if default:
            r_serv_db.hset('user_metadata:{}'.format(username_id), 'change_passwd', True)
        if role:
            if role in get_all_role():
                for role_to_add in get_all_user_role(role):
                    r_serv_db.sadd('user_role:{}'.format(role_to_add), username_id)
                r_serv_db.hset('user_metadata:{}'.format(username_id), 'role', role)

        r_serv_db.hset('user:all', username_id, password_hash)

def edit_user_db(user_id, role, password=None):
    if password:
        password_hash = hashing_password(password.encode())
        r_serv_db.hset('user:all', user_id, password_hash)

    current_role = r_serv_db.hget('user_metadata:{}'.format(user_id), 'role')
    if role != current_role:
        request_level = get_role_level(role)
        current_role = get_role_level(current_role)

        if current_role < request_level:
            role_to_remove = get_user_role_by_range(current_role -1, request_level - 2)
            for role_id in role_to_remove:
                r_serv_db.srem('user_role:{}'.format(role_id), user_id)
            r_serv_db.hset('user_metadata:{}'.format(user_id), 'role', role)
        else:
            role_to_add = get_user_role_by_range(request_level -1, current_role)
            for role_id in role_to_add:
                r_serv_db.sadd('user_role:{}'.format(role_id), user_id)
            r_serv_db.hset('user_metadata:{}'.format(user_id), 'role', role)

def delete_user_db(user_id):
    if r_serv_db.exists('user_metadata:{}'.format(user_id)):
        role_to_remove =get_all_role()
        for role_id in role_to_remove:
            r_serv_db.srem('user_role:{}'.format(role_id), user_id)
        user_token = r_serv_db.hget('user_metadata:{}'.format(user_id), 'token')
        r_serv_db.hdel('user:tokens', user_token)
        r_serv_db.delete('user_metadata:{}'.format(user_id))
        r_serv_db.hdel('user:all', user_id)
    else:
        print('Error: user {} do not exist'.format(user_id))

def hashing_password(bytes_password):
    hashed = bcrypt.hashpw(bytes_password, bcrypt.gensalt())
    return hashed

def check_password_strength(password):
    result = regex_password.match(password)
    if result:
        return True
    else:
        return False

def get_all_role():
    return r_serv_db.zrange('ail:all_role', 0, -1)

def get_role_level(role):
    return int(r_serv_db.zscore('ail:all_role', role))

def get_all_user_role(user_role):
    current_role_val = get_role_level(user_role)
    return r_serv_db.zrange('ail:all_role', current_role_val -1, -1)

def get_all_user_upper_role(user_role):
    current_role_val = get_role_level(user_role)
    # remove one rank
    if current_role_val > 1:
        return r_serv_db.zrange('ail:all_role', 0, current_role_val -2)
    else:
        return []

def get_user_role_by_range(inf, sup):
    return r_serv_db.zrange('ail:all_role', inf, sup)

def get_user_role(user_id):
    return r_serv_db.hget('user_metadata:{}'.format(user_id), 'role')

def check_user_role_integrity(user_id):
    user_role = get_user_role(user_id)
    all_user_role = get_all_user_role(user_role)
    res = True
    for role in all_user_role:
        if not r_serv_db.sismember('user_role:{}'.format(role), user_id):
            res = False
    upper_role = get_all_user_upper_role(user_role)
    for role in upper_role:
        if r_serv_db.sismember('user_role:{}'.format(role), user_id):
            res = False
    return res
