#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Cryptocurrency
import Pgp
import Decoded
import Domain
import Item
import Screenshot
import Correlate_object

import Import

# MISP
from pymisp import MISPEvent, MISPObject, PyMISP

# # TODO: deplace me in another fil
def get_global_id(obj_type, obj_id, obj_subtype=None):
    if obj_subtype:
        return '{}:{}:{}'.format(obj_type, obj_subtype, obj_id)
    else:
        return '{}:{}'.format(obj_type, obj_id)

# sub type
# obj type
# obj value
def get_global_id_from_misp_obj(misp_obj):
    pass

def get_misp_obj_tag(misp_obj):
    if misp_obj.attributes:
        misp_tags = misp_obj.attributes[0].tags
        tags = []
        for misp_tag in misp_tags:
            tags.append(misp_tag.name)
        return tags
    else:
        return []

def get_object_metadata(misp_obj):
    obj_meta = {}
    if 'first_seen' in misp_obj.keys():
        obj_meta['first_seen'] = misp_obj.first_seen
    if 'last_seen' in misp_obj.keys():
        obj_meta['last_seen'] = misp_obj.first_seen
    obj_meta['tags'] = get_misp_obj_tag(misp_obj)
    return obj_meta

def unpack_item_obj(map_uuid_global_id, misp_obj):
    obj_meta = get_object_metadata(misp_obj)
    obj_id = None
    io_content = None

    for attribute in misp_obj.attributes:
        if attribute.object_relation == 'raw-data':
            obj_id = attribute.value               # # TODO: sanitize
            io_content = attribute.data             # # TODO: check if type == io

    if obj_id and io_content:
        res = Item.create_item(obj_id, obj_meta, io_content)
        print(res)

    map_uuid_global_id[misp_obj.uuid] = get_global_id('item', obj_id)

def get_obj_relationship(misp_obj):
    for item in misp_obj.ObjectReference:
        print(item.to_json())



## TODO: handle multiple pgp in the same object
def unpack_obj_pgp(map_uuid_global_id, misp_obj):
    # get obj sub type
    obj_attr = misp_obj.attributes[0]
    obj_id = obj_attr.value
    if obj_attr.object_relation == 'key-id':
        obj_subtype = 'key'
    elif obj_attr.object_relation == 'user-id-name':
        obj_subtype = 'name'
    elif obj_attr.object_relation == 'user-id-email':
        obj_subtype = 'mail'

    if obj_id and obj_subtype:
        obj_meta = get_object_metadata(misp_obj)
        res = Pgp.pgp.create_correlation(obj_subtype, obj_id, obj_meta)
        print(res)

        map_uuid_global_id[misp_obj.uuid] = get_global_id('pgp', obj_id, obj_subtype=obj_subtype)

        #get_obj_relationship(misp_obj)

def unpack_obj_cryptocurrency(map_uuid_global_id, misp_obj):
    obj_id = None
    obj_subtype = None
    for attribute in misp_obj.attributes:
        if attribute.object_relation == 'address': # # TODO: handle xmr address field
            obj_id = attribute.value
        elif attribute.object_relation == 'symbol':
            obj_subtype = Cryptocurrency.get_cryptocurrency_type(attribute.value)

    # valid cryptocurrency type
    if obj_subtype and obj_id:
        print('crypto')
        print(obj_id)
        print(obj_subtype)

        obj_meta = get_object_metadata(misp_obj)
        print(obj_meta)
        res = Cryptocurrency.cryptocurrency.create_correlation(obj_subtype, obj_id, obj_meta)
        print(res)

        map_uuid_global_id[misp_obj.uuid] = get_global_id('pgp', obj_id, obj_subtype=obj_subtype)

    get_obj_relationship(misp_obj)

def get_misp_import_fct(map_uuid_global_id, misp_obj):
    #print(misp_obj.ObjectReference)
    #for item in misp_obj.ObjectReference:
    #    print(item.to_json())
    #obj_meta = get_object_metadata(misp_obj)

    #print(misp_obj.name)

    if misp_obj.name == 'ail-leak':
        unpack_item_obj(map_uuid_global_id, misp_obj)
        #print(misp_obj.to_json())
        pass
    elif misp_obj.name == 'domain-ip':
        pass
    elif misp_obj.name == 'pgp-meta':
        unpack_obj_pgp(map_uuid_global_id, misp_obj)
    elif misp_obj.name == 'coin-address':
        pass
    elif misp_obj.name == 'file':

        #unpack_item_obj(map_uuid_global_id, misp_obj)
        pass

def import_objs_from_file(filepath):
    event_to_import = MISPEvent()
    event_to_import.load_file(filepath)

    map_uuid_global_id = {}

    for misp_obj in event_to_import.objects:
        get_misp_import_fct(map_uuid_global_id, misp_obj)

    print(map_uuid_global_id)


if __name__ == '__main__':

    # misp = PyMISP('https://127.0.0.1:8443/', 'uXgcN42b7xuL88XqK5hubwD8Q8596VrrBvkHQzB0', False)

    #import_objs_from_file('test_import_item.json')
    import_objs_from_file('test_export.json')
