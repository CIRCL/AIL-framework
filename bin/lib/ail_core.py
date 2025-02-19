#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
config_loader = None

AIL_OBJECTS = sorted({'barcode', 'chat', 'chat-subchannel', 'chat-thread', 'cookie-name', 'cve', 'cryptocurrency',
                      'decoded', 'domain', 'dom-hash', 'etag', 'favicon', 'file-name', 'hhhash','item', 'image',
                      'message', 'ocr', 'pgp', 'qrcode', 'screenshot', 'title', 'user-account', 'username'})

AIL_OBJECTS_WITH_SUBTYPES = {'chat', 'chat-subchannel', 'cryptocurrency', 'pgp', 'username', 'user-account'}

# TODO by object TYPE ????
AIL_OBJECTS_CORRELATIONS_DEFAULT = sorted({'barcode', 'chat', 'chat-subchannel', 'chat-thread', 'cve', 'cryptocurrency',
                                           'decoded', 'domain', 'dom-hash', 'favicon', 'file-name', 'item', 'image',
                                           'message', 'ocr', 'pgp', 'qrcode', 'screenshot', 'title', 'user-account',
                                           'username'})

def get_ail_uuid():
    ail_uuid = r_serv_db.get('ail:uuid')
    if not ail_uuid:
        ail_uuid = _set_ail_uuid()
    return ail_uuid

def _set_ail_uuid():
    ail_uuid = generate_uuid()
    r_serv_db.set('ail:uuid', ail_uuid)
    return ail_uuid

def get_ail_uuid_int():
    ail_uuid = get_ail_uuid()
    header_uuid = ail_uuid.replace('-', '')
    return uuid.UUID(hex=header_uuid, version=4).int

def is_valid_uuid_v4(header_uuid):
    try:
        header_uuid = header_uuid.replace('-', '')
        uuid_test = uuid.UUID(hex=header_uuid, version=4)
        return uuid_test.hex == header_uuid
    except:
        return False

def generate_uuid():
    return str(uuid.uuid4())

def is_valid_uuid_v5(header_uuid):
    try:
        header_uuid = header_uuid.replace('-', '')
        uuid_test = uuid.UUID(hex=header_uuid, version=5)
        return uuid_test.hex == header_uuid
    except:
        return False

def generate_uuid5(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))

#### AIL OBJECTS ####

def get_all_objects():
    return AIL_OBJECTS

def is_object_type(obj_type):
    return obj_type in AIL_OBJECTS

def get_objects_with_subtypes():
    return AIL_OBJECTS_WITH_SUBTYPES

def get_object_all_subtypes(obj_type):  # TODO Dynamic subtype
    if obj_type == 'chat':
        return r_object.smembers(f'all_chat:subtypes')
    if obj_type == 'chat-subchannel':
        return r_object.smembers(f'all_chat-subchannel:subtypes')
    if obj_type == 'chat-thread':
        return r_object.smembers(f'all_chat-thread:subtypes')
    if obj_type == 'cryptocurrency':
        return ['bitcoin', 'bitcoin-cash', 'dash', 'ethereum', 'litecoin', 'monero', 'ripple', 'tron', 'zcash']
    if obj_type == 'pgp':
        return ['key', 'mail', 'name']
    if obj_type == 'username':
        return ['telegram', 'discord', 'twitter', 'jabber']
    if obj_type == 'user-account':
        return r_object.smembers(f'all_chat:subtypes')
    return []

def get_default_correlation_objects():
    return AIL_OBJECTS_CORRELATIONS_DEFAULT

def get_obj_queued():
    return ['barcode', 'item', 'image', 'message', 'ocr', 'qrcode'] # screenshot ???

def get_objects_tracked():
    return ['barcode', 'decoded', 'item', 'message', 'ocr', 'pgp', 'qrcode', 'title']

def get_objects_retro_hunted():
    return ['decoded', 'item', 'message', 'ocr']

def get_all_objects_with_subtypes_tuple():
    str_objs = []
    for obj_type in get_all_objects():
        subtypes = get_object_all_subtypes(obj_type)
        if subtypes:
            for subtype in subtypes:
                str_objs.append((obj_type, subtype))
        else:
            str_objs.append((obj_type, ''))
    return str_objs

def unpack_obj_global_id(global_id, r_type='tuple'):
    if r_type == 'dict':
        obj = global_id.split(':', 2)
        return {'type': obj[0], 'subtype': obj[1], 'id': obj[2]}
    else:  # tuple(type, subtype, id)
        return global_id.split(':', 2)    # TODO REPLACE get_obj_type_subtype_id_from_global_id(global_id)

def unpack_objs_global_id(objs_global_id, r_type='tuple'):
    objs = []
    for global_id in objs_global_id:
        objs.append(unpack_obj_global_id(global_id, r_type=r_type))
    return objs

def unpack_correl_obj__id(obj_type, global_id, r_type='tuple'):
    obj = global_id.split(':', 1)
    if r_type == 'dict':
        return {'type': obj_type, 'subtype': obj[0], 'id': obj[1]}
    else:  # tuple(type, subtype, id)
        return obj_type, obj[0], obj[1]

def unpack_correl_objs_id(obj_type, correl_objs_id, r_type='tuple'):
    objs = []
    for correl_obj_id in correl_objs_id:
        objs.append(unpack_correl_obj__id(obj_type, correl_obj_id, r_type=r_type))
    return objs

##-- AIL OBJECTS --##

def get_chat_instance_name(chat_instance):
    if chat_instance == '00098785-7e70-5d12-a120-c5cdc1252b2b':
        return 'telegram'
    elif chat_instance == 'd2426e3f-22f3-5a57-9a98-d2ae9794e683':
        return 'discord'
    else:
        return chat_instance

####    Redis     ####

def _parse_zscan(response):
    cursor, r = response
    it = iter(r)
    return str(cursor), list(it)

def zscan_iter(r_redis, name):  # count ???
    cursor = 0
    while cursor != "0":
        cursor, data = _parse_zscan(r_redis.zscan(name, cursor=cursor))
        yield from data

## --    Redis     -- ##

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def paginate_iterator(iter_elems, nb_obj=50, page=1):
    dict_page = {'nb_all_elem': len(iter_elems)}
    nb_pages = dict_page['nb_all_elem'] / nb_obj
    if not nb_pages.is_integer():
        nb_pages = int(nb_pages)+1
    else:
        nb_pages = int(nb_pages)
    if page > nb_pages:
        page = nb_pages

    # multiple pages
    if nb_pages > 1:
        dict_page['list_elem'] = []
        start = nb_obj*(page - 1)
        stop = (nb_obj*page) - 1
        current_index = 0
        for elem in iter_elems:
            if current_index > stop:
                break
            if start <= current_index <= stop:
                dict_page['list_elem'].append(elem)
            current_index += 1
        stop += 1
        if stop > dict_page['nb_all_elem']:
            stop = dict_page['nb_all_elem']

    else:
        start = 0
        stop = dict_page['nb_all_elem']
        dict_page['list_elem'] = list(iter_elems)
    dict_page['page'] = page
    dict_page['nb_pages'] = nb_pages
    # UI
    dict_page['nb_first_elem'] = start+1
    dict_page['nb_last_elem'] = stop
    return dict_page
