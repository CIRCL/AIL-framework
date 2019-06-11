#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import redis
import bcrypt
import secrets
import configparser

from functools import wraps
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from flask import request, current_app

login_manager = LoginManager()
login_manager.login_view = 'role'

# CONFIG #
configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
if not os.path.exists(configfile):
    raise Exception('Unable to find the configuration file. \
                    Did you set environment variables? \
                    Or activate the virtualenv.')

cfg = configparser.ConfigParser()
cfg.read(configfile)

r_serv_db = redis.StrictRedis(
    host=cfg.get("ARDB_DB", "host"),
    port=cfg.getint("ARDB_DB", "port"),
    db=cfg.getint("ARDB_DB", "db"),
    decode_responses=True)

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



###############################################################
###############################################################
###############################################################



def create_user_db(username_id , password, default=False, role=None, update=False):
    password = password.encode()
    password_hash = hashing_password(password)

    # create user token
    token = secrets.token_urlsafe(41)
    r_serv_db.hset('user:tokens', token, username_id)
    r_serv_db.hset('user_metadata:{}'.format(username_id), 'token', token)

    if update:
        r_serv_db.hdel('user_metadata:{}'.format(username_id), 'change_passwd')
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
            print('to remove')
            print(role_to_remove)
            for role_id in role_to_remove:
                r_serv_db.srem('user_role:{}'.format(role_id), user_id)
            r_serv_db.hset('user_metadata:{}'.format(user_id), 'role', role)
        else:
            role_to_add = get_user_role_by_range(request_level -1, current_role)
            print('to add')
            print(role_to_add)
            for role_id in role_to_add:
                r_serv_db.sadd('user_role:{}'.format(role_id), user_id)
            r_serv_db.hset('user_metadata:{}'.format(user_id), 'role', role)

def delete_user_db(user_id):
    if r_serv_db.exists('user_metadata:{}'.format(user_id)):
        print('r')
        role_to_remove =get_all_role()
        for role_id in role_to_remove:
            r_serv_db.srem('user_role:{}'.format(role_id), user_id)
        user_token = r_serv_db.hget('user_metadata:{}'.format(user_id), 'token')
        r_serv_db.hdel('user:tokens', user_token)
        r_serv_db.delete('user_metadata:{}'.format(user_id))
        r_serv_db.hdel('user:all', user_id)

def hashing_password(bytes_password):
    hashed = bcrypt.hashpw(bytes_password, bcrypt.gensalt())
    return hashed

def get_all_role():
    return r_serv_db.zrange('ail:all_role', 0, -1)

def get_role_level(role):
    return int(r_serv_db.zscore('ail:all_role', role))

def get_all_user_role(user_role):
    current_role_val = get_role_level(user_role)
    return r_serv_db.zrange('ail:all_role', current_role_val -1, -1)

def get_user_role_by_range(inf, sup):
    print(inf)
    print(sup)
    return r_serv_db.zrange('ail:all_role', inf, sup)
