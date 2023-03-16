#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import bcrypt
import os
import re
import secrets
import sys

from flask_login import UserMixin

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

# Config
config_loader = ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

regex_password = r'^(?=(.*\d){2})(?=.*[a-z])(?=.*[A-Z]).{10,100}$'
regex_password = re.compile(regex_password)

# # TODO: ADD FUNCTIONS PASSWORD RESET + API KEY RESET + CREATE USER

# # TODO: migrate Role_Manager

#### PASSWORDS + TOKENS ####

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

def get_default_admin_token():
    if r_serv_db.exists('ail:user:metadata:admin@admin.test'):
        return r_serv_db.hget('ail:user:metadata:admin@admin.test', 'token')
    else:
        return ''

##-- PASSWORDS + TOKENS --##

#### USERS ####

def get_all_users():
    return r_serv_db.hkeys('ail:users:all')

def get_user_role(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'role')

def get_user_passwd_hash(user_id):
    return r_serv_db.hget('ail:users:all', user_id)

def get_user_token(user_id):
    return r_serv_db.hget(f'ail:users:metadata:{user_id}', 'token')

def get_token_user(token):
    return r_serv_db.hget('ail:users:tokens', token)

def exists_token(token):
    return r_serv_db.hexists('ail:users:tokens', token)

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
        r_serv_db.hdel('ail:users:tokens', user_token)
        r_serv_db.delete(f'ail:user:metadata:{user_id}')
        r_serv_db.hdel('ail:users:all', user_id)

    # # TODO: raise Exception
    else:
        print(f'Error: user {user_id} do not exist')

##-- USERS --##

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

##-- ROLES --##

class User(UserMixin):

    def __init__(self, id):

        if r_serv_db.hexists('ail:users:all', id):
            self.id = id
        else:
            self.id = "__anonymous__"

    def exists(self):
        return self.id != "__anonymous__"

    # return True or False
    # def is_authenticated():

    # return True or False
    # def is_anonymous():

    @classmethod
    def get(self_class, id):
        return self_class(id)

    def user_is_anonymous(self):
        if self.id == "__anonymous__":
            return True
        else:
            return False

    def check_password(self, password):
        if self.user_is_anonymous():
            return False

        password = password.encode()
        hashed_password = r_serv_db.hget('ail:users:all', self.id).encode()
        if bcrypt.checkpw(password, hashed_password):
            return True
        else:
            return False

    def request_password_change(self):
        if r_serv_db.hget(f'ail:user:metadata:{self.id}', 'change_passwd') == 'True':
            return True
        else:
            return False

    def is_in_role(self, role):
        if r_serv_db.sismember(f'ail:users:role:{role}', self.id):
            return True
        else:
            return False
