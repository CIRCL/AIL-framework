#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import bcrypt
import os
import pyotp
import re
import secrets
import sys

import segno

from base64 import b64encode
from datetime import datetime
from flask_login import UserMixin
from io import BytesIO
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

if config_loader.get_config_boolean('Users', 'force_2fa'):
    r_serv_db.hset('ail:2fa', '2fa', 1)
else:
    r_serv_db.hset('ail:2fa', '2fa', 0)
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

def is_user_logged(user_id):
    if get_user_session(user_id):
        return True
    else:
        return False

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

def get_user_passwd_hash(user_id):
    return r_serv_db.hget('ail:users:all', user_id)

## --PASSWORDS-- ##

def check_email(email):
    email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}')
    result = email_regex.match(email)
    if result:
        return True
    else:
        return False

#### TOKENS ####

def get_user_token(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'token')

def get_token_user(token):
    return r_serv_db.hget('ail:users:tokens', token)

def exists_token(token):
    return r_serv_db.hexists('ail:users:tokens', token)

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

def get_user_otp_secret(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'otp_secret')

def get_user_hotp_counter(user_id):
    return int(r_serv_db.hget(f'ail:user:metadata:{user_id}', 'otp_counter'))

def verify_user_totp(user_id, code):
    totp = _get_totp(get_user_otp_secret(user_id))
    return _verify_totp(totp, code)

def verify_user_hotp(user_id, code):
    hotp = _get_hotp(get_user_otp_secret(user_id))
    counter = get_user_hotp_counter(user_id)
    valid = _verify_hotp(hotp, counter, code)
    if valid:
        r_serv_db.hincrby(f'ail:user:metadata:{user_id}', 'otp_counter', 1)
    return valid

def verify_user_otp(user_id, code):
    if verify_user_totp(user_id, code):
        return True
    elif verify_user_hotp(user_id, code):
        return True
    return False

def create_user_otp(user_id):
    secret = pyotp.random_base32()
    r_serv_db.hset(f'ail:user:metadata:{user_id}', 'otp_secret', secret)
    r_serv_db.hset(f'ail:user:metadata:{user_id}', 'otp_counter', 0)
    enable_user_2fa(user_id)

def delete_user_otp(user_id):
    r_serv_db.hdel(f'ail:user:metadata:{user_id}', 'otp_secret')
    r_serv_db.hdel(f'ail:user:metadata:{user_id}', 'otp_counter')
    r_serv_db.hset(f'ail:user:metadata:{user_id}', 'otp_setup', 0)
    disable_user_2fa(user_id)

def get_user_otp_uri(user_id, instance_name):
    return pyotp.totp.TOTP(get_user_otp_secret(user_id)).provisioning_uri(name=user_id, issuer_name=instance_name)

def get_user_otp_qr_code(user_id, instance_name):
    uri = get_user_otp_uri(user_id, instance_name)
    qrcode = segno.make_qr(uri)
    buff = BytesIO()
    qrcode.save(buff, kind='png', scale=10)
    return b64encode(buff.getvalue()).decode()
    # qrcode.save('qrcode.png', scale=10)

def get_user_hotp_code(user_id):
    hotp = _get_hotp(get_user_otp_secret(user_id))
    counter = get_user_hotp_counter(user_id)
    codes = []
    for i in range(counter, counter + 20):
        codes.append(f'{i}: {hotp.at(i)}')
    return codes

# TODO GET USER HOTP LISTS
# TODO RESET OTP

def is_user_otp_setup(user_id):
    otp_setup = r_serv_db.hget(f'ail:user:metadata:{user_id}', 'otp_setup')
    if otp_setup:
        return int(otp_setup) == 1
    return False

## --OTP-- ##

#### 2FA ####

# Global 2fa option
def is_2fa_enabled():
    fa2 = r_serv_db.hget('ail:2fa', '2fa')
    if fa2:
        return int(fa2) == 1
    return False

def is_user_2fa_enabled(user_id):
    fa2 = r_serv_db.hget(f'ail:user:metadata:{user_id}', '2fa')
    if fa2:
        return int(fa2) == 1
    return False

def enable_user_2fa(user_id):
    return r_serv_db.hset(f'ail:user:metadata:{user_id}', '2fa', 1)

def disable_user_2fa(user_id):
    return r_serv_db.hset(f'ail:user:metadata:{user_id}', '2fa', 0)

## --2FA-- ##

#### USERS ####

def get_users():
    return r_serv_db.hkeys('ail:users:all')

def get_user_role(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'role')

## --USERS-- ##

#### USERS ####

def get_user_creator(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'creator')

def get_user_creation_date(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'created_at')

def get_user_last_edit(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'last_edit')  # self edit or admin ???

def get_user_last_login(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'last_login')

def get_user_last_seen(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'last_seen')

def get_disabled_users():
    return r_serv_db.smembers(f'ail:users:disabled')

def is_user_disabled(user_id):
    return r_serv_db.sismember(f'ail:users:disabled', user_id)

def disable_user(user_id):
    r_serv_db.sadd(f'ail:users:disabled', user_id)

def enable_user(user_id):
    r_serv_db.srem(f'ail:users:disabled', user_id)

def create_user(user_id, password=None, admin_id=None, chg_passwd=True, role=None, otp=False):  # TODO LOGS
    # # TODO: check password strength
    if password:
        new_password = password
    else:
        new_password = gen_password()
    password_hash = hashing_password(new_password)

    # EDIT
    if exists_user(user_id):
        if password or chg_passwd:
            edit_user(user_id, password_hash, chg_passwd=chg_passwd)
        if role:
            edit_user_role(user_id, role)
    # CREATE USER
    elif admin_id:
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'creator', admin_id)
        date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'created_at', date)
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'last_edit', date)

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

        if otp or is_2fa_enabled():
            enable_user_2fa(user_id)


def edit_user(user_id, password_hash, chg_passwd=False, otp=True):
    if chg_passwd:
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'change_passwd', 'True')
        r_serv_db.hset('ail:users:all', user_id, password_hash)

        # create new token
        generate_new_token(user_id)
    else:
        r_serv_db.hdel(f'ail:user:metadata:{user_id}', 'change_passwd')

    # 2FA OTP
    if otp or is_2fa_enabled():
        enable_user_2fa(user_id)
    else:
        disable_user_2fa(user_id)

    date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    r_serv_db.hset(f'ail:user:metadata:{user_id}', 'last_edit', date)

    # Remove default user password file
    if user_id == 'admin@admin.test':
        default_passwd_file = os.path.join(os.environ['AIL_HOME'], 'DEFAULT_PASSWORD')
        if os.path.isfile(default_passwd_file):
            os.remove(default_passwd_file)








## --USER-- ##

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

    def update_last_seen(self):
        r_serv_db.hset(f'ail:user:metadata:{self.user_id}', 'last_seen', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

    def update_last_login(self):
        r_serv_db.hset(f'ail:user:metadata:{self.user_id}', 'last_login', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

    def get_meta(self, options=set()):
        meta = {'id': self.user_id}
        if 'creator' in options:
            meta['creator'] = get_user_creator(self.user_id)
        if 'created_at' in options:
            meta['created_at'] = get_user_creation_date(self.user_id)
        if 'last_edit' in options:
            meta['last_edit'] = get_user_last_edit(self.user_id)
        if 'last_login' in options:
            meta['last_login'] = get_user_last_login(self.user_id)
        if 'last_seen' in options:
            meta['last_seen'] =  get_user_last_seen(self.user_id)
        if 'api_key' in options: # TODO add option to censor key
            meta['api_key'] = self.get_api_key()
        if 'role' in options:
            meta['role'] = get_user_role(self.user_id)
        if '2fa' in options:
            meta['2fa'] = self.is_2fa_enabled()
        if 'otp_setup' in options:
            meta['otp_setup'] = self.is_2fa_setup()
        if 'is_disabled' in options:
            meta['is_disabled'] = self.is_disabled()
        if 'is_logged' in options:
            meta['is_logged'] = is_user_logged(self.user_id)
        return meta

    ## SESSION ##

    def is_disabled(self):
        return is_user_disabled(self.user_id)

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

    ## OTP ##

    def is_2fa_setup(self):
        return is_user_otp_setup(self.user_id)

    def is_2fa_enabled(self):
        if is_2fa_enabled():
            return True
        else:
            return is_user_2fa_enabled(self.user_id)

    def get_htop_counter(self):
        return get_user_hotp_counter(self.user_id)

    def is_valid_otp(self, code):
        return verify_user_otp(self.user_id, code)

    def init_setup_2fa(self, create=True):
        if create:
            create_user_otp(self.user_id)
        instance_name = 'AIL TEST'
        return get_user_otp_qr_code(self.user_id, instance_name), get_user_otp_uri(self.user_id, instance_name), get_user_hotp_code(self.user_id)

    def setup_2fa(self):
        r_serv_db.hset(f'ail:user:metadata:{self.user_id}', 'otp_setup', 1)

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
    options = {'api_key', 'creator', 'created_at', 'is_logged', 'last_edit', 'last_login', 'last_seen', 'role', '2fa', 'otp_setup'}
    for user_id in get_users():
        user = AILUser(user_id)
        meta['users'].append(user.get_meta(options=options))
    return meta

def api_get_user_profile(user_id):
    options = {'api_key', 'role', '2fa'}
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    meta = user.get_meta(options=options)
    return meta, 200

def api_get_user_hotp(user_id):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    hotp = get_user_hotp_code(user_id)
    return hotp, 200

def api_logout_user(admin_id, user_id): # TODO LOG ADMIN ID
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    print(admin_id)
    return user.kill_session(), 200

def api_logout_users(admin_id): # TODO LOG ADMIN ID
    print(admin_id)
    return kill_sessions(), 200

def api_disable_user(admin_id, user_id): # TODO LOG ADMIN ID
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    if user.is_disabled():
        return {'status': 'error', 'reason': 'User is already disabled'}, 400
    print(admin_id)
    disable_user(user_id)

def api_enable_user(admin_id, user_id): # TODO LOG ADMIN ID
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    if not user.is_disabled():
        return {'status': 'error', 'reason': 'User is not disabled'}, 400
    print(admin_id)
    enable_user(user_id)

def api_enable_user_otp(user_id):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    if user.is_2fa_enabled():
        return {'status': 'error', 'reason': 'User OTP is already setup'}, 400
    delete_user_otp(user_id)
    enable_user_2fa(user_id)
    return user_id, 200

def api_disable_user_otp(user_id):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    if not user.is_2fa_enabled():
        return {'status': 'error', 'reason': 'User OTP is not enabled'}, 400
    if is_2fa_enabled():
        return {'status': 'error', 'reason': '2FA is enforced on this instance'}, 400
    disable_user_2fa(user_id)
    delete_user_otp(user_id)
    return user_id, 200

def api_reset_user_otp(admin_id, user_id):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    admin = AILUser(admin_id)
    if not admin.is_in_role('admin'):
        return {'status': 'error', 'reason': 'Access Denied'}, 403
    if not user.is_2fa_setup():
        return {'status': 'error', 'reason': 'User OTP is not setup'}, 400
    delete_user_otp(user_id)
    enable_user_2fa(user_id)
    return user_id, 200

def api_create_user_api_key_self(user_id): # TODO LOG USER ID
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    return user.new_api_key(), 200

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
        r_serv_db.srem(f'ail:users:disabled', user_id)

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

# if __name__ == '__main__':
#     user_id = 'admin@admin.test'
#     instance_name = 'AIL TEST'
#     delete_user_otp(user_id)
#     # q = get_user_otp_qr_code(user_id, instance_name)
#     # print(q)