#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

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
    "cryptocurrency" : ["domain", "item"],
    "decoded" : ["domain", "item"],
    "domain": ["cryptocurrency", "decoded", "item", "pgp", "username", "screenshot"],
    "item": ["cryptocurrency", "decoded", "domain", "pgp", "username", "screenshot"],
    "pgp" : ["domain", "item"],
    "username" : ["domain", "item"],
    "screenshot" : ["domain", "item"],
}

def get_obj_correl_types(obj_type):
    return CORRELATION_TYPES_BY_OBJ.get(obj_type)

def sanityze_obj_correl_types(obj_type, correl_types):
    obj_correl_types = get_obj_correl_types(obj_type)
    if correl_types:
        correl_types = set(correl_types).intersection(obj_correl_types)
    if not correl_types:
        correl_types = obj_correl_types
    return correl_types

def get_nb_correlation_by_correl_type(obj_type, subtype, obj_id, correl_type):
    return r_metadata.scard(f'correlation:obj:{obj_type}:{subtype}:{correl_type}:{obj_id}')

def get_nb_correlations(obj_type, subtype, obj_id, filter_types=[]):
    if subtype is None:
        subtype = ''
    nb_correlations = 0
    filter_types = sanityze_obj_correl_types(obj_type, filter_types)
    for correl_type in filter_types:
        obj_correlations += get_nb_correlation_by_correl_type(obj_type, subtype, obj_id, correl_type)
    return obj_correlations

def get_correlation_by_correl_type(obj_type, subtype, obj_id, correl_type):
    return r_metadata.smembers(f'correlation:obj:{obj_type}:{subtype}:{correl_type}:{obj_id}')

def get_correlations(obj_type, subtype, obj_id, filter_types=[]):
    if subtype is None:
        subtype = ''
    obj_correlations = {}
    filter_types = sanityze_obj_correl_types(obj_type, filter_types)
    for correl_type in filter_types:
        obj_correlations[correl_type] = get_correlation_by_correl_type(obj_type, subtype, obj_id, correl_type)
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
    return r_metadata.sismember(f'correlation:obj:{obj_type}:{subtype}:{obj2_type}:{obj_id}', '{subtype2}:{obj2_id}')

def add_obj_correlation(obj1_type, subtype1, obj1_id, obj2_type, subtype2, obj2_id):
    print(obj1_type, subtype1, obj1_id, obj2_type, subtype2, obj2_id)
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
    r_metadata.srem(f'correlation:obj:{obj1_type}:{subtype}:{obj2_type}:{obj_id}', f'{subtype2}:{obj2_id}')
    r_metadata.srem(f'correlation:obj:{obj2_type}:{subtype2}:{obj1_type}:{obj2_id}', f'{subtype}:{obj_id}')



# # TODO: CORRELATION GRAPH


def get_obj_str_id(obj_type, subtype, obj_id): ################ REPLACE BY : ?????????????????????????
    if subtype is None:
        subtype = ''
    return f'{obj_type};{subtype};{obj_id}'

def get_correlations_graph_nodes_links(obj_type, subtype, obj_id, filter_types=[], max_nodes=300, level=1, flask_context=False):
    links = set()
    nodes = set()

    obj_str_id = get_obj_str_id(obj_type, subtype, obj_id)

    _get_correlations_graph_node(links, nodes, obj_type, subtype, obj_id, level, max_nodes, filter_types=[], previous_str_obj='')
    return obj_str_id, nodes, links


def _get_correlations_graph_node(links, nodes, obj_type, subtype, obj_id, level, max_nodes, filter_types=[], previous_str_obj=''):
    obj_str_id = get_obj_str_id(obj_type, subtype, obj_id)
    nodes.add(obj_str_id)

    obj_correlations = get_correlations(obj_type, subtype, obj_id, filter_types=[])
    print(obj_correlations)
    for correl_type in obj_correlations:
        for str_obj in obj_correlations[correl_type]:
            subtype2, obj2_id = str_obj.split(':', 1)
            obj2_str_id = get_obj_str_id(correl_type, subtype2, obj2_id)

            if obj2_str_id == previous_str_obj:
                continue

            if len(nodes) > max_nodes:
                break
            nodes.add(obj2_str_id)
            links.add((obj_str_id, obj2_str_id))

            if level > 0:
                next_level = level - 1
                _get_correlations_graph_node(links, nodes, correl_type, subtype2, obj2_id, next_level, max_nodes, filter_types=filter_types, previous_str_obj=obj_str_id)




##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################























# get_correlations_fcts = {
#     "cryptocurrency" : ["domain", "item"],
#     "decoded" : ["domain", "item"],
#     "domain": ["cryptocurrency", "decoded", "item", "pgp", "username", "screenshot"],
#     "item": ["cryptocurrency", "decoded", "domain", "pgp", "username", "screenshot"],
#     "pgp" : ["domain", "item"],
#     "username" : ["domain", "item"],
#     "screenshot" :{
#         "domain": get_correl_screenshot_domain,
#         "item": get_correl_screenshot_item,
#          },
#     }
# }
#
# def build_lsets_obj_types(obj1_type, obj_types):
#     return [set(obj1_type, x) for x in subtypes_obj]
#
# ##########################
# subtypes_obj = ['cryptocurrency', 'pgp', 'username']
# lsets_subtypes_obj_domain = build_lsets_obj_types('domain', subtypes_obj)
# lsets_subtypes_obj_item = build_lsets_obj_types('item', subtypes_obj)
# ##########################

# TODO HANDLE CRAWLED ITEMS
def add_correlation(obj1_type, obj1_subtype, obj1_id, obj2_type, obj2_subtype, obj2_id):
    set_type = set(ob1_type, ob2_type)

    # domain - subtypes objs
    if set_type in lsets_subtypes_obj_domain:
        if ob1_type == 'domain':
            domain = obj1_id
            obj_type = obj2_type
            obj_subtype = obj2_subtype
            obj_id = obj2_id
        else:
            domain = obj2_id
            obj_type = obj1_type
            obj_subtype = obj1_subtype
            obj_id = obj1_id
        r_metadata.sadd(f'domain_{obj_type}_{obj_subtype}:{domain}', obj_id)
        r_metadata.sadd(f'set_domain_{obj_type}_{obj_subtype}:{obj_id}', domain)

    # TODO HANDLE CRAWLED ITEMS
    # item - subtypes objs
    elif set_type in lsets_subtypes_obj_item:
        if ob1_type == 'item':
            item_id = obj1_id
            obj_type = obj2_type
            obj_subtype = obj2_subtype
            obj_id = obj2_id
        else:
            item_id = obj2_id
            obj_type = obj1_type
            obj_subtype = obj1_subtype
            obj_id = obj1_id
        r_metadata.sadd(f'set_{obj_type}_{obj_subtype}:{obj_id}', item_id)
        r_metadata.sadd(f'item_{obj_type}_{obj_subtype}:{item_id}', obj_id)

    # domain - decoded
    elif set_type == set('domain', 'decoded'):
        if ob1_type == 'decoded':
            decoded_id = ob1_id
            domain = obj2_id
        else:
            decoded_id = obj2_id
            domain = ob1_id
        r_metadata.sadd(f'hash_domain:{domain}', decoded_id) # domain - hash map
        r_metadata.sadd(f'domain_hash:{decoded_id}', domain) # hash - domain map

    # item - decoded
    elif set_type == set('item', 'decoded'):
        if ob1_type == 'decoded':
            decoded_id = ob1_id
            item_id = obj2_id
        else:
            decoded_id = obj2_id
            item_id = ob1_id

        ############################################################


    # domain - screenshot
    elif set_type == set('domain', 'screenshot'):
        if ob1_type == 'screenshot':
            screenshot_id = ob1_id
            domain = obj2_id
        else:
            screenshot_id = obj2_id
            domain = ob1_id
        r_crawler.sadd(f'domain_screenshot:{domain}', screenshot_id)
        r_crawler.sadd(f'screenshot_domain:{screenshot_id}', domain)

    # item - screenshot
    elif set_type == set('item', 'screenshot'):
        if ob1_type == 'screenshot':
            screenshot_id = ob1_id
            item_id = obj2_id
        else:
            screenshot_id = obj2_id
            item_id = ob1_id
        r_metadata.hset(f'paste_metadata:{item_id}', 'screenshot', screenshot_id)
        r_crawler.sadd(f'screenshot:{screenshot_id}', item_id)

    # domain - item
    elif set_type == set('domain', 'item'):
        if ob1_type == 'item':
            item_id = ob1_id
            domain = obj2_id
        else:
            item_id = obj2_id
            domain = ob1_id

    ############################################################



# TODO ADD COMPLETE DELETE
# TODO: Handle items crawled
def delete_correlation(obj1_type, obj1_subtype, obj1_id, obj2_type, obj2_subtype, obj2_id):
    set_type = set(ob1_type, ob2_type)

    # domain - subtypes objs
    if set_type in lsets_subtypes_obj_domain:
        if ob1_type == 'domain':
            domain = obj1_id
            obj_type = obj2_type
            obj_subtype = obj2_subtype
            obj_id = obj2_id
        else:
            domain = obj2_id
            obj_type = obj1_type
            obj_subtype = obj1_subtype
            obj_id = obj1_id
        r_metadata.srem(f'domain_{obj_type}_{obj_subtype}:{domain}', obj_id)
        r_metadata.srem(f'set_domain_{obj_type}_{obj_subtype}:{obj_id}', domain)



    # TODO ADD COMPLETE DELETE
    # item - subtypes objs
    elif set_type in lsets_subtypes_obj_item:
        if ob1_type == 'item':
            item_id = obj1_id
            obj_type = obj2_type
            obj_subtype = obj2_subtype
            obj_id = obj2_id
        else:
            item_id = obj2_id
            obj_type = obj1_type
            obj_subtype = obj1_subtype
            obj_id = obj1_id
        # TODO ADD COMPLETE DELETE
        r_metadata.srem(f'set_{obj_type}_{subtype}:{obj_id}', item_id)
        r_metadata.srem(f'item_{obj_type}_{subtype}:{item_id}', obj_id)
        # TODO ADD COMPLETE DELETE

    # domain - decoded
    elif set_type == set('domain', 'decoded'):
        if ob1_type == 'decoded':
            decoded_id = ob1_id
            domain = obj2_id
        else:
            decoded_id = obj2_id
            domain = ob1_id
        r_metadata.srem(f'hash_domain:{domain}', decoded_id)
        r_metadata.srem(f'domain_hash:{decoded_id}', domain)

    # item - decoded
    elif set_type == set('item', 'decoded'):
        if ob1_type == 'decoded':
            decoded_id = ob1_id
            item_id = obj2_id
        else:
            decoded_id = obj2_id
            item_id = ob1_id

            ####################################################################


    # domain - screenshot
    elif set_type == set('domain', 'screenshot'):
        if ob1_type == 'screenshot':
            screenshot_id = ob1_id
            domain = obj2_id
        else:
            screenshot_id = obj2_id
            domain = ob1_id
        r_crawler.srem(f'domain_screenshot:{domain}', screenshot_id)
        r_crawler.srem(f'screenshot_domain:{screenshot_id}', domain)

    # item - screenshot
    elif set_type == set('item', 'screenshot'):
        if ob1_type == 'screenshot':
            screenshot_id = ob1_id
            item_id = obj2_id
        else:
            screenshot_id = obj2_id
            item_id = ob1_id
        r_metadata.hdel(f'paste_metadata:{item_id}', 'screenshot', screenshot_id)
        r_crawler.srem(f'screenshot:{screenshot_id}', item_id)

    # domain - item

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

## Subtypes - Cryptocurrency Pgp Username ##

def get_correl_subtypes_obj_domain(obj_type, obj_subtype, obj_id):
    r_serv_metadata.smembers(f'set_domain_{obj_type}_{obj_subtype}:{obj_id}')

def get_correl_subtypes_obj_item():
    pass

def delete_subtype_domain_correlation(domain, obj_type, subtype, obj_id):
    r_metadata.srem(f'domain_{obj_type}_{subtype}:{domain}', obj_id)
    r_metadata.srem(f'set_domain_{obj_type}_{subtype}:{obj_id}', domain)

# TODO ADD COMPLETE DELETE
def delete_subtype_item_correlation(obj_type, subtype, obj_id, item_id, item_date):
    #self.update_correlation_daterange(subtype, obj_id, item_date) update daterange ! # # TODO:
    r_metadata.srem(f'set_{obj_type}_{subtype}:{obj_id}', item_id)
    r_metadata.srem(f'item_{obj_type}_{subtype}:{item_id}', obj_id)

    # # TODO: FIXME HANDLE SUB Objects Metadata # WARNING:
    # res = r_serv_metadata.hincrby('{}:{}:{}'.format(self.correlation_name, subtype, item_date), obj_id, -1)
    # if int(res) < 0: # remove last
    #     r_serv_metadata.hdel('{}:{}:{}'.format(self.correlation_name, subtype, item_date), obj_id)
    #
    # res = r_serv_metadata.zscore('{}_all:{}'.format(self.correlation_name, subtype), obj_id)
    # if int(res) > 0:
    #     r_serv_metadata.zincrby('{}_all:{}'.format(self.correlation_name, subtype), obj_id, -1)

## Screenshot ##

##-- Screenshot - Domain --##
def add_correl_screenshot_domain(screenshot_id, domain):
    r_crawler.sadd(f'domain_screenshot:{domain}', screenshot_id)
    r_crawler.sadd(f'screenshot_domain:{screenshot_id}', domain)

def get_correl_screenshot_domain(screenshot_id):
    return r_crawler.smembers(f'screenshot_domain:{screenshot_id}')

# def delete_correl_screenshot_domain(screenshot_id, domain):
#     r_crawler.srem(f'domain_screenshot:{domain}', screenshot_id)
#     r_crawler.srem(f'screenshot_domain:{screenshot_id}', domain)

##-- Screenshot - Item --##
def add_correl_screenshot_item(screenshot_id, item_id):
    r_metadata.hset(f'paste_metadata:{item_id}', 'screenshot', screenshot_id)
    r_crawler.sadd(f'screenshot:{screenshot_id}', item_id)

def get_correl_screenshot_item(screenshot_id):
    r_crawler.smembers(f'screenshot:{screenshot_id}')

# def delete_correl_screenshot_item(screenshot_id, item_id):
#     r_metadata.hdel(f'paste_metadata:{item_id}', 'screenshot', screenshot_id)
#     r_crawler.srem(f'screenshot:{screenshot_id}', item_id)

##    --     ##


def get_correl_item_screenshot(item_id):
    res = r_metadata.hget(f'paste_metadata:{item_id}', 'screenshot')
    if res:
        return set(res)
    else:
        return set()

## Domain ##

def get_correl_domain_subtypes_obj(domain_id, obj_type, obj_subtype):
    return r_serv_metadata.smembers(f'domain_{obj_type}_{obj_subtype}:{domain_id}')

##   --   ##

## Item ##

def get_correl_item_subtypes_obj():
    pass

##   --   ## war game stinger - stranger thing


def _get_object_correlations(obj_type, obj_subtype, obj_id, filter_types=[]): # # TODO: , filter_subtypes=[]
    obj_relationships = get_obj_relationships(obj_type)
    correlations = []
    for correlation_fct in obj_relationship_fcts[obj_type]:
        correlations






def get_object_correlations(filter_types, filter_subtypes, lvl=0):
    pass









































####################################################################
####################################################################
####################################################################
####################################################################
####################################################################
####################################################################

def get_object_correlation(object_type, value, correlation_names=None, correlation_objects=None, requested_correl_type=None):
    if object_type == 'domain':
        return Domain.get_domain_all_correlation(value, correlation_names=correlation_names)
    elif object_type == 'paste' or object_type == 'item':
        return Item.get_item_all_correlation(value, correlation_names=correlation_names)
    elif object_type == 'decoded':
        return Decoded.get_decoded_correlated_object(value, correlation_objects=correlation_objects)
    elif object_type == 'pgp':
        return Pgp.pgp.get_correlation_all_object(requested_correl_type, value, correlation_objects=correlation_objects)
    elif object_type == 'cryptocurrency':
        return Cryptocurrency.cryptocurrency.get_correlation_all_object(requested_correl_type, value, correlation_objects=correlation_objects)
    elif object_type == 'username':
        return Username.correlation.get_correlation_all_object(requested_correl_type, value, correlation_objects=correlation_objects)
    elif object_type == 'screenshot' or object_type == 'image':
        return Screenshot.get_screenshot_correlated_object(value, correlation_objects=correlation_objects)
    return {}

def get_obj_tag_table_keys(object_type):
    '''
    Warning: use only in flask (dynamic templates)
    '''
    if object_type=="domain":
        return ['id', 'first_seen', 'last_check', 'status'] # # TODO: add root screenshot

def create_obj_relationship(obj1_type, obj1_id, obj2_type, obj2_id, obj1_subtype=None, obj2_subtype=None):
    if obj1_type == 'domain':
        pass
    elif obj1_type == 'item':
        pass # son/father + duplicate + domain
    elif obj1_type == 'pgp':
        Pgp.pgp.save_obj_relationship(obj1_subtype, obj1_id, obj2_type, obj2_id)
    elif obj1_type == 'cryptocurrency':
        Cryptocurrency.cryptocurrency.save_obj_relationship(obj1_subtype, obj1_type, obj2_type, obj2_id)
    elif obj1_type == 'decoded':
        Decoded.save_obj_relationship(obj1_id, obj2_type, obj2_id)
    elif obj1_type == 'image':
        Screenshot.save_obj_relationship(obj1_id, obj2_type, obj2_id)

def delete_obj_relationship(obj1_type, obj1_id, obj2_type, obj2_id, obj1_subtype=None, obj2_subtype=None):
    if obj1_type == 'domain':
        pass
    elif obj1_type == 'item':
        pass # son/father + duplicate + domain
    elif obj1_type == 'pgp':
        Pgp.pgp.delete_obj_relationship(obj1_subtype, obj1_id, obj2_type, obj2_id)
    elif obj1_type == 'cryptocurrency':
        Cryptocurrency.cryptocurrency.delete_obj_relationship(obj1_subtype, obj1_type, obj2_type, obj2_id)
    elif obj1_type == 'decoded':
        Decoded.delete_obj_relationship(obj1_id, obj2_type, obj2_id)
    elif obj1_type == 'image':
        Screenshot.delete_obj_relationship(obj1_id, obj2_type, obj2_id)

def create_graph_links(links_set):
    graph_links_list = []
    for link in links_set:
        graph_links_list.append({"source": link[0], "target": link[1]})
    return graph_links_list

def create_graph_nodes(nodes_set, root_node_id, flask_context=True):
    graph_nodes_list = []
    for node_id in nodes_set:
        correlation_name, correlation_type, value = node_id.split(';', 3)
        dict_node = {"id": node_id}
        dict_node['style'] = get_correlation_node_icon(correlation_name, correlation_type, value)
        dict_node['text'] = value
        if node_id == root_node_id:
            dict_node["style"]["node_color"] = 'orange'
            dict_node["style"]["node_radius"] = 7
        dict_node['url'] = get_item_url(correlation_name, value, correlation_type, flask_context=flask_context)
        graph_nodes_list.append(dict_node)
    return graph_nodes_list

def create_node_id(correlation_name, value, correlation_type=''):
    if correlation_type is None:
        correlation_type = ''
    return '{};{};{}'.format(correlation_name, correlation_type, value)



# # TODO: filter by correlation type => bitcoin, mail, ...
def get_graph_node_object_correlation(object_type, root_value, mode, correlation_names, correlation_objects, max_nodes=300, requested_correl_type=None, flask_context=True):
    links = set()
    nodes = set()

    root_node_id = create_node_id(object_type, root_value, requested_correl_type)
    nodes.add(root_node_id)

    root_correlation = get_object_correlation(object_type, root_value, correlation_names, correlation_objects, requested_correl_type=requested_correl_type)
    for correl in root_correlation:
        if correl in ('pgp', 'cryptocurrency', 'username'):
            for correl_type in root_correlation[correl]:
                for correl_val in root_correlation[correl][correl_type]:

                    # add correlation
                    correl_node_id = create_node_id(correl, correl_val, correl_type)

                    if mode=="union":
                        if len(nodes) > max_nodes:
                            break
                        nodes.add(correl_node_id)
                        links.add((root_node_id, correl_node_id))

                    # get second correlation
                    res = get_object_correlation(correl, correl_val, correlation_names, correlation_objects, requested_correl_type=correl_type)
                    if res:
                        for corr_obj in res:
                            for correl_key_val in res[corr_obj]:
                                #filter root value
                                if correl_key_val == root_value:
                                    continue

                                if len(nodes) > max_nodes:
                                    break
                                new_corel_1 = create_node_id(corr_obj, correl_key_val)
                                new_corel_2 = create_node_id(correl, correl_val, correl_type)
                                nodes.add(new_corel_1)
                                nodes.add(new_corel_2)
                                links.add((new_corel_1, new_corel_2))

                                if mode=="inter":
                                    nodes.add(correl_node_id)
                                    links.add((root_node_id, correl_node_id))
        if correl in ('decoded', 'screenshot', 'domain', 'paste'):
            for correl_val in root_correlation[correl]:

                correl_node_id = create_node_id(correl, correl_val)
                if mode=="union":
                    if len(nodes) > max_nodes:
                        break
                    nodes.add(correl_node_id)
                    links.add((root_node_id, correl_node_id))

                res = get_object_correlation(correl, correl_val, correlation_names, correlation_objects)
                if res:
                    for corr_obj in res:
                        if corr_obj in ('decoded', 'domain', 'paste', 'screenshot'):
                            for correl_key_val in res[corr_obj]:
                                #filter root value
                                if correl_key_val == root_value:
                                    continue

                                if len(nodes) > max_nodes:
                                    break
                                new_corel_1 = create_node_id(corr_obj, correl_key_val)
                                new_corel_2 = create_node_id(correl, correl_val)
                                nodes.add(new_corel_1)
                                nodes.add(new_corel_2)
                                links.add((new_corel_1, new_corel_2))

                                if mode=="inter":
                                    nodes.add(correl_node_id)
                                    links.add((root_node_id, correl_node_id))

                        if corr_obj in ('pgp', 'cryptocurrency', 'username'):
                            for correl_key_type in res[corr_obj]:
                                for correl_key_val in res[corr_obj][correl_key_type]:
                                    #filter root value
                                    if correl_key_val == root_value:
                                        continue

                                    if len(nodes) > max_nodes:
                                        break
                                    new_corel_1 = create_node_id(corr_obj, correl_key_val, correl_key_type)
                                    new_corel_2 = create_node_id(correl, correl_val)
                                    nodes.add(new_corel_1)
                                    nodes.add(new_corel_2)
                                    links.add((new_corel_1, new_corel_2))

                                    if mode=="inter":
                                        nodes.add(correl_node_id)
                                        links.add((root_node_id, correl_node_id))


    return {"nodes": create_graph_nodes(nodes, root_node_id, flask_context=flask_context), "links": create_graph_links(links)}











#######################################################################################3
