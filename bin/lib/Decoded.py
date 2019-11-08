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

def _get_decoded_items_list(sha1_string):
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

def save_domain_decoded(domain, sha1_string):
    r_serv_metadata.sadd('hash_domain:{}'.format(domain), sha1_string) # domain - hash map
    r_serv_metadata.sadd('domain_hash:{}'.format(sha1_string), domain) # hash - domain ma

if __name__ == "__main__":
    #sha1_str = '1e4db5adc1334ad2c9762db9ff6b845ee6ddc223'
    #res = _get_decoded_items_list(sha1_str)
    #print(res)
    #print(len(res))

    res = get_domain_decoded_item('2222222dpg65ioqu.onion')
    print(res)
