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
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

AIL_OBJECTS = sorted({'cookie-name', 'cve', 'cryptocurrency', 'decoded', 'domain', 'etag', 'favicon', 'hhhash', 'item',
                      'pgp', 'screenshot', 'title', 'username'})

def get_ail_uuid():
    ail_uuid = r_serv_db.get('ail:uuid')
    if not ail_uuid:
        ail_uuid = _set_ail_uuid()
    return ail_uuid

def _set_ail_uuid():
    ail_uuid = generate_uuid()
    r_serv_db.set('ail:uuid', ail_uuid)
    return ail_uuid

def generate_uuid():
    return str(uuid4())

#### AIL OBJECTS ####

def get_all_objects():
    return AIL_OBJECTS

def get_objects_with_subtypes():
    return ['cryptocurrency', 'pgp', 'username']

def get_object_all_subtypes(obj_type):
    if obj_type == 'cryptocurrency':
        return ['bitcoin', 'bitcoin-cash', 'dash', 'ethereum', 'litecoin', 'monero', 'zcash']
    if obj_type == 'pgp':
        return ['key', 'mail', 'name']
    if obj_type == 'username':
        return ['telegram', 'twitter', 'jabber']
    return []

def get_objects_tracked():
    return ['decoded', 'item', 'pgp', 'title']

def get_objects_retro_hunted():
    return ['decoded', 'item']

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

##-- AIL OBJECTS --##

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
