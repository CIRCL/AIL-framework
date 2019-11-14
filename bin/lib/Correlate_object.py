#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid
import redis

from flask import url_for

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import Decoded
import Domain

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Pgp
import Cryptocurrency
import Item

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

def get_all_correlation_names():
    '''
    Return a list of all available correlations
    '''
    return ['pgp', 'cryptocurrency', 'decoded']

def get_all_correlation_objects():
    '''
    Return a list of all correllated objects
    '''
    return ['domain', 'paste']

def get_object_metadata(object_type, correlation_id, type_id=None):
    if object_type == 'domain':
        return Domain.Domain(correlation_id).get_domain_metadata()
    elif object_type == 'paste':
        return None
    elif object_type == 'decoded':
        return Decoded.get_decoded_metadata(correlation_id)
    elif object_type == 'pgp':
        return Pgp.pgp._get_metadata(type_id, correlation_id)
    elif object_type == 'cryptocurrency':
        return Cryptocurrency.cryptocurrency._get_metadata(type_id, correlation_id)

def get_object_correlation(object_type, value, correlation_names, correlation_objects, requested_correl_type=None):
    if object_type == 'domain':
        return Domain.get_domain_all_correlation(value, correlation_names=correlation_names)
    elif object_type == 'paste':
        return Item.get_item_all_correlation(value, correlation_names=correlation_names)
    elif object_type == 'decoded':
        return Decoded.get_decoded_correlated_object(value, correlation_objects)
    elif object_type == 'pgp':
        return Pgp.pgp.get_correlation_all_object(requested_correl_type, value, correlation_objects=correlation_objects)
    elif object_type == 'cryptocurrency':
        return Cryptocurrency.cryptocurrency.get_correlation_all_object(requested_correl_type, value, correlation_objects=correlation_objects)

    return {}

def get_correlation_node_icon(correlation_name, correlation_type=None, value=None):
    '''
    Used in UI Graph.
    Return a font awesome icon for a given correlation_name.

    :param correlation_name: correlation name
    :param correlation_name: str
    :param correlation_type: correlation type
    :type correlation_type: str, optional

    :return: a dictionnary {font awesome class, icon_code}
    :rtype: dict
    '''
    icon_class = 'fas'
    icon_text = ''
    node_color = "#332288"
    node_radius = 6
    if correlation_name == "pgp":
        node_color = '#44AA99'
        if correlation_type == 'key':
            icon_text = '\uf084'
        elif correlation_type == 'name':
            icon_text = '\uf507'
        elif correlation_type == 'mail':
            icon_text = '\uf1fa'
        else:
            icon_text = 'times'

    elif correlation_name == 'cryptocurrency':
        node_color = '#DDCC77'
        if correlation_type == 'bitcoin':
            icon_class = 'fab'
            icon_text = '\uf15a'
        elif correlation_type == 'monero':
            icon_class = 'fab'
            icon_text = '\uf3d0'
        elif correlation_type == 'ethereum':
            icon_class = 'fab'
            icon_text = '\uf42e'
        else:
            icon_text = '\uf51e'

    elif correlation_name == 'decoded':
        node_color = '#88CCEE'
        correlation_type = Decoded.get_decoded_item_type(value).split('/')[0]
        if correlation_type == 'application':
            icon_text = '\uf15b'
        elif correlation_type == 'audio':
            icon_text = '\uf1c7'
        elif correlation_type == 'image':
            icon_text = '\uf1c5'
        elif correlation_type == 'text':
            icon_text = '\uf15c'
        else:
            icon_text = '\uf249'

    elif correlation_name == 'domain':
        node_radius = 5
        node_color = '#3DA760'
        if Domain.get_domain_type(value) == 'onion':
            icon_text = '\uf06e'
        else:
            icon_class = 'fab'
            icon_text = '\uf13b'

    elif correlation_name == 'paste':
        node_radius = 5
        if Item.is_crawled(value):
            node_color = 'red'
        else:
            node_color = '#332288'

    return {"icon_class": icon_class, "icon_text": icon_text, "node_color": node_color, "node_radius": node_radius}

def get_item_url(correlation_name, value, correlation_type=None):
    '''
    Warning: use only in flask
    '''
    url = '#'
    if correlation_name == "pgp":
        endpoint = 'hashDecoded.show_pgpdump'
        url = url_for(endpoint, type_id=correlation_type, key_id=value)
    elif correlation_name == 'cryptocurrency':
        endpoint = 'hashDecoded.show_cryptocurrency'
        url = url_for(endpoint, type_id=correlation_type, key_id=value)
    elif correlation_name == 'decoded':
        endpoint = 'hashDecoded.showHash'
        url = url_for(endpoint, hash=value)
    elif correlation_name == 'domain':
        endpoint = 'crawler_splash.showDomain'
        url = url_for(endpoint, domain=value)
    elif correlation_name == 'paste':
        endpoint = 'showsavedpastes.showsavedpaste'
        url = url_for(endpoint, paste=value)
    return url


def create_graph_links(links_set):
    graph_links_list = []
    for link in links_set:
        graph_links_list.append({"source": link[0], "target": link[1]})
    return graph_links_list

def create_graph_nodes(nodes_set, root_node_id):
    graph_nodes_list = []
    for node_id in nodes_set:
        correlation_name, correlation_type, value = node_id.split(';', 3)
        dict_node = {"id": node_id}
        dict_node['style'] = get_correlation_node_icon(correlation_name, correlation_type, value)
        dict_node['text'] = value
        if node_id == root_node_id:
            dict_node["style"]["node_color"] = 'orange'
            dict_node["style"]["node_radius"] = 7
        dict_node['url'] = get_item_url(correlation_name, value, correlation_type)
        graph_nodes_list.append(dict_node)
    return graph_nodes_list

def create_node_id(correlation_name, value, correlation_type=''):
    if correlation_type is None:
        correlation_type = ''
    return '{};{};{}'.format(correlation_name, correlation_type, value)



# # TODO: filter by correlation type => bitcoin, mail, ...
def get_graph_node_object_correlation(object_type, root_value, mode, correlation_names, correlation_objects, max_nodes=300, requested_correl_type=None):
    links = set()
    nodes = set()

    root_node_id = create_node_id(object_type, root_value, requested_correl_type)
    nodes.add(root_node_id)

    root_correlation = get_object_correlation(object_type, root_value, correlation_names, correlation_objects, requested_correl_type=requested_correl_type)
    for correl in root_correlation:
        if correl in ('pgp', 'cryptocurrency'):
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
        if correl in ('decoded', 'domain', 'paste'):
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
                        if corr_obj in ('decoded', 'domain', 'paste'):
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

                        if corr_obj in ('pgp', 'cryptocurrency'):
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


    return {"nodes": create_graph_nodes(nodes, root_node_id), "links": create_graph_links(links)}



######## API EXPOSED ########


########  ########
