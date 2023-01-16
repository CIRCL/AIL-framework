#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_obj = config_loader.get_db_conn("Kvrocks_Objects")
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None

# TODO HOW TO HANDLE SCREENSHOTS ????
# SCREENSHOT ID -> MEMBER OF ITEMS -> DATES
# META SCREENSHOT -> NB DOMAINS + FIRST/LAST SEEN ???

# TAG /!\ DIFF TAG CREDENTIAL ITEM != DOMAIN:CREDENTIAL
#   -> IN OBJECT TYPE ?????
# OR SPECIAL FIRST SEEN / LAST SEEN IN TAG LIB


# DOMAIN -> subtype = domain type

# TAG -> type = "TAG"
# TAG -> subtype = f"OBJ:{tag}"

def load_obj_date_first_last():
    # LOAD FIRST DATE
    dates = r_obj.hgetall(f'date:first')
    for str_row in dates:
        obj_type, subtype = str_row.split(':', 1)
        date = dates[str_row]
        _set_obj_date_first(date, obj_type, subtype=subtype)
    # LOAD LAST DATE
    dates = r_obj.hgetall(f'date:last')
    for str_row in dates:
        obj_type, subtype = str_row.split(':', 1)
        date = dates[str_row]
        _set_obj_date_last(date, obj_type, subtype=subtype)


# MAKE IT WORK WITH TAGS
def get_obj_date_first(obj_type, subtype='', r_int=False):
    first = r_cache.hget(f'date:first', f'{obj_type}:{subtype}')
    if not first:
        first = r_obj.hget(f'date:first', f'{obj_type}:{subtype}')
    if r_int:
        if not first:
            return 99999999
        else:
            return int(first)
    return first

def get_obj_date_last(obj_type, subtype='', r_int=False):
    last = r_cache.hget(f'date:last', f'{obj_type}:{subtype}')
    if not last:
        last = r_obj.hget(f'date:last', f'{obj_type}:{subtype}')
    if r_int:
        if not last:
            return 0
        else:
            return int(last)
    return last

# FIRST
def _set_obj_date_first(date, obj_type, subtype=''):
    r_cache.hset(f'date:first', f'{obj_type}:{subtype}', date)

def set_obj_date_first(date, obj_type, subtype=''):
    _set_obj_date_first(date, obj_type, subtype=subtype)
    r_obj.hset(f'date:first', f'{obj_type}:{subtype}', date)

# LAST
def _set_obj_date_last(date, obj_type, subtype=''):
    r_cache.hset(f'date:last', f'{obj_type}:{subtype}', date)

def set_obj_date_last(date, obj_type, subtype=''):
    _set_obj_date_last(date, obj_type, subtype=subtype)
    r_obj.hset(f'date:last', f'{obj_type}:{subtype}', date)

def update_obj_date(date, obj_type, subtype=''):
    date = int(date)
    first = get_obj_date_first(obj_type, subtype=subtype, r_int=True)
    last = get_obj_date_last(obj_type, subtype=subtype, r_int=True)
    if date < first:
        set_obj_date_first(date, obj_type, subtype=subtype)
    if date > last:
        set_obj_date_last(date, obj_type, subtype=subtype)


if __name__ == '__main__':
    print(r_obj.hgetall(f'date:first'))
    print(r_obj.hgetall(f'date:last'))
