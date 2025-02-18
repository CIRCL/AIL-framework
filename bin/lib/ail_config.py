#!/usr/bin/python3

import os
import sys

from abc import ABC

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_users
from lib.ail_core import generate_uuid5, is_valid_uuid_v5
from lib.ConfigLoader import ConfigLoader

# Config
config_loader = ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None


# SIMPLE CONFIG
def get_user_simple_config(user_id, name):
    return r_serv_db.hget(f'ail:user:settings:{user_id}', name)

def set_user_simple_config(user_id, name, value):
    return r_serv_db.hset(f'ail:user:settings:{user_id}', name, value)

def remove_user_simple_config(user_id, name):
    return r_serv_db.hdel(f'ail:user:settings:{user_id}', name)

# SET
def get_user_set_names():
    return set()

def get_user_set_config(user_id, name):
    return r_serv_db.smembers(f'ail:user:set:settings:{name}:{user_id}')

def add_user_set_config(user_id, name, value):
    return r_serv_db.sadd(f'ail:user:set:settings:{name}:{user_id}', value)

def remove_user_set_config(user_id, name, value):
    return r_serv_db.srem(f'ail:user:set:settings:{name}:{user_id}', value)

def delete_user_set_config(user_id, name):
    return r_serv_db.delete(f'ail:user:set:settings:{name}:{user_id}')

# OBJECT
def get_user_obj_names():
    return {'misp'}

def _get_user_obj_config(user_id, obj_name, field_name):
    field = f'{obj_name}:{field_name}'
    return get_user_simple_config(user_id, field)

def _set_user_obj_config(user_id, obj_name, field_name, value):
    field = f'{obj_name}:{field_name}'
    return set_user_simple_config(user_id, field, value)

def _remove_user_obj_config(user_id, obj_name, field_name):
    field = f'{obj_name}:{field_name}'
    return remove_user_simple_config(user_id, field)


class AbstractUserConfigUniqObject(ABC):
    def __init__(self, obj_name, fields_names, user_id):
        self.name = obj_name
        self.fields_names = fields_names
        self.user_id = user_id

    def get_config_field(self, field_name):
        return _get_user_obj_config(self.user_id, self.name, field_name)

    def get_config(self):
        obj_config = {}
        for field_name in self.fields_names:
            conf = _get_user_obj_config(self.user_id, self.name, field_name)
            obj_config[field_name] = conf
        return obj_config

    def set_config_field(self, field_name, value):
        _set_user_obj_config(self.user_id, self.name, field_name, value)

    def set_config(self, config):
        obj_config = {}
        for field in config:
            field_name = field
            value = config[field]
            _set_user_obj_config(self.user_id, self.name, field_name, value)
        return obj_config

# Objects

class AbstractUserConfigObject(ABC):
    def __init__(self, name, fields_names, uuidv5, user_id):
        self.name = name
        self.fields_names = fields_names
        self.user_id = user_id
        self.uuid = uuidv5

    def exists(self):
        return r_serv_db.sismember(f'ail:user:obj:settings:{self.name}:{self.user_id}', self.uuid)

    def get_uuid(self):
        return self.uuid

    def get_name(self):
        return self.name

    def get_key_name(self):
        return f'{self.name}:{self.uuid}'

    def get_config_field(self, field_name):
        return _get_user_obj_config(self.user_id, self.get_key_name(), field_name)

    def get_config(self):
        obj_config = {}
        for field_name in self.fields_names:
            conf = _get_user_obj_config(self.user_id, self.get_key_name(), field_name)
            obj_config[field_name] = conf
        return obj_config

    def set_config_field(self, field_name, value):
        r_serv_db.sadd(f'ail:user:obj:settings:{self.name}:{self.user_id}', self.uuid)
        _set_user_obj_config(self.user_id, self.get_key_name(), field_name, value)

    def set_config(self, config):
        r_serv_db.sadd(f'ail:user:obj:settings:{self.name}:{self.user_id}', self.uuid)
        obj_config = {}
        for field in config:
            field_name = field
            value = config[field]
            _set_user_obj_config(self.user_id, self.get_key_name(), field_name, value)
        return obj_config

    def delete(self):
        for field in self.fields_names:
            _remove_user_obj_config(self.user_id, self.get_key_name(), field)
        r_serv_db.srem(f'ail:user:obj:settings:{self.name}:{self.user_id}', self.uuid)

def get_user_config_objs(name, user_id):
    return r_serv_db.smembers(f'ail:user:obj:settings:{name}:{user_id}')

def delete_user_config_objs(name, user_id):
    r_serv_db.delete(f'ail:user:obj:settings:{name}:{user_id}')

def delete_user_config(user_id):
    for set_name in get_user_set_names():
        delete_user_set_config(user_id, set_name)
    for obj_name in get_user_obj_names():
        delete_user_config_objs(obj_name, user_id)
    r_serv_db.delete(f'ail:user:settings:{user_id}')

#### MISP ####

class UserConfigMISP(AbstractUserConfigObject):
    def __init__(self, uuidv5, user_id):
        super().__init__(name='misp', fields_names={'url', 'key', 'ssl'}, uuidv5=uuidv5, user_id=user_id)

    def get_description(self):
        return self.get_config_field('description')

    def get_url(self):
        return self.get_config_field('url')

    def get_meta(self):
        meta = {'uuid': self.uuid,
                'url': self.get_url(),
                'key': self.get_config_field('key'),
                'ssl': self.get_config_field('ssl') == 'True',
                'description': self.get_description()}
        return meta


def get_user_config_misps(user_id):
    meta = []
    for uuidv5 in get_user_config_objs('misp', user_id):
        misp_cong = UserConfigMISP(uuidv5, user_id)
        meta.append(misp_cong.get_meta())
    return meta

def create_user_config_misp(user_id, url, key, ssl, description):
    uuidv5 = generate_uuid5(f'{url}|{key}')
    misp_cong = UserConfigMISP(uuidv5, user_id)
    if misp_cong.exists():
        return uuidv5
    else:
        ssl = bool(ssl)
        misp_cong.set_config({'url': url, 'key': key, 'ssl': str(ssl), 'description': description})

def edit_user_config_misp(uuidv5, user_id, url, key, ssl, description):
    new_uuidv5 = generate_uuid5(f'{url}|{key}')
    if new_uuidv5 != uuidv5:
        UserConfigMISP(uuidv5, user_id).delete()
        return create_user_config_misp(user_id, url, key, ssl, description)
    else:
        misp_conf = UserConfigMISP(new_uuidv5, user_id)
        misp_conf.set_config_field('ssl', str(ssl))
        misp_conf.set_config_field('description', description)
        return new_uuidv5

## ## API ## ##

def get_user_misps_selector(user_id):
    misps = []
    for misp_uuid in get_user_config_objs('misp', user_id):
        misp = UserConfigMISP(misp_uuid, user_id)
        name = misp.get_description()
        if not name:
            misps.append(f'{misp_uuid}:{misp.get_url()}')
        else:
            misps.append(f'{misp_uuid}:{misp.get_url()} - {name}')
    return misps

def api_get_user_misps(user_id, uuidv5):
    misp_cong = UserConfigMISP(uuidv5, user_id)
    if not misp_cong.exists():
        return {'status': 'error', 'reason': 'Unknown uuid'}, 404
    else:
        return misp_cong.get_meta(), 200

def api_edit_user_misp(user_id, data):
    conf_uuid = data.get('uuid')
    url = data.get('url')
    key = data.get('key')
    misp_ssl = data.get('ssl')
    if misp_ssl:
        misp_ssl = True
    else:
        misp_ssl = False
    description = data.get('description')
    if description:
        if len(description) > 2000:
            description = description[:2000]

    if not url:
        return {'status': 'error', 'reason': 'missing misp url'}, 400
    if not key:
        return {'status': 'error', 'reason': 'missing misp key'}, 400

    if len(url) > 2000:
        url = url[:2000]
    if len(key) > 200:
        key = key[:200]

    if not ail_users.exists_user(user_id):
        return {'status': 'error', 'reason': 'Unknown user'}, 400

    if conf_uuid:
        if not is_valid_uuid_v5(conf_uuid):
            return {'status': 'error', 'reason': 'Unknown user'}, 400
        else:
            return edit_user_config_misp(conf_uuid, user_id, url, key, misp_ssl, description), 200
    else:
        return create_user_config_misp(user_id, url, key, misp_ssl, description), 200

def api_delete_user_misp(user_id, data):
    conf_uuid = data.get('uuid')
    if not is_valid_uuid_v5(conf_uuid):
        return {'status': 'error', 'reason': 'Unknown user'}, 400
    else:
        misp = UserConfigMISP(conf_uuid, user_id)
        misp.delete()
        return conf_uuid, 200

## -- API -- ##

## --MISP-- ##





