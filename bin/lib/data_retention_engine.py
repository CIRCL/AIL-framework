#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

def get_first_object_date(object_type, subtype, field=''):
    first_date = r_serv_db.zscore('objs:first_date', f'{object_type}:{subtype}:{field}')
    if not first_date:
        first_date = 99999999
    return int(first_date)

def get_last_object_date(object_type, subtype, field=''):
    last_date = r_serv_db.zscore('objs:last_date', f'{object_type}:{subtype}:{field}')
    if not last_date:
        last_date = 0
    return int(last_date)

def _set_first_object_date(object_type, subtype, date, field=''):
    return r_serv_db.zadd('objs:first_date', f'{object_type}:{subtype}:{field}', date)

def _set_last_object_date(object_type, subtype, date, field=''):
    return r_serv_db.zadd('objs:last_date', f'{object_type}:{subtype}:{field}', date)

def update_first_object_date(object_type, subtype, date, field=''):
    first_date = get_first_object_date(object_type, subtype, field=field)
    if int(date) < first_date:
        _set_first_object_date(object_typel, subtype, date, field=field)
        return date
    else:
        return first_date

def update_last_object_date(object_type, subtype, date, field=''):
    last_date = get_last_object_date(object_type, subtype, field=field)
    if int(date) > last_date:
        _set_last_object_date(object_type, subtype, date, field=field)
        return date
    else:
        return last_date

def update_object_date(object_type, subtype, date, field=''):
    update_first_object_date(object_type, subtype, date, field=field)
    update_last_object_date(object_type, subtype, date, field=field)


###############################################################
