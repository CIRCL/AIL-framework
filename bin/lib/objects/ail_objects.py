#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from abc import ABC
from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.ail_core import get_all_objects
from lib import correlations_engine
from lib import btc_ail
from lib import Tag

from lib.objects import CryptoCurrencies
from lib.objects.Cves import Cve
from lib.objects.Decodeds import Decoded
from lib.objects.Domains import Domain
from lib.objects.Items import Item
from lib.objects import Pgps
from lib.objects.Screenshots import Screenshot
from lib.objects import Usernames


config_loader = ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

class AILObjects(object):  ## ??????????????????????
    initial = 0
    ongoing = 1
    completed = 2

def is_valid_object_type(obj_type):
    return obj_type in get_all_objects()

def is_valid_object_subtype(obj_type, subtype):
    if obj_type == 'cryptocurrency':
        return subtype in CryptoCurrencies.get_all_subtypes()
    elif obj_type == 'pgp':
        return subtype in Pgps.get_all_subtypes()
    elif obj_type == 'username':
        return subtype in CryptoCurrencies.get_all_subtypes()

def sanitize_objs_types(objs):
    l_types = []
    for obj in objs:
        if is_valid_object_type(obj):
            l_types.append(obj)
    if not l_types:
        l_types = get_all_objects()
    return l_types

def get_object(obj_type, subtype, id):
    if obj_type == 'item':
        return Item(id)
    elif obj_type == 'domain':
        return Domain(id)
    elif obj_type == 'decoded':
        return Decoded(id)
    elif obj_type == 'cve':
        return Cve(id)
    elif obj_type == 'screenshot':
        return Screenshot(id)
    elif obj_type == 'cryptocurrency':
        return CryptoCurrencies.CryptoCurrency(id, subtype)
    elif obj_type == 'pgp':
        return Pgps.Pgp(id, subtype)
    elif obj_type == 'username':
        return Usernames.Username(id, subtype)

def exists_obj(obj_type, subtype, obj_id):
    obj = get_object(obj_type, subtype, obj_id)
    if obj:
        return obj.exists()
    else:
        return False

def get_obj_global_id(obj_type, subtype, obj_id):
    obj = get_object(obj_type, subtype, obj_id)
    return obj.get_global_id()

def get_obj_from_global_id(global_id):
    obj = global_id.split(':', 3)
    return get_object(obj[0], obj[1], obj[2])

def get_object_link(obj_type, subtype, id, flask_context=False):
    obj = get_object(obj_type, subtype, id)
    return obj.get_link(flask_context=flask_context)

def get_object_svg(obj_type, subtype, id):
    obj = get_object(obj_type, subtype, id)
    return obj.get_svg_icon()

def get_object_meta(obj_type, subtype, id, options=[], flask_context=False):
    obj = get_object(obj_type, subtype, id)
    meta = obj.get_meta(options=options)
    meta['icon'] = obj.get_svg_icon()
    meta['link'] = obj.get_link(flask_context=flask_context)
    return meta

def get_objects_meta(objs, options=[], flask_context=False):
    metas = []
    for obj_dict in objs:
        metas.append(get_object_meta(obj_dict['type'], obj_dict['subtype'], obj_dict['id'], options=options,
                                     flask_context=flask_context))
    return metas

def get_object_card_meta(obj_type, subtype, id, related_btc=False):
    obj = get_object(obj_type, subtype, id)
    meta = obj.get_meta()
    meta['icon'] = obj.get_svg_icon()
    if subtype or obj_type == 'cve':
        meta['sparkline'] = obj.get_sparkline()
    if subtype == 'bitcoin' and related_btc:
        meta["related_btc"] = btc_ail.get_bitcoin_info(obj.id)
    if obj.get_type() == 'decoded':
        meta["vt"] = obj.get_meta_vt()
        meta["vt"]["status"] = obj.is_vt_enabled()
    # TAGS MODAL
    if obj.get_type() == 'screenshot' or obj.get_type() == 'decoded':
        meta["add_tags_modal"] = Tag.get_modal_add_tags(obj.id, obj.get_type(), obj.get_subtype(r_str=True))
    return meta

def get_ui_obj_tag_table_keys(obj_type):
    '''
    Warning: use only in flask (dynamic templates)
    '''
    if obj_type == "domain":
        return ['id', 'first_seen', 'last_check', 'status']  # # TODO: add root screenshot

# # TODO: CHECK IF object already have an UUID
def get_misp_object(obj_type, subtype, id):
    obj = get_object(obj_type, subtype, id)
    return obj.get_misp_object()

# get misp relationship
def get_objects_relationship(obj_1, obj2):
    relationship = {}
    obj_types = (obj_1.get_type(), obj2.get_type())

    ##############################################################
    # if ['cryptocurrency', 'pgp', 'username', 'decoded', 'screenshot']:
    #     {'relation': '', 'src':, 'dest':}
    #     relationship[relation] =
    ##############################################################
    if 'cryptocurrency' in obj_types:
        relationship['relation'] = 'extracted-from'
        if obj_1.get_type() == 'cryptocurrency':
            relationship['src'] = obj_1.get_id()
            relationship['dest'] = obj2.get_id()
        else:
            relationship['src'] = obj2.get_id()
            relationship['dest'] = obj_1.get_id()

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
        return {'status': 'error', 'reason': 'Incorrect object type'}, 400

def get_obj_correlations(obj_type, subtype, id):
    obj = get_object(obj_type, subtype, id)
    return obj.get_correlations()

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
