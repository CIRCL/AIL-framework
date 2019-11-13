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

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

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

# # TODO: refractor
# # get object description, return dict, used by correlation
# def get_object_desc(object_type, item_value, correlation_name, correlation_type=None):
#     if object_type=="domain":
#         return Domain.get_object_desc(item_value)
#     if object_type=="correlation":
#         return Domain.get_object_desc(item_value)
#     {"name": self.correlation_name, "type": correlation_type, "id": correlation_value, "object": correl_object}
#
#
# # # TODO: sanithyse dict_correlation_to_check
# def get_object_correlation(object, object_value, mode, nb_max_elem=400, dict_correlation_to_check=[], depth_limit=1):
#     '''
#     Return all correlation of a given item id.
#
#     :param l_items_to_correlate: list of dict
#     :type l_items_to_correlate: list
#     :param mode: correlation mode
#         mode == intersection, union
#             union: show all related objects
#             intersection: show only direct correlation
#     :type mode: str
#     :param nb_max_elem: max nb of nodes
#     :type nb_max_elem: int, optional
#
#
#     '''
#     dict_item_desc = {}
#     dict_correlation = object.get_correlation(value, dict_correlation_to_check)

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
    return '{};{};{}'.format(correlation_name, correlation_type, value)


def get_graph_node_domain_correlation(domain, mode, max_nodes=50):
    links = set()
    nodes = set()

    root_node_id = create_node_id('domain', domain)
    nodes.add(root_node_id)

    domain_correlation = Domain.get_domain_all_correlation(domain)
    for correl in domain_correlation:
        if correl in ('pgp', 'cryptocurrency'):
            for correl_type in domain_correlation[correl]:
                for correl_val in domain_correlation[correl][correl_type]:

                    # add correlation
                    correl_node_id = create_node_id(correl, correl_val, correl_type)

                    if mode=="union":
                        if len(nodes) > max_nodes:
                            break
                        nodes.add(correl_node_id)
                        links.add((root_node_id, correl_node_id))

                    # get PGP correlation
                    if correl=='pgp':
                        res = Pgp.pgp.get_correlation_obj_domain(correl_val, correlation_type=correl_type)    # change function for item ?
                    # get Cryptocurrency correlation
                    else:
                        res = Cryptocurrency.cryptocurrency.get_correlation_obj_domain(correl_val, correlation_type=correl_type)

                    # inter mode
                    if res:
                        for correl_key_val in res:
                            #filter root domain
                            if correl_key_val == domain:
                                continue

                            if len(nodes) > max_nodes:
                                break
                            new_corel_1 = create_node_id('domain', correl_key_val)
                            new_corel_2 = create_node_id(correl, correl_val, correl_type)
                            nodes.add(new_corel_1)
                            nodes.add(new_corel_2)
                            links.add((new_corel_1, new_corel_2))

                            if mode=="inter":
                                nodes.add(correl_node_id)
                                links.add((root_node_id, correl_node_id))
        if correl=='decoded':
            for correl_val in domain_correlation[correl]:

                correl_node_id = create_node_id(correl, correl_val)
                if mode=="union":
                    if len(nodes) > max_nodes:
                        break
                    nodes.add(correl_node_id)
                    links.add((root_node_id, correl_node_id))

                res = Decoded.get_decoded_domain_item(correl_val)
                if res:
                    for correl_key_val in res:
                        #filter root domain
                        if correl_key_val == domain:
                            continue

                        if len(nodes) > max_nodes:
                            break
                        new_corel_1 = create_node_id('domain', correl_key_val)
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
