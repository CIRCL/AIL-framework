#!/usr/bin/python3

"""
Config save in DB
===================


"""

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
from lib import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_db = config_loader.get_redis_conn("_DB")
config_loader = None

#### TO PUT IN CONFIG
# later => module timeout
#
## data retention
#########################


ail_config = {
    "crawler": {
        "enable_har_by_default": {
            "default": False,
            "type": bool,
            "info": "Enable HAR by default"
        },
        "enable_screenshot_by_default": {
            "default": True,
            "type": bool,
            "info": "Enable screenshot by default"
        },
        "depth_limit": {
            "default": 1,
            "type": int,
            "info": "Maximum number of url depth"
        },
        "closespider_pagecount": {
            "default": 50,
            "type": int,
            "info": "Maximum number of pages"
        },
        "user_agent": {
            "default": 50,
            "type": str,
            "info": "User agent used by default"
        },
        "timeout": {
            "default": 30,
            "type": int,
            "info": "Crawler connection timeout"
        },
    },
    "misp": {
        "url": {
            "default": "https://localhost:8443/",
            "type": str,
            "info": "Crawler connection timeout"
        },
        "key": {
            "default": "",
            "type": str,
            "info": "Crawler connection timeout"
        },
        "verifycert": {
            "default": True,
            "type": bool,
            "info": "Crawler connection timeout"
        },
    }
}

# The MISP auth key can be found on the MISP web interface under the automation section

def get_config_value(section, field, value):
    return r_serv_db.hget(f'ail:config:global:{section}', field, value)

def get_config_default_value(section, field, value):
    return ail_config[section][field]['default']

def get_config_type(section, field, value):
    return ail_config[section][field]['type']

def get_config_info(section, field, value):
    return ail_config[section][field]['info']

def save_config(section, field, value):
    if section in ail_config:
        if is_valid_type(value, section, field, value_type=value_type):
            # if value_type in ['list', 'set', 'dict']:
            #     pass
            # else:
            r_serv_db.hset(f'ail:config:global:{section}', field, value)


config_documentation = {

}

default_config = {

}

def get_default_config():
    return default_config

def get_default_config_value(section, field):
    return default_config[section][field]




#### DEFAULT CONFIG ####

#### CONFIG TYPE ####
# CONFIG DOC
config_type = {

}

# # TODO: add set, dict, list and select_(multiple_)value
def is_valid_type(obj, section, field, value_type=None):
    res = isinstance(obj, get_config_type(section, field))
    return res

# # TODO: ###########################################################
def reset_default_config():
    for section in config_type:

    pass

def set_default_config(section, field):
    save_config(section, field, get_default_config_value(section, field))

def get_all_config_sections():
    return list(get_default_config())

def get_all_config_fields_by_section(section):
    return list(get_default_config()[section])

def get_config(section, field):
    # config field don't exist
    if not r_serv_db.hexists(f'config:global:{section}', field):
        set_default_config(section, field)
        return get_default_config_value(section, field)

    # load default config section
    if not r_serv_db.exists('config:global:{}'.format(section)):
        save_config(section, field, get_default_config_value(section, field))
        return get_default_config_value(section, field)

    return r_serv_db.hget(f'config:global:{section}', field)

def get_config_dict_by_section(section):
    config_dict = {}
    for field in get_all_config_fields_by_section(section):
        config_dict[field] = get_config(section, field)
    return config_dict


# check config value + type
def check_integrity():
    pass


def get_field_full_config(section, field):
    dict_config = {}
    dict_config['value'] = get_config(section, field)
    dict_config['type'] = get_config_type(section, field)
    dict_config['info'] = get_config_documentation(section, field)
    return dict_config

def get_full_config_by_section(section):
    dict_config = {}
    for field in get_all_config_fields_by_section(section):
        dict_config[field] = get_field_full_config(section, field)
    return dict_config

def get_full_config():
    dict_config = {}
    for section in get_all_config_sections():
        dict_config[section] = get_full_config_by_section(section)
    return dict_config

if __name__ == '__main__':
    res = get_full_config()
    print(res)
