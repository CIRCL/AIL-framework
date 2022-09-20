#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid
import redis

from abc import ABC
from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
from lib.ConfigLoader import ConfigLoader
from lib.ail_core import get_all_objects
from lib import correlations_engine

from lib.objects.CryptoCurrencies import CryptoCurrency
from lib.objects.Decodeds import Decoded
from lib.objects.Domains import Domain
from lib.objects.Items import Item
from lib.objects.Pgps import Pgp
from lib.objects.Screenshots import Screenshot
from lib.objects.Usernames import Username


config_loader = ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

class AILObjects(object): ## ??????????????????????
    initial = 0
    ongoing = 1
    completed = 2

def is_valid_object_type(obj_type):
    return obj_type in get_all_objects()

def sanitize_objs_types(objs):
    l_types = []
    print('sanitize')
    print(objs)
    print(get_all_objects())
    for obj in objs:
        if is_valid_object_type(obj):
            l_types.append(obj)
    return l_types

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

def exists_obj(obj_type, subtype, id):
    object = get_object(obj_type, subtype, id)
    return object.exists()

def get_object_link(obj_type, subtype, id, flask_context=False):
    object = get_object(obj_type, subtype, id)
    return object.get_link(flask_context=flask_context)

def get_object_svg(obj_type, subtype, id):
    object = get_object(obj_type, subtype, id)
    return object.get_svg_icon()

def get_object_meta(obj_type, subtype, id, flask_context=False):
    object = get_object(obj_type, subtype, id)
    meta = object.get_meta()
    meta['icon'] = object.get_svg_icon()
    meta['link'] = object.get_link(flask_context=flask_context)
    return meta

def get_ui_obj_tag_table_keys(obj_type):
    '''
    Warning: use only in flask (dynamic templates)
    '''
    if obj_type=="domain":
        return ['id', 'first_seen', 'last_check', 'status'] # # TODO: add root screenshot

# # TODO: # FIXME:
# def get_objects_meta(l_dict_objs, icon=False, url=False, flask_context=False):
#     l_meta = []
#     for dict_obj in l_dict_objs:
#         object = get_object(dict_obj['type'], dict_obj['subtype'], dict_obj['id'])
#         dict_meta = object.get_default_meta(tags=True)
#         if icon:
#             dict_meta['icon'] = object.get_svg_icon()
#         if url:
#             dict_meta['link'] = object.get_link(flask_context=flask_context)
#         l_meta.append(dict_meta)
#     return l_meta

# # TODO: CHECK IF object already have an UUID
def get_misp_object(obj_type, subtype, id):
    object = get_object(obj_type, subtype, id)
    return object.get_misp_object()

# get misp relationship
def get_objects_relationship(obj_1, obj2):
    relationship = {}
    obj_types = ( obj_1.get_type(), obj2.get_type() )

    ##############################################################
    # if ['cryptocurrency', 'pgp', 'username', 'decoded', 'screenshot']:
    #     {'relation': '', 'src':, 'dest':}
    #     relationship[relation] =
    ##############################################################
    if 'cryptocurrency' in obj_types:
        relationship['relation'] = 'extracted-from'
        if obj1_type == 'cryptocurrency':
            relationship['src'] = obj1_id
            relationship['dest'] =  obj2_id
        else:
            relationship['src'] = obj2_id
            relationship['dest'] =  obj1_id

    elif 'pgp' in obj_types:
        relationship['relation'] = 'extracted-from'

    elif 'username' in obj_types:
        relationship['relation'] = 'extracted-from'

    elif 'decoded' in obj_types:
        relationship['relation'] = 'included-in'

    elif 'screenshot' in obj_types:
        relationship['relation'] = 'screenshot-of'

    elif 'domain' in obj_types:
        relationship['relation'] = 'extracted-from'

    # default
    else:
        pass






    return relationship

def api_sanitize_object_type(obj_type):
    if not is_valid_object_type(obj_type):
        return ({'status': 'error', 'reason': 'Incorrect object type'}, 400)

################################################################################
# DATA RETENTION
# # TODO: TO ADD ??????????????????????
# def get_first_objects_date():
#     return r_object.zrange('objs:first_date', 0, -1)
#
# def get_first_object_date(obj_type, subtype):
#     return r_object.zscore('objs:first_date', f'{obj_type}:{subtype}')
#
# def set_first_object_date(obj_type, subtype, date):
#     return r_object.zadd('objs:first_date', f'{obj_type}:{subtype}', date)


################################################################################
################################################################################
################################################################################

def delete_obj(obj_type, subtype, id):
    object = get_object(obj_type, subtype, id)
    return object.delete()

################################################################################
################################################################################
################################################################################
################################################################################
################################################################################

def create_correlation_graph_links(links_set):
    links = []
    for link in links_set:
        links.append({"source": link[0], "target": link[1]})
    return links

def create_correlation_graph_nodes(nodes_set, obj_str_id, flask_context=True):
    graph_nodes_list = []
    for node_id in nodes_set:
        obj_type, subtype, obj_id = node_id.split(';', 2)
        dict_node = {"id": node_id}
        dict_node['style'] = get_object_svg(obj_type, subtype, obj_id)

        # # TODO: # FIXME: in UI
        dict_node['style']['icon_class'] = dict_node['style']['style']
        dict_node['style']['icon_text'] = dict_node['style']['icon']
        dict_node['style']['node_color'] = dict_node['style']['color']
        dict_node['style']['node_radius'] = dict_node['style']['radius']
        # # TODO: # FIXME: in UI

        dict_node['style']
        dict_node['text'] = obj_id
        if node_id == obj_str_id:
            dict_node["style"]["node_color"] = 'orange'
            dict_node["style"]["node_radius"] = 7
        dict_node['url'] = get_object_link(obj_type, subtype, obj_id, flask_context=flask_context)
        graph_nodes_list.append(dict_node)
    return graph_nodes_list

def get_correlations_graph_node(obj_type, subtype, obj_id, filter_types=[], max_nodes=300, level=1, flask_context=False):
    obj_str_id, nodes, links = correlations_engine.get_correlations_graph_nodes_links(obj_type, subtype, obj_id, filter_types=filter_types, max_nodes=max_nodes, level=level, flask_context=flask_context)
    return {"nodes": create_correlation_graph_nodes(nodes, obj_str_id, flask_context=flask_context), "links": create_correlation_graph_links(links)}




###############
