#!/usr/bin/python3

"""
Config save in DB
===================


"""

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_db = config_loader.get_redis_conn("ARDB_DB")
config_loader = None

#### TO PUT IN CONFIG
# later => module timeout
#
## data retention
#########################

default_config = {
    "crawler": {
        "enable_har_by_default": False,
        "enable_screenshot_by_default": True,
        "default_depth_limit": 1,
        "default_closespider_pagecount": 50,
        "default_user_agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0",
        "default_timeout": 30
    }
}

def get_default_config():
    return default_config

def get_default_config_value(section, field):
    return default_config[section][field]

config_type = {
    # crawler config
    "crawler": {
        "enable_har_by_default": bool,
        "enable_screenshot_by_default": bool,
        "default_depth_limit": int,
        "default_closespider_pagecount": int,
        "default_user_agent": str,
        "default_timeout": int
    }
}

def get_config_type(section, field):
    return config_type[section][field]

# # TODO: add set, dict, list and select_(multiple_)value
def is_valid_type(obj, section, field, value_type=None):
    res = isinstance(obj, get_config_type(section, field))
    return res

def reset_default_config():
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

def save_config(section, field, value, value_type=None): ###########################################
    if section in default_config:
        if is_valid_type(value, section, field, value_type=value_type):
            if value_type in ['list', 'set', 'dict']:
                pass
            else:
                r_serv_db.hset(f'config:global:{section}', field, value)
                # used by check_integrity
                r_serv_db.sadd('config:all_global_section', field, value)

# check config value + type
def check_integrity():
    pass


config_documentation = {
    "crawler": {
        "enable_har_by_default": 'Enable HAR by default',
        "enable_screenshot_by_default": 'Enable screenshot by default',
        "default_depth_limit": 'Maximum number of url depth',
        "default_closespider_pagecount": 'Maximum number of pages',
        "default_user_agent": "User agent used by default",
        "default_timeout": "Crawler connection timeout"
    }
}

def get_config_documentation(section, field):
    return config_documentation[section][field]

# def conf_view():
#     class F(MyBaseForm):
#         pass
#
#     F.username = TextField('username')
#     for name in iterate_some_model_dynamically():
#         setattr(F, name, TextField(name.title()))
#
#     form = F(request.POST, ...)

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
