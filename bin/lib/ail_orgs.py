#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from datetime import datetime

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_logger
from lib.ail_core import is_valid_uuid_v4, generate_uuid
from lib.ConfigLoader import ConfigLoader


# LOGS

access_logger = ail_logger.get_access_config()

# Config
config_loader = ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
r_data = config_loader.get_db_conn("Kvrocks_DB")  # TODO MOVE DEFAULT DB
# r_cache = config_loader.get_redis_conn("Redis_Cache")

config_loader = None

# #### PART OF ORGANISATION ####
# from abc import ABC, abstractmethod
#
# class AbstractObject(ABC):
#
#     @abstractmethod
#     def get_org(self):
#         pass
#
#
#     ## LEVEL ##
#
#     @abstractmethod
#     def get_level(self):
#         pass
#
#     @abstractmethod
#     def set_level(self):
#         pass
#
#     @abstractmethod
#     def reset_level(self):
#         pass

#### ORGANISATIONS ####

# TODO EDIT

# TODO DELETE CHECK
# TODO DELETE OBJS

# TODO ORG View

# TODO TAGS
# TODO TAGS USERS ????

# TODO Check if ORG name is UNIQUE

def get_orgs():
    return r_serv_db.smembers(f'ail:orgs')

def is_user_in_org(org_uuid, user_id):
    return r_serv_db.sadd(f'ail:org:{org_uuid}:users', user_id)

#### ORGANISATION ####

class Organisation:

    def __init__(self, org_uuid):
        self.uuid = org_uuid

    def exists(self):
        return r_serv_db.exists(f'ail:org:{self.uuid}')

    def _get_field(self, field):
        return r_serv_db.hget(f'ail:org:{self.uuid}', field)

    def _set_fields(self, field, value):
        return r_serv_db.hset(f'ail:org:{self.uuid}', field, value)

    def get_uuid(self):
        return self.uuid

    def get_date_created(self):
        return self._get_field('date_created')

    def get_date_modified(self):
        return self._get_field('date_modified')

    def get_description(self):
        return self._get_field('description')

    def get_name(self):
        return self._get_field('name')

    def get_nationality(self):
        return self._get_field('nationality')

    def get_creator(self):
        return self._get_field('creator')

    def get_org_type(self):
        return self._get_field('type')

    def get_sector(self):
        return self._get_field('sector')

    def get_tags(self):  # TODO
        pass

    def get_logo(self):
        pass

    def get_users(self):
        return r_serv_db.smembers(f'ail:org:{self.uuid}:users')

    def get_nb_users(self):
        return r_serv_db.scard(f'ail:org:{self.uuid}:users')

    def get_meta(self, options=set()):
        meta = {'uuid': self.uuid}
        if 'name' in options:
            meta['name'] = self._get_field('name')
        if 'description' in options:
            meta['description'] = self._get_field('description')
        if 'creator' in options:
            meta['creator'] = self._get_field('creator')
        if 'date_created' in options:
            meta['date_created'] = self._get_field('date_created')
        return meta

    def add_user(self, user_id):
        r_serv_db.sadd(f'ail:org:{self.uuid}:users', user_id)
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'org', self.uuid)

    def remove_user(self, user_id):
        r_serv_db.srem(f'ail:org:{self.uuid}:users', user_id)
        r_serv_db.hdel(f'ail:user:metadata:{user_id}', 'org')

    def remove_users(self):
        for user_id in self.get_users():
            self.remove_user(user_id)

    def create(self, creator, name, description=None, nationality=None, sector=None, org_type=None, logo=None):
        r_serv_db.sadd(f'ail:orgs', self.uuid)

        self._set_fields('creator', creator)
        self._set_fields('name', name)
        self._set_fields('description', description)
        if nationality:
            self._set_fields('nationality', nationality)
        if sector:
            self._set_fields('sector', sector)
        if org_type:
            self._set_fields('type', org_type)
        # if logo:

        current = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self._set_fields('date_created', current)
        self._set_fields('date_modified', current)

    def edit(self):
        pass

    def delete(self):  # TODO CHANGE ACL ASSOCIATED WITH ORGS -> Tracker, Investigation, objects, ...
        self.remove_users()
        r_serv_db.delete(f'ail:org:{self.uuid}')
        r_serv_db.srem(f'ail:orgs', self.uuid)


def exists_org(org_uuid):
    return r_serv_db.exists(f'ail:org:{org_uuid}')

def create_org(name, description, uuid=None, nationality=None, sector=None, org_type=None, logo=None): # contacts ?????
    if uuid is None:
        uuid = generate_uuid()
    else:
        if exists_org(uuid):
            raise Exception('Organisation already exists')  # TODO CUSTOM ERROR

    org = Organisation(uuid)
    org.create(name, description, nationality=nationality, sector=sector, org_type=org_type, logo=logo)

def get_org_objs_by_type(org_uuid, obj_type):
    return r_serv_db.smembers(f'org:{org_uuid}:{obj_type}')

def add_obj_to_org(org_uuid, obj_type, obj_gid):  # ADD set UUID -> object types ???
    r_serv_db.sadd(f'org:{org_uuid}:{obj_type}', obj_gid)

def remove_obj_to_org(org_uuid, obj_type, obj_gid):
    r_serv_db.srem(f'org:{org_uuid}:{obj_type}', obj_gid)


## --ORGANISATION-- ##

def check_access_acl(obj, user_org, is_admin=False):
    if is_admin:
        return True
    return obj.get_org() == user_org

#### API ####

def api_get_orgs_meta():
    meta = {'orgs': []}
    options = {'date_created', 'description', 'name'}
    for org_uuid in get_orgs():
        org = Organisation(org_uuid)
        meta['orgs'].append(org.get_meta(options=options))
    return meta

def api_create_org(creator, org_uuid, name, ip_address, description=None):
    if not is_valid_uuid_v4(org_uuid):
        return {'status': 'error', 'reason': 'Invalid UUID'}, 400
    if exists_org(org_uuid):
        return {'status': 'error', 'reason': 'Org already exists'}, 400

    org = Organisation(org_uuid)
    org.create(creator, name, description=description)
    access_logger.info(f'Created org {org_uuid}', extra={'user_id': creator, 'ip_address': ip_address})
    return org.get_uuid(), 200

def api_delete_org(org_uuid, admin_id, ip_address):  # TODO check if nothing is linked to this org
    if not exists_org(org_uuid):
        return {'status': 'error', 'reason': 'Org not found'}, 404
    access_logger.warning(f'Deleted org {org_uuid}', extra={'user_id': admin_id, 'ip_address': ip_address})
    org = Organisation(org_uuid)
    org.delete()
    return org_uuid, 200


# if __name__ == '__main__':
#     user_id = 'admin@admin.test'
#     instance_name = 'AIL TEST'
#     delete_user_otp(user_id)
#     # q = get_user_otp_qr_code(user_id, instance_name)
#     # print(q)
