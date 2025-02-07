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
from lib import ail_logger
from lib import ail_orgs
from lib.ConfigLoader import ConfigLoader


# LOGS

access_logger = ail_logger.get_access_config()

# Config
config_loader = ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
r_cache = config_loader.get_redis_conn("Redis_Cache")

if config_loader.get_config_boolean('Users', 'force_2fa'):
    r_serv_db.hset('ail:2fa', '2fa', 1)
else:
    r_serv_db.hset('ail:2fa', '2fa', 0)

ail_2fa_name = config_loader.get_config_str('Users', '2fa_name')

config_loader = None

regex_password = r'^(?=(.*\d){2})(?=.*[a-z])(?=.*[A-Z]).{10,100}$'
regex_password = re.compile(regex_password)

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

def remove_default_password():
    # Remove default user password file
    default_passwd_file = os.path.join(os.environ['AIL_HOME'], 'DEFAULT_PASSWORD')
    if os.path.isfile(default_passwd_file):
        os.remove(default_passwd_file)

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
    return totp.verify(code, valid_window=1)

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

def create_qr_code(content):
    qrcode = segno.make_qr(content)
    buff = BytesIO()
    qrcode.save(buff, kind='png', scale=10)
    return b64encode(buff.getvalue()).decode()
    # qrcode.save('qrcode.png', scale=10)

def get_user_otp_qr_code(user_id, instance_name):
    uri = get_user_otp_uri(user_id, instance_name)
    return create_qr_code(uri)

def get_user_hotp_code(user_id, nb=20):
    hotp = _get_hotp(get_user_otp_secret(user_id))
    counter = get_user_hotp_counter(user_id)
    codes = []
    for i in range(counter, counter + nb):
        codes.append(f'{i}: {hotp.at(i)}')
    return codes

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

def get_users_meta(users):
    meta = []
    for user_id in users:
        user = AILUser(user_id)
        meta.append(user.get_meta({'role'}))
    return meta

def get_user_role(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'role')

## --USERS-- ##

#### USER ####

def exists_user(user_id):
    return r_serv_db.exists(f'ail:user:metadata:{user_id}')

def get_user_org(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'org')

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

def get_user_last_seen_api(user_id):
    return r_serv_db.hget(f'ail:user:metadata:{user_id}', 'last_seen_api')

def update_user_last_seen_api(user_id):
    r_serv_db.hset(f'ail:user:metadata:{user_id}', 'last_seen_api', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

def get_disabled_users():
    return r_serv_db.smembers(f'ail:users:disabled')

def is_user_disabled(user_id):
    return r_serv_db.sismember(f'ail:users:disabled', user_id)

def disable_user(user_id):
    r_serv_db.sadd(f'ail:users:disabled', user_id)

def enable_user(user_id):
    r_serv_db.srem(f'ail:users:disabled', user_id)

def create_user(user_id, password=None, admin_id=None, chg_passwd=True, org_uuid=None, role=None, otp=False):
    # # TODO: check password strength
    if password:
        new_password = password
    else:
        new_password = gen_password()
    password_hash = hashing_password(new_password)

    # CREATE USER
    if admin_id:
        # ORG
        org = ail_orgs.Organisation(org_uuid)
        if not org.exists():
            raise Exception('Organisation does not exist')

        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'creator', admin_id)
        date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'created_at', date)
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'last_edit', date)

        # Role
        if not role or role not in get_roles():
            role = get_default_role()
        set_user_role(user_id, role)

        # ORG
        org.add_user(user_id)

        r_serv_db.hset('ail:users:all', user_id, password_hash)
        if chg_passwd:
            r_serv_db.hset(f'ail:user:metadata:{user_id}', 'change_passwd', 'True')

        # create user token
        generate_new_token(user_id)

        if otp or is_2fa_enabled():
            enable_user_2fa(user_id)

# TODO edit_org
# TODO LOG
def edit_user(admin_id, user_id, password=None, chg_passwd=False, org_uuid=None, edit_otp=False, otp=True, role=None):
    if password:
        password_hash = hashing_password(password)
        if chg_passwd:
            r_serv_db.hset(f'ail:user:metadata:{user_id}', 'change_passwd', 'True')
            r_serv_db.hset('ail:users:all', user_id, password_hash)

            # create new token
            generate_new_token(user_id)
        else:
            r_serv_db.hdel(f'ail:user:metadata:{user_id}', 'change_passwd')

    if org_uuid:
        org = ail_orgs.Organisation(org_uuid)
        if org.exists():
            if not org.is_user(user_id):
                current_org = ail_orgs.Organisation(get_user_org(user_id))
                current_org.remove_user(user_id)
                org.add_user(user_id)

    if role:
        set_user_role(user_id, role)

    # 2FA OTP
    if edit_otp:
        if otp or is_2fa_enabled():
            enable_user_2fa(user_id)
        else:
            disable_user_2fa(user_id)

    date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    r_serv_db.hset(f'ail:user:metadata:{user_id}', 'last_edit', date)

    # Remove default user password file
    if user_id == 'admin@admin.test':
        remove_default_password()

## --USER-- ##

########################################################################################################################
########################################################################################################################

# TODO USER:
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

    def update_last_seen_api(self):
        update_user_last_seen_api(self.user_id)

    def update_last_login(self):
        r_serv_db.hset(f'ail:user:metadata:{self.user_id}', 'last_login', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

    def get_org(self):
        return get_user_org(self.user_id)

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
            meta['last_seen'] = get_user_last_seen(self.user_id)
        if 'last_seen_api' in options:
            meta['last_seen_api'] = get_user_last_seen_api(self.user_id)
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
        if 'org' in options:
            meta['org'] = self.get_org()
            if 'org_name' in options and meta['org']:
                meta['org_name'] = ail_orgs.Organisation(self.get_org()).get_name()
        return meta

    ## SESSION ##

    def is_disabled(self):
        return is_user_disabled(self.user_id)

    def get_session(self):
        return self.id

    def rotate_session(self):
        self.id = _rotate_user_session(self.user_id)
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
        instance_name = ail_2fa_name
        return get_user_otp_qr_code(self.user_id, instance_name), get_user_otp_uri(self.user_id, instance_name), get_user_hotp_code(self.user_id)

    def setup_2fa(self):
        r_serv_db.hset(f'ail:user:metadata:{self.user_id}', 'otp_setup', 1)

    ## ROLE ##

    def is_in_role(self, role):
        if r_serv_db.sismember(f'ail:users:role:{role}', self.user_id):
            return True
        else:
            return False

    def is_admin(self):
        return self.is_in_role('admin')

    def get_role(self):
        return r_serv_db.hget(f'ail:user:metadata:{self.user_id}', 'role')

    ##  ##

    def delete(self):
        kill_session_user(self.user_id)
        for role_id in get_roles():
            r_serv_db.srem(f'ail:users:role:{role_id}', self.user_id)
        user_token = self.get_api_key()
        if user_token:
            r_serv_db.hdel('ail:users:tokens', user_token)
        user_org = self.get_org()
        if user_org:
            org = ail_orgs.Organisation(user_org)
            org.remove_user(self.user_id)
        r_serv_db.delete(f'ail:user:metadata:{self.user_id}')
        r_serv_db.hdel('ail:users:all', self.user_id)


#### API ####

def api_get_users_meta():
    meta = {'users': []}
    options = {'api_key', 'creator', 'created_at', 'is_logged', 'last_edit', 'last_login', 'last_seen', 'last_seen_api', 'org', 'org_name', 'role', '2fa', 'otp_setup'}
    for user_id in get_users():
        user = AILUser(user_id)
        meta['users'].append(user.get_meta(options=options))
    return meta

def api_get_user_profile(user_id):
    options = {'api_key', 'role', '2fa', 'org', 'org_name'}
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    meta = user.get_meta(options=options)
    return meta, 200

def api_get_user_hotp(user_id, nb=20):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    hotp = get_user_hotp_code(user_id, nb=nb)
    return hotp, 200

def api_logout_user(admin_id, user_id, ip_address, user_agent):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    access_logger.info(f'Logout user {user_id}', extra={'user_id': admin_id, 'ip_address': ip_address, 'user_agent': user_agent})
    return user.kill_session(), 200

def api_logout_users(admin_id, ip_address, user_agent):
    access_logger.info('Logout all users', extra={'user_id': admin_id, 'ip_address': ip_address, 'user_agent': user_agent})
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

def api_enable_user_otp(user_id, ip_address):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    if user.is_2fa_enabled():
        return {'status': 'error', 'reason': 'User OTP is already setup'}, 400
    delete_user_otp(user_id)
    enable_user_2fa(user_id)
    return user_id, 200

def api_disable_user_otp(user_id, ip_address):
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

def api_reset_user_otp(admin_id, user_id, ip_address): # TODO LOGS
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

def api_create_user_api_key_self(user_id, ip_address, user_agent):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    access_logger.info('New api key', extra={'user_id': user_id, 'ip_address': ip_address, 'user_agent': user_agent})
    return user.new_api_key(), 200

def api_create_user_api_key(user_id, admin_id, ip_address, user_agent):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    access_logger.info(f'New api key for user {user_id}', extra={'user_id': admin_id, 'ip_address': ip_address, 'user_agent': user_agent})
    return user.new_api_key(), 200

def api_create_user(admin_id, ip_address, user_agent, user_id, password, org_uuid, role, otp):
    user = AILUser(user_id)
    if not ail_orgs.exists_org(org_uuid):
        return {'status': 'error', 'reason': 'Unknown Organisation'}, 400
    if not exists_role(role):
        return {'status': 'error', 'reason': 'Unknown User Role'}, 400
    if not user.exists():
        create_user(user_id, password=password, admin_id=admin_id, org_uuid=org_uuid, role=role, otp=otp)
        access_logger.info(f'Create user {user_id}', extra={'user_id': admin_id, 'ip_address': ip_address, 'user_agent': user_agent})
        return user_id, 200
    # Edit
    else:
        edit_user(admin_id, user_id, password, chg_passwd=True, org_uuid=org_uuid, edit_otp=True, otp=otp, role=role)
        access_logger.info(f'Edit user {user_id}', extra={'user_id': admin_id, 'ip_address': ip_address, 'user_agent': user_agent})
        return user_id, 200

def api_change_user_self_password(user_id, password):
    if not check_password_strength(password):
        return {'status': 'error', 'reason': 'Invalid Password'}, 400
    password_hash = hashing_password(password)
    user = AILUser(user_id)
    user.edit_password(password_hash, chg_passwd=False)
    return user_id, 200

def api_delete_user(user_id, admin_id, ip_address, user_agent):
    user = AILUser(user_id)
    if not user.exists():
        return {'status': 'error', 'reason': 'User not found'}, 404
    access_logger.info(f'Delete user {user_id}', extra={'user_id': admin_id, 'ip_address': ip_address, 'user_agent': user_agent})
    return user.delete(), 200

########################################################################################################################

def _fix_user_lowercase(user_id):  # TODO CHANGE EDIT DATE
    l_user_id = user_id.lower()

    if user_id != l_user_id:
        kill_session_user(user_id)

        # role
        role = get_user_role(user_id)
        for role_id in get_roles():
            r_serv_db.srem(f'ail:users:role:{role_id}', user_id)
        set_user_role(l_user_id, role)

        # token
        token = get_user_token(user_id)
        r_serv_db.hdel('ail:users:tokens', token)
        r_serv_db.hset('ail:users:tokens', token, l_user_id)

        # org
        org = ail_orgs.Organisation(get_user_org(user_id))
        org.remove_user(user_id)

        # meta
        try:
            r_serv_db.rename(f'ail:user:metadata:{user_id}', f'ail:user:metadata:{l_user_id}')
        except Exception:
            pass

        # org
        org.add_user(l_user_id)

        # sets
        p_hash = get_user_passwd_hash(user_id)
        r_serv_db.hdel('ail:users:all', user_id)
        r_serv_db.hset('ail:users:all', l_user_id, p_hash)

        date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        r_serv_db.hset(f'ail:user:metadata:{l_user_id}', 'last_edit', date)

########################################################################################################################

#### ROLES ####

def get_roles():
    return r_serv_db.smembers('ail:roles')

def _create_roles():
    r_serv_db.sadd('ail:roles', 'admin')
    r_serv_db.sadd('ail:roles', 'read_only')
    r_serv_db.sadd('ail:roles', 'user')
    r_serv_db.sadd('ail:roles', 'user_no_api')
    r_serv_db.sadd('ail:roles', 'contributor')

def get_default_role():
    return 'read_only'

def is_in_role(user_id, role):
    return r_serv_db.sismember(f'ail:users:role:{role}', user_id)

def _get_users_roles_list():
    return ['read_only', 'user_no_api', 'user', 'org_admin', 'admin']

def _get_users_roles_dict():
    return {
        'read_only':    ['read_only'],
        'user_no_api':  ['read_only', 'user_no_api'],
        'user':         ['read_only', 'user_no_api', 'user'],
        'org_admin':    ['read_only', 'user_no_api', 'user', 'org_admin'],
        'admin':        ['read_only', 'user_no_api', 'user', 'org_admin', 'admin'],
    }

def exists_role(role):
    return role in _get_users_roles_list()

def set_user_role(user_id, role):
    roles = _get_users_roles_dict()
    # set role
    for role_to_add in roles[role]:
        r_serv_db.sadd(f'ail:users:role:{role_to_add}', user_id)
    r_serv_db.hset(f'ail:user:metadata:{user_id}', 'role', role)

def check_user_role_integrity(user_id):
    return True
    roles = _get_users_roles_dict()
    user_role = get_user_role(user_id)
    if user_role not in roles:
        return False
    # check if is in role
    for r in roles[user_role]:
        if not r_serv_db.sismember(f'ail:users:role:{r}', user_id):
            print(r)
            return False
    for r in list(set(_get_users_roles_list()) - set(roles[user_role])):
        if r_serv_db.sismember(f'ail:users:role:{r}', user_id):
            print(r)
            return False
    return True

# TODO
# ACL:
#       - mass tag correlation graph
#
#
#
#
