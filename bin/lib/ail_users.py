#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import bcrypt
import os
import pyotp
import re
import secrets
import sys

from flask_login import UserMixin
from uuid import uuid4

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

# Config
config_loader = ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None

regex_password = r'^(?=(.*\d){2})(?=.*[a-z])(?=.*[A-Z]).{10,100}$'
regex_password = re.compile(regex_password)

# # TODO: migrate Role_Manager


#### SESSIONS ####

def get_sessions():
    r_cache.smembers('ail:sessions')

def exists_session(session):
    r_cache.hexists('ail:sessions', session)

def exists_session_user(user_id):
    r_cache.hexists('ail:sessions:users', user_id)

def get_session_user(session):
    return r_cache.hget('ail:sessions', session)

def get_user_session(user_id):
    return r_cache.hget('ail:sessions:users', user_id)

def _generate_session_key(user_id):
    return f'{user_id}:{str(uuid4())}'

def _rotate_user_session(user_id):
    kill_session_user(user_id)
    new_session = _generate_session_key(user_id)
    r_cache.hset('ail:sessions', new_session, user_id)
    r_cache.hset('ail:sessions:users', user_id, new_session)
    return new_session

def kill_session_user(user_id):
    session = get_user_session(user_id)
    if session:
        r_cache.hdel('ail:sessions', session)
    r_cache.hdel('ail:sessions:users', user_id)

def kill_sessions():
    r_cache.delete('ail:sessions')
    r_cache.delete('ail:sessions:users')


#### PASSWORDS ####

def check_password_strength(password):
    result = regex_password.match(password)
    if result:
        return True
    else:
        return False

def gen_password():
    return secrets.token_urlsafe(30)

def hashing_password(password):
    password = password.encode()
    return bcrypt.hashpw(password, bcrypt.gensalt())

## --PASSWORDS-- ##


#### TOKENS ####

def gen_token():
    return secrets.token_urlsafe(41)

def _delete_user_token(user_id):
    current_token = get_user_token(user_id)
    if current_token:
        r_serv_db.hdel('ail:users:tokens', current_token)

def _set_user_token(user_id, token):
    r_serv_db.hset('ail:users:tokens', token, user_id)
    r_serv_db.hset(f'ail:user:metadata:{user_id}', 'token', token)

def generate_new_token(user_id):
    # create user token
    _delete_user_token(user_id)
    token = gen_token()
    _set_user_token(user_id, token)

def get_default_admin_token():  # TODO REMOVE ME ##############################################################################
    if r_serv_db.exists('ail:user:metadata:admin@admin.test'):
        return r_serv_db.hget('ail:user:metadata:admin@admin.test', 'token')
    else:
        return ''

## --TOKENS-- ##


#### OTP ####

def _get_totp(secret):
    return pyotp.TOTP(secret)

def _verify_totp(totp, code):
    return totp.verify(code)

def _get_hotp(secret):
    return pyotp.HOTP(secret)

def _verify_hotp(hotp, counter, code):
    return hotp.verify(code, counter)

## --OTP-- ##

#### USERS ####

def get_users():
    return r_serv_db.hkeys('ail:users:all')

def get_user_role(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'role')

def get_user_passwd_hash(user_id):
    return r_serv_db.hget('ail:users:all', user_id)

def get_user_token(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'token')

def get_token_user(token):
    return r_serv_db.hget('ail:users:tokens', token)

def exists_token(token):
    return r_serv_db.hexists('ail:users:tokens', token)

# def _get_user_otp(user_id):
#
#
# def get_user_hotps(user_id):
#
#
# def _get_user_hotp(user_id):
#
#
# def verify_user_otp(user_id, code):
#
#
# def get_user_hotp_counter(user_id):
#     return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'hotp:counter')
#
# def verify_user_hotp(user_id, code):
#     counter

########################################################################################################################
########################################################################################################################

# TODO USER LAST LOGIN TIME
# TODO Check if logged

# TODO USER:     - Creation Date
#                - Last Login
#                - Last Request
#                - Last API Usage
#                - Organisation ???
#                - Disabled / Lock

class AILUser(UserMixin):
    def __init__(self, user_id):
        self.user_id = user_id
        session = get_user_session(self.user_id)
        if session:
            self.id = session
        else:
            self.id = "__anonymous__"

    @classmethod
    def get(self_class, id):
        return self_class(id)

    # @property
    # def is_anonymous(self):
    #     return  self.id == "__anonymous__"

    # def get_id(self):
    #     return self.id

    def get_user_id(self):
        return self.user_id

    def exists(self): # TODO CHECK USAGE
        return r_serv_db.exists(f'ail:user:metadata:{self.user_id}')

    def get_meta(self, options=set()): # TODO user creation date
        meta = {'id': self.user_id}
        if 'api_key' in options: # TODO add option to censor key
            meta['api_key'] = self.get_api_key()
        if 'role' in options:
            meta['role'] = get_user_role(self.user_id)
        return meta

    ## SESSION ##

    def is_logged(self): #####################################################################################################
        pass

    def get_session(self):
        return self.id

    def rotate_session(self):
        self.id = _rotate_user_session(self.user_id)
        print('rotate session:', self.id)
        return self.id

    def kill_session(self):
        kill_session_user(self.user_id)
        self.id = None

    ## PASSWORD ##

    def is_password_change_requested(self):
        if r_serv_db.hget(f'ail:user:metadata:{self.user_id}', 'change_passwd') == 1:
            return True
        else:
            return False

    def request_password_change(self):
        r_serv_db.hset(f'ail:user:metadata:{self.user_id}', 'change_passwd', 1)

    def check_password(self, password):
        password = password.encode()
        hashed_password = r_serv_db.hget('ail:users:all', self.user_id).encode()
        if bcrypt.checkpw(password, hashed_password):
            return True
        else:
            return False

    def edit_password(self, password_hash, chg_passwd=False):  # TODO REPLACE BY PASSWORD
        if chg_passwd:
            r_serv_db.hset(f'ail:user:metadata:{self.user_id}', 'change_passwd', 1)
        else:
            r_serv_db.hdel(f'ail:user:metadata:{self.user_id}', 'change_passwd')
        # remove default user password file ##########################################################################  TODO MOVE ME
        if self.user_id == 'admin@admin.test':
            default_passwd_file = os.path.join(os.environ['AIL_HOME'], 'DEFAULT_PASSWORD')
            if os.path.isfile(default_passwd_file):
                os.remove(default_passwd_file)
        r_serv_db.hset('ail:users:all', self.user_id, password_hash)
        # create new token
        generate_new_token(self.user_id)

    ## TOKEN ##

    def get_api_key(self):
        return get_user_token(self.user_id)

    def new_api_key(self):
        _delete_user_token(self.user_id)
        new_api_key = gen_token()
        _set_user_token(self.user_id, new_api_key)
        return new_api_key

    ## ROLE ##

    def is_in_role(self, role):  # TODO Get role via user alternative ID
        print('is_in_role')
        print(f'ail:users:role:{role}', self.user_id)
        if r_serv_db.sismember(f'ail:users:role:{role}', self.user_id):
            return True
        else:
            return False

    def get_role(self):
        return r_serv_db.hget(f'ail:user:metadata:{self.user_id}', 'role')

    ##  ##

    def delete(self):
        kill_session_user(self.user_id)
        for role_id in get_all_roles():
            r_serv_db.srem(f'ail:users:role:{role_id}', self.user_id)
        user_token = self.get_api_key()
        if user_token:
            r_serv_db.hdel('ail:users:tokens', user_token)
        r_serv_db.delete(f'ail:user:metadata:{self.user_id}')
        r_serv_db.hdel('ail:users:all', self.user_id)


# def create_user(user_id):

#### API ####

def api_get_users_meta():
    meta = {'users': []}
    options = {'api_key', 'role'}
    for user_id in get_users():
        user = AILUser(user_id)
        meta['users'].append(user.get_meta(options=options))
    return meta

def api_create_user_api_key(user_id, admin_id): # TODO LOG ADMIN ID
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    print(admin_id)
    return user.new_api_key(), 200

def api_delete_user(user_id, admin_id): # TODO LOG ADMIN ID
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    print(admin_id)
    return user.delete(), 200

########################################################################################################################
########################################################################################################################


def exists_user(user_id):
    return r_serv_db.exists(f'ail:user:metadata:{user_id}')

def get_user_metadata(user_id):
    user_metadata = {'email': user_id,
                     'role': r_serv_db.hget(f'ail:user:metadata:{user_id}', 'role'),
                     'api_key': r_serv_db.hget(f'ail:user:metadata:{user_id}', 'token')}
    return user_metadata

def get_users_metadata(list_users):
    users = []
    for user in list_users:
        users.append(get_user_metadata(user))
    return users

def create_user(user_id, password=None, chg_passwd=True, role=None):
    # # TODO: check password strength
    if password:
        new_password = password
    else:
        new_password = gen_password()
    password_hash = hashing_password(new_password)

    # EDIT
    if exists_user(user_id):
        if password or chg_passwd:
            edit_user_password(user_id, password_hash, chg_passwd=chg_passwd)
        if role:
            edit_user_role(user_id, role)
    # CREATE USER
    else:
        # Role
        if not role:
            role = get_default_role()

        if role in get_all_roles():
            for role_to_add in get_all_user_role(role):
                r_serv_db.sadd(f'ail:users:role:{role_to_add}', user_id)
            r_serv_db.hset(f'ail:user:metadata:{user_id}', 'role', role)

        r_serv_db.hset('ail:users:all', user_id, password_hash)
        if chg_passwd:
            r_serv_db.hset(f'ail:user:metadata:{user_id}', 'change_passwd', 'True')

        # create user token
        generate_new_token(user_id)

def edit_user_password(user_id, password_hash, chg_passwd=False):
    if chg_passwd:
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'change_passwd', 'True')
    else:
        r_serv_db.hdel(f'ail:user:metadata:{user_id}', 'change_passwd')
    # remove default user password file
    if user_id == 'admin@admin.test':
        default_passwd_file = os.path.join(os.environ['AIL_HOME'], 'DEFAULT_PASSWORD')
        if os.path.isfile(default_passwd_file):
            os.remove(default_passwd_file)
    r_serv_db.hset('ail:users:all', user_id, password_hash)
    # create new token
    generate_new_token(user_id)

# # TODO: solve edge_case self delete
def delete_user(user_id):
    if exists_user(user_id):
        for role_id in get_all_roles():
            r_serv_db.srem(f'ail:users:role:{role_id}', user_id)
        user_token = get_user_token(user_id)
        if user_token:
            r_serv_db.hdel('ail:users:tokens', user_token)
        r_serv_db.delete(f'ail:user:metadata:{user_id}')
        r_serv_db.hdel('ail:users:all', user_id)

    # # TODO: raise Exception
    else:
        print(f'Error: user {user_id} do not exist')

## --USERS-- ##

#### ROLES ####

def get_all_roles():
    return r_serv_db.zrange('ail:roles:all', 0, -1)

# create role_list
def _create_roles_list():
    if not r_serv_db.exists('ail:roles:all'):
        r_serv_db.zadd('ail:roles:all', {'admin': 1})
        r_serv_db.zadd('ail:roles:all', {'analyst': 2})
        r_serv_db.zadd('ail:roles:all', {'user': 3})
        r_serv_db.zadd('ail:roles:all', {'user_no_api': 4})
        r_serv_db.zadd('ail:roles:all', {'read_only': 5})

def get_role_level(role):
    return int(r_serv_db.zscore('ail:roles:all', role))

def get_user_role_by_range(inf, sup):
    return r_serv_db.zrange('ail:roles:all', inf, sup)

def get_all_user_role(user_role):
    current_role_val = get_role_level(user_role)
    return r_serv_db.zrange('ail:roles:all', current_role_val - 1, -1)

def get_all_user_upper_role(user_role):
    current_role_val = get_role_level(user_role)
    # remove one rank
    if current_role_val > 1:
        return r_serv_db.zrange('ail:roles:all', 0, current_role_val -2)
    else:
        return []

def get_default_role():
    return 'read_only'

def is_in_role(user_id, role):
    return r_serv_db.sismember(f'ail:users:role:{role}', user_id)

def edit_user_role(user_id, role):
    current_role = get_user_role(user_id)
    if role != current_role:
        request_level = get_role_level(role)
        current_role = get_role_level(current_role)

        if current_role < request_level:
            role_to_remove = get_user_role_by_range(current_role - 1, request_level - 2)
            for role_id in role_to_remove:
                r_serv_db.srem(f'ail:users:role:{role_id}', user_id)
            r_serv_db.hset(f'ail:user:metadata:{user_id}', 'role', role)
        else:
            role_to_add = get_user_role_by_range(request_level - 1, current_role)
            for role_id in role_to_add:
                r_serv_db.sadd(f'ail:users:role:{role_id}', user_id)
            r_serv_db.hset(f'ail:user:metadata:{user_id}', 'role', role)

def check_user_role_integrity(user_id):
    user_role = get_user_role(user_id)
    all_user_role = get_all_user_role(user_role)
    res = True
    for role in all_user_role:
        if not r_serv_db.sismember(f'ail:users:role:{role}', user_id):
            res = False
    upper_role = get_all_user_upper_role(user_role)
    for role in upper_role:
        if r_serv_db.sismember(f'ail:users:role:{role}', user_id):
            res = False
    return res

## --ROLES-- ##
