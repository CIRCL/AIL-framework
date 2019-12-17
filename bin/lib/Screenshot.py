#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis


sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item
import Date


import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
SCREENSHOT_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "crawled_screenshot"), 'screenshot')
config_loader = None

# get screenshot relative path
def get_screenshot_rel_path(sha256_string, add_extension=False):
    screenshot_path =  os.path.join(sha256_string[0:2], sha256_string[2:4], sha256_string[4:6], sha256_string[6:8], sha256_string[8:10], sha256_string[10:12], sha256_string[12:])
    if add_extension:
        screenshot_path = screenshot_path + '.png'
    return screenshot_path

def exist_screenshot(sha256_string):
    screenshot_path = os.path.join(SCREENSHOT_FOLDER, get_screenshot_rel_path(sha256_string, add_extension=True))
    return os.path.isfile(screenshot_path)

def get_metadata(sha256_string):
    metadata_dict = {}
    metadata_dict['sha256'] = sha256_string
    return metadata_dict


def get_screenshot_items_list(sha256_string):
    res = r_serv_onion.smembers('screenshot:{}'.format(sha256_string))
    if res:
        return list(res)
    else:
        return []

def get_item_screenshot_list(item_id):
    '''
    Retun all decoded item of a given item id.

    :param item_id: item id
    '''
    screenshot = r_serv_metadata.hget('paste_metadata:{}'.format(item_id), 'screenshot')
    if screenshot:
        return [screenshot]
    else:
        return []

def get_domain_screenshot(domain):
    '''
    Retun all screenshot of a given domain.

    :param domain: crawled domain
    '''
    res = r_serv_onion.smembers('domain_screenshot:{}'.format(domain))
    if res:
        return list(res)
    else:
        return []

def get_screenshot_domain(sha256_string):
    '''
    Retun all domain of a given screenshot.

    :param sha256_string: sha256_string
    '''
    res = r_serv_onion.smembers('screenshot_domain:{}'.format(sha256_string))
    if res:
        return list(res)
    else:
        return []

def get_screenshot_correlated_object(sha256_string, correlation_objects=[]):
    '''
    Retun all correlation of a given sha256.

    :param sha1_string: sha256
    :type sha1_string: str

    :return: a dict of all correlation for a given sha256
    :rtype: dict
    '''
    if correlation_objects is None:
        correlation_objects = Correlation.get_all_correlation_objects()
    decoded_correlation = {}
    for correlation_object in correlation_objects:
        if correlation_object == 'paste':
            res = get_screenshot_items_list(sha256_string)
        elif correlation_object == 'domain':
            res = get_screenshot_domain(sha256_string)
        else:
            res = None
        if res:
            decoded_correlation[correlation_object] = res
    return decoded_correlation
