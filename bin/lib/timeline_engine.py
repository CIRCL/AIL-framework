#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from uuid import uuid4

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_meta = config_loader.get_db_conn("Kvrocks_Timeline")
config_loader = None

# CORRELATION_TYPES_BY_OBJ = {
#     "chat": ["item", "username"],  # item ???
#     "cookie-name": ["domain"],
#     "cryptocurrency": ["domain", "item"],
#     "cve": ["domain", "item"],
#     "decoded": ["domain", "item"],
#     "domain": ["cve", "cookie-name", "cryptocurrency", "decoded", "etag", "favicon", "hhhash", "item", "pgp", "title", "screenshot", "username"],
#     "etag": ["domain"],
#     "favicon": ["domain", "item"],
#     "hhhash": ["domain"],
#     "item": ["chat", "cve", "cryptocurrency", "decoded", "domain", "favicon", "pgp", "screenshot", "title", "username"],
#     "pgp": ["domain", "item"],
#     "screenshot": ["domain", "item"],
#     "title": ["domain", "item"],
#     "username": ["chat", "domain", "item"],
# }
#
# def get_obj_correl_types(obj_type):
#     return CORRELATION_TYPES_BY_OBJ.get(obj_type)

# def sanityze_obj_correl_types(obj_type, correl_types):
#     obj_correl_types = get_obj_correl_types(obj_type)
#     if correl_types:
#         correl_types = set(correl_types).intersection(obj_correl_types)
#     if not correl_types:
#         correl_types = obj_correl_types
#         if not correl_types:
#             return []
#     return correl_types

# TODO rename all function + add missing parameters

def get_bloc_obj_global_id(bloc):
    return r_meta.hget('hset:key', bloc)

def set_bloc_obj_global_id(bloc, global_id):
    return r_meta.hset('hset:key', bloc, global_id)

def get_bloc_timestamp(bloc, position):
    return r_meta.zscore('key', f'{position}:{bloc}')

def add_bloc(global_id, timestamp, end=None):
    if end:
        timestamp_end = end
    else:
        timestamp_end = timestamp
    new_bloc = str(uuid4())
    r_meta.zadd('key', {f'start:{new_bloc}': timestamp, f'end:{new_bloc}': timestamp_end})
    set_bloc_obj_global_id(new_bloc, global_id)
    return new_bloc

def _update_bloc(bloc, position, timestamp):
    r_meta.zadd('key', {f'{position}:{bloc}': timestamp})

# score = timestamp
def get_nearest_bloc_inf(timestamp):
    return r_meta.zrevrangebyscore('key', timestamp, 0, num=1)

def get_nearest_bloc_sup(timestamp):
    return r_meta.zrangebyscore('key', timestamp, 0, num=1)

#######################################################################################

def add_timestamp(timestamp, obj_global_id):
    inf = get_nearest_bloc_inf(timestamp)
    sup = get_nearest_bloc_sup(timestamp)
    if not inf and not sup:
        # create new bloc
        new_bloc = add_bloc(obj_global_id, timestamp)
        return new_bloc
    # timestamp < first_seen
    elif not inf:
        sup_pos, sup_id = inf.split(':')
        sup_obj = get_bloc_obj_global_id(sup_pos)
        if sup_obj == obj_global_id:
            _update_bloc(sup_id, 'start', timestamp)
        # create new bloc
        else:
            new_bloc = add_bloc(obj_global_id, timestamp)
            return new_bloc

    # timestamp > first_seen
    elif not sup:
        inf_pos, inf_id = inf.split(':')
        inf_obj = get_bloc_obj_global_id(inf_id)
        if inf_obj == obj_global_id:
            _update_bloc(inf_id, 'end', timestamp)
        # create new bloc
        else:
            new_bloc = add_bloc(obj_global_id, timestamp)
            return new_bloc

    else:
        inf_pos, inf_id = inf.split(':')
        sup_pos, sup_id = inf.split(':')
        inf_obj = get_bloc_obj_global_id(inf_id)

        if inf_id == sup_id:
            # reduce bloc + create two new bloc
            if obj_global_id != inf_obj:
                # get end timestamp
                sup_timestamp = get_bloc_timestamp(sup_id, 'end')
                # reduce original bloc
                _update_bloc(inf_id, 'end', timestamp - 1)
                # Insert new bloc
                new_bloc = add_bloc(obj_global_id, timestamp)
                # Recreate end of the first bloc by a new bloc
                add_bloc(inf_obj, timestamp + 1, end=sup_timestamp)
                return new_bloc

            # timestamp in existing bloc
            else:
                return inf_id

        # different blocs: expend sup/inf bloc or create a new bloc if
        elif inf_pos == 'end' and sup_pos == 'start':
            # Extend inf bloc
            if obj_global_id == inf_obj:
                _update_bloc(inf_id, 'end', timestamp)
                return inf_id

            sup_obj = get_bloc_obj_global_id(sup_pos)
            # Extend sup bloc
            if obj_global_id == sup_obj:
                _update_bloc(sup_id, 'start', timestamp)
                return sup_id

            # create new bloc
            new_bloc = add_bloc(obj_global_id, timestamp)
            return new_bloc

        # inf_pos == 'start' and sup_pos == 'end'
        # else raise error ???






