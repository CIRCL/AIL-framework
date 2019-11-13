#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis


sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item


import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

def get_decoded_item_type(sha1_string):
    '''
    Retun the estimed type of a given decoded item.

    :param sha1_string: sha1_string
    '''
    return r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'estimated_type')

def get_decoded_items_list(sha1_string):
    return r_serv_metadata.zrange('nb_seen_hash:{}'.format(sha1_string), 0, -1)

def get_item_decoded(item_id):
    '''
    Retun all decoded item of a given item id.

    :param item_id: item id
    '''
    res = r_serv_metadata.smembers('hash_paste:{}'.format(item_id))
    if res:
        return list(res)
    else:
        return []

def get_domain_decoded_item(domain):
    '''
    Retun all decoded item of a given domain.

    :param domain: crawled domain
    '''
    res = r_serv_metadata.smembers('hash_domain:{}'.format(domain))
    if res:
        return list(res)
    else:
        return []

def get_decoded_domain_item(sha1_string):
    '''
    Retun all domain of a given decoded item.

    :param sha1_string: sha1_string
    '''
    res = r_serv_metadata.smembers('domain_hash:{}'.format(sha1_string))
    if res:
        return list(res)
    else:
        return []

def get_decoded_correlated_object(sha1_string, correlation_objects=[]):
    '''
    Retun all correlation of a given sha1.

    :param sha1_string: sha1
    :type sha1_string: str

    :return: a dict of all correlation for a given sha1
    :rtype: dict
    '''
    if correlation_objects is None:
        correlation_objects = Correlation.get_all_correlation_objects()
    decoded_correlation = {}
    for correlation_object in correlation_objects:
        if correlation_object == 'paste':
            res = get_decoded_items_list(sha1_string)
        elif correlation_object == 'domain':
            res = get_decoded_domain_item(sha1_string)
        else:
            res = None
        if res:
            decoded_correlation[correlation_object] = res
    return decoded_correlation

def save_domain_decoded(domain, sha1_string):
    r_serv_metadata.sadd('hash_domain:{}'.format(domain), sha1_string) # domain - hash map
    r_serv_metadata.sadd('domain_hash:{}'.format(sha1_string), domain) # hash - domain ma
