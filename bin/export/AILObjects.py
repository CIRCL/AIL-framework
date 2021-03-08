#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import ConfigLoader
import Correlate_object

config_loader = ConfigLoader.ConfigLoader()
r_serv_objects = config_loader.get_redis_conn("ARDB_Objects")
config_loader = None

def create_map_obj_uuid_golbal_id(obj_uuid, global_id):
    r_serv_objects.sadd('all_object:uuid', obj_uuid)
    r_serv_objects.sadd('all_object:global_id', global_id)
    r_serv_objects.sadd('object:map:uuid_id:{}'.format(obj_uuid), global_id)
    r_serv_objects.sadd('object:map:id_uuid:{}'.format(global_id), obj_uuid)

def create_map_obj_event_uuid(event_uuid, global_id):
    r_serv_objects.sadd('export:all_object:event_uuid', event_uuid)
    r_serv_objects.sadd('export:all_object:global_id', global_id)
    r_serv_objects.sadd('object:map:event_id:{}'.format(event_uuid), global_id)
    r_serv_objects.sadd('object:map:id_event:{}'.format(global_id), event_uuid)

def get_user_list_of_obj_to_export(user_id, add_uuid=False):
    objs_to_export = []
    res = r_serv_objects.hgetall('user:all_objs_to_export:{}'.format(user_id))
    for global_id in res:
        dict_obj = Correlate_object.get_global_id_from_id(global_id)
        dict_obj['lvl'] = int(res[global_id])
        if add_uuid:
            obj_dict['uuid'] = str(uuid.uuid4())
        objs_to_export.append(dict_obj)
    return objs_to_export

def add_user_object_to_export(user_id, obj_type, obj_id, lvl, obj_subtype=None):
    ## TODO: check if user exist
    # # TODO: check if valid object
    # # TODO: check lvl
    global_id = Correlate_object.get_obj_global_id(obj_type, obj_id, obj_sub_type=obj_subtype)
    return r_serv_objects.hset('user:all_objs_to_export:{}'.format(user_id), global_id, lvl)

def delete_user_object_to_export(user_id, obj_type, obj_id, obj_subtype=None):
    ## TODO: check if user exist
    global_id = Correlate_object.get_obj_global_id(obj_type, obj_id, obj_sub_type=obj_subtype)
    r_serv_objects.hdel('user:all_objs_to_export:{}'.format(user_id), global_id)

def delete_all_user_object_to_export(user_id):
    ## TODO: check if user exist
    r_serv_objects.delete('user:all_objs_to_export:{}'.format(user_id))
