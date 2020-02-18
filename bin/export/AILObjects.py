#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_objects = config_loader.get_redis_conn("ARDB_Objects")
config_loader = None

def create_map_obj_uuid_golbal_id(obj_uuid, global_id):
    r_serv_objects.sadd('all_object:uuid', obj_uuid)
    r_serv_objects.sadd('all_object:global_id', global_id)
    r_serv_objects.sadd('object:map:uuid_id:{}'.format(obj_uuid), global_id)
    r_serv_objects.sadd('object:map:id_uuid:{}'.format(global_id), obj_uuid)
