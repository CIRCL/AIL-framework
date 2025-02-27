#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_metadata = config_loader.get_db_conn("Kvrocks_Correlations")
config_loader = None

##################################
# CORRELATION MIGRATION
##################################
#
#   MIGRATE TO KVROCKS + Rename correlation Keys
#                           => Add support for correlations between subtypes
#                           => Common correlation engine for each objects
#
#   Objects Iterations: -screenshot
#                       -decoded
#                       -subtypes
#                       -domains
#
#   /!\ Handle reinsertion /!\
#
#
#   CORRELATION DB ????? => purge if needed
#
#
#
#
#
##################################
# CORRELATION MIGRATION
##################################

CORRELATION_TYPES_BY_OBJ = {
    "barcode": ["chat", "cve", "cryptocurrency", "decoded", "domain", "image", "message", "screenshot"],
    "chat": ["barcode", "chat-subchannel", "chat-thread", "cryptocurrency", "cve", "decoded", "domain", "image", "message", "ocr", "pgp", "user-account"],
    "chat-subchannel": ["chat", "chat-thread", "image", "message", "ocr", "user-account"],
    "chat-thread": ["chat", "chat-subchannel", "image", "message", "ocr", "user-account"],
    "cookie-name": ["domain"],
    "cryptocurrency": ["barcode", "chat", "domain", "item", "message", "ocr", "qrcode"],
    "cve": ["barcode", "chat", "domain", "item", "message", "ocr", "qrcode"],
    "decoded": ["barcode", "chat", "domain", "item", "message", "ocr", "qrcode"],
    "domain": ["barcode", "chat", "cve", "cookie-name", "cryptocurrency", "dom-hash", "decoded", "etag", "favicon", "hhhash", "item", "message", "pgp", "title", "screenshot", "username"],
    "dom-hash": ["domain", "item"],
    "etag": ["domain"],
    "favicon": ["domain", "item"],  # TODO Decoded
    "file-name": ["chat", "item", "message"],
    "hhhash": ["domain"],
    "image": ["barcode", "chat", "chat-subchannel", "chat-thread", "message", "ocr", "qrcode", "user-account"],  # TODO subchannel + threads ????
    "item": ["cve", "cryptocurrency", "decoded", "domain", "dom-hash", "favicon", "file-name", "message", "pgp", "screenshot", "title", "username"],  # chat ???
    "message": ["barcode", "chat", "chat-subchannel", "chat-thread", "cve", "cryptocurrency", "decoded", "domain", "file-name", "image", "item", "ocr", "pgp", "user-account"],
    "ocr": ["chat", "chat-subchannel", "chat-thread", "cve", "cryptocurrency", "decoded", "image", "message", "pgp", "user-account"],
    "pgp": ["chat", "domain", "item", "message", "ocr"],
    "qrcode": ["chat", "cve", "cryptocurrency", "decoded", "domain", "image", "message", "screenshot"],     # "chat-subchannel", "chat-thread" ?????
    "screenshot": ["barcode", "domain", "item", "qrcode"],
    "title": ["domain", "item"],
    "user-account": ["chat", "chat-subchannel", "chat-thread", "image", "message", "ocr", "username"],
    "username": ["domain", "item", "message", "user-account"],
}

def get_obj_correl_types(obj_type):
    return CORRELATION_TYPES_BY_OBJ.get(obj_type)

def sanityze_obj_correl_types(obj_type, correl_types, sanityze=True):
    if not sanityze:
        return correl_types
    obj_correl_types = get_obj_correl_types(obj_type)
    if correl_types:
        correl_types = set(correl_types).intersection(obj_correl_types)
    if not correl_types:
        correl_types = obj_correl_types
        if not correl_types:
            return []
    return correl_types

def get_nb_correlation_by_correl_type(obj_type, subtype, obj_id, correl_type):
    return r_metadata.scard(f'correlation:obj:{obj_type}:{subtype}:{correl_type}:{obj_id}')

def get_nb_correlations(obj_type, subtype, obj_id, filter_types=[]):
    if subtype is None:
        subtype = ''
    obj_correlations = {}
    filter_types = sanityze_obj_correl_types(obj_type, filter_types)
    for correl_type in filter_types:
        obj_correlations[correl_type] = get_nb_correlation_by_correl_type(obj_type, subtype, obj_id, correl_type)
    return obj_correlations

def get_correlation_by_correl_type(obj_type, subtype, obj_id, correl_type, unpack=False):
    correl = r_metadata.smembers(f'correlation:obj:{obj_type}:{subtype}:{correl_type}:{obj_id}')
    if unpack:
        unpacked = []
        for str_correl in correl:
            unpacked.append(str_correl.split(':', 1))
        return unpacked
    else:
        return correl

def get_correlations(obj_type, subtype, obj_id, filter_types=[], unpack=False, sanityze=True):
    if subtype is None:
        subtype = ''
    obj_correlations = {}
    filter_types = sanityze_obj_correl_types(obj_type, filter_types, sanityze=sanityze)
    for correl_type in filter_types:
        obj_correlations[correl_type] = get_correlation_by_correl_type(obj_type, subtype, obj_id, correl_type,
                                                                       unpack=unpack)
    return obj_correlations

def exists_obj_correlation(obj_type, subtype, obj_id, obj2_type):
    if subtype is None:
        subtype = ''
    return r_metadata.exists(f'correlation:obj:{obj_type}:{subtype}:{obj2_type}:{obj_id}')

def is_obj_correlated(obj_type, subtype, obj_id, obj2_type, subtype2, obj2_id):
    if subtype is None:
        subtype = ''
    if subtype2 is None:
        subtype2 = ''
    try:
        return r_metadata.sismember(f'correlation:obj:{obj_type}:{subtype}:{obj2_type}:{obj_id}', f'{subtype2}:{obj2_id}')
    except:
        return False

def get_obj_inter_correlation(obj_type1, subtype1, obj_id1, obj_type2, subtype2, obj_id2, correl_type):
    return r_metadata.sinter(f'correlation:obj:{obj_type1}:{subtype1}:{correl_type}:{obj_id1}', f'correlation:obj:{obj_type2}:{subtype2}:{correl_type}:{obj_id2}')

def add_obj_correlation(obj1_type, subtype1, obj1_id, obj2_type, subtype2, obj2_id):
    if subtype1 is None:
        subtype1 = ''
    if subtype2 is None:
        subtype2 = ''
    r_metadata.sadd(f'correlation:obj:{obj1_type}:{subtype1}:{obj2_type}:{obj1_id}', f'{subtype2}:{obj2_id}')
    r_metadata.sadd(f'correlation:obj:{obj2_type}:{subtype2}:{obj1_type}:{obj2_id}', f'{subtype1}:{obj1_id}')


def delete_obj_correlation(obj1_type, subtype1, obj1_id, obj2_type, subtype2, obj2_id):
    if subtype1 is None:
        subtype1 = ''
    if subtype2 is None:
        subtype2 = ''
    r_metadata.srem(f'correlation:obj:{obj1_type}:{subtype1}:{obj2_type}:{obj1_id}', f'{subtype2}:{obj2_id}')
    r_metadata.srem(f'correlation:obj:{obj2_type}:{subtype2}:{obj1_type}:{obj2_id}', f'{subtype1}:{obj1_id}')

def delete_obj_correlations(obj_type, subtype, obj_id):
    obj_correlations = get_correlations(obj_type, subtype, obj_id)
    for correl_type in obj_correlations:
        for str_obj in obj_correlations[correl_type]:
            subtype2, obj2_id = str_obj.split(':', 1)
            delete_obj_correlation(obj_type, subtype, obj_id, correl_type, subtype2, obj2_id)

# # bypass max result/objects ???
# def get_correlation_depht(obj_type, subtype, obj_id, filter_types=[], level=1, nb_max=300):
#     objs = set()
#     _get_correlation_depht(objs, obj_type, subtype, obj_id, filter_types, level, nb_max)
#     return objs
#
# def _get_correlation_depht(objs, obj_type, subtype, obj_id, filter_types, level, nb_max, previous_str_obj=''):
#     obj_str_id = get_obj_str_id(obj_type, subtype, obj_id)
#     objs.add(obj_str_id)
#
#     obj_correlations = get_correlations(obj_type, subtype, obj_id, filter_types=filter_types)
#     for correl_type in obj_correlations:
#         for str_obj in obj_correlations[correl_type]:
#             subtype2, obj2_id = str_obj.split(':', 1)
#             obj2_str_id = get_obj_str_id(correl_type, subtype2, obj2_id)
#
#             if obj2_str_id == previous_str_obj:
#                 continue
#
#             if len(nodes) > nb_max:
#                 break
#             objs.add(obj2_str_id)
#
#             if level > 0:
#                 next_level = level - 1
#                 _get_correlation_depht(objs, correl_type, subtype2, obj2_id, filter_types, next_level, nb_max,
#                                        previous_str_obj=obj_str_id)

def get_obj_str_id(obj_type, subtype, obj_id):
    if subtype is None:
        subtype = ''
    return f'{obj_type}:{subtype}:{obj_id}'

def get_correlations_graph_nodes_links(obj_type, subtype, obj_id, filter_types=[], max_nodes=300, level=1, objs_hidden=set(), flask_context=False):
    links = set()
    nodes = set()
    meta = {'complete': True, 'objs': set()}

    obj_str_id = get_obj_str_id(obj_type, subtype, obj_id)

    _get_correlations_graph_node(links, nodes, meta, obj_type, subtype, obj_id, level, max_nodes, filter_types=filter_types, objs_hidden=objs_hidden, previous_str_obj='')
    return obj_str_id, nodes, links, meta


def _get_correlations_graph_node(links, nodes, meta, obj_type, subtype, obj_id, level, max_nodes, filter_types=[], objs_hidden=set(), previous_str_obj=''):
    obj_str_id = get_obj_str_id(obj_type, subtype, obj_id)
    meta['objs'].add(obj_str_id)
    nodes.add(obj_str_id)

    obj_correlations = get_correlations(obj_type, subtype, obj_id, filter_types=filter_types)
    # print(obj_correlations)
    for correl_type in obj_correlations:
        for str_obj in obj_correlations[correl_type]:
            subtype2, obj2_id = str_obj.split(':', 1)
            obj2_str_id = get_obj_str_id(correl_type, subtype2, obj2_id)
            # filter objects to hide
            if obj2_str_id in objs_hidden:
                continue

            meta['objs'].add(obj2_str_id)

            if obj2_str_id == previous_str_obj:
                continue

            if len(nodes) > max_nodes != 0:
                meta['complete'] = False
                break
            nodes.add(obj2_str_id)
            links.add((obj_str_id, obj2_str_id))

            if level > 0:
                next_level = level - 1
                _get_correlations_graph_node(links, nodes, meta, correl_type, subtype2, obj2_id, next_level, max_nodes, filter_types=filter_types, objs_hidden=objs_hidden, previous_str_obj=obj_str_id)

