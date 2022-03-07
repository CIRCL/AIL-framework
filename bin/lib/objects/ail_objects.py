#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid
import redis

from abc import ABC
from flask import url_for


sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/objects'))
from Decodeds import Decoded
from Domains import Domain
from CryptoCurrencies import CryptoCurrency
from Items import Item
from Pgps import Pgp
from Screenshots import Screenshot
from Usernames import Username

##################################################################
##################################################################
#sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))

#sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
##################################################################
##################################################################

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

class AILObjects(object):
    initial = 0
    ongoing = 1
    completed = 2


# # TODO: check change paste => item
def get_all_objects():
    return ['domain', 'item', 'pgp', 'cryptocurrency', 'decoded', 'screenshot', 'username']

def get_object(obj_type, subtype, id):
    if obj_type == 'item':
        return Item(id)
    elif obj_type == 'domain':
        return Domain(id)
    elif obj_type == 'decoded':
        return Decoded(id)
    elif obj_type == 'screenshot':
        return Screenshot(id)
    elif obj_type == 'cryptocurrency':
        return CryptoCurrency(id, subtype)
    elif obj_type == 'pgp':
        return Pgp(id, subtype)
    elif obj_type == 'username':
        return Username(id, subtype)

def get_object_svg(obj_type, subtype, id):
    object = get_object(obj_type, subtype, id)
    return object.get_svg_icon()

def get_objects_meta(l_dict_objs, icon=False, url=False, flask_context=False):
    l_meta = []
    for dict_obj in l_dict_objs:
        object = get_object(dict_obj['type'], dict_obj['subtype'], dict_obj['id'])
        dict_meta = object.get_default_meta(tags=True)
        if icon:
            dict_meta['icon'] = object.get_svg_icon()
        if url:
            dict_meta['link'] = object.get_link(flask_context=flask_context)
        l_meta.append(dict_meta)
    return l_meta


################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
