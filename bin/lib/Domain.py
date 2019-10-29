#!/usr/bin/python3

"""
The ``Domain``
===================


"""

import os
import sys
import time
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Correlation
from Cryptocurrency import cryptocurrency
from Pgp import pgp
import Item
import Tag

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
config_loader = None

def get_domain_type(domain):
    if str(domain).endswith('.onion'):
        return 'onion'
    else:
        return 'regular'

def get_all_domain_up_by_type(domain_type):
    if domain_type in domains:
        list_domain = list(r_serv_onion.smembers('full_{}_up'.format(domain_type)))
        return ({'type': domain_type, 'domains': list_domain}, 200)
    else:
        return ({"status": "error", "reason": "Invalid domain type"}, 400)

def get_domain_items(domain, root_item_id):
    dom_item =  get_domain_item_children(domain, root_item_id)
    dom_item.append(root_item_id)
    return dom_item

def get_domain_item_children(domain, root_item_id):
    all_items = []
    for item_id in Item.get_item_children(root_item_id):
        if Item.is_item_in_domain(domain, item_id):
            all_items.append(item_id)
            all_items.extend(get_domain_item_children(domain, item_id))
    return all_items

def get_link_tree():
    pass


def get_domain_tags(domain):
    '''
    Retun all tags of a given domain.

    :param domain: crawled domain
    '''
    return Tag.get_item_tags(domain)

def get_domain_cryptocurrency(domain, currencies_type=None):
    '''
    Retun all cryptocurrencies of a given domain.

    :param domain: crawled domain
    :param currencies_type: list of cryptocurrencies type
    :type currencies_type: list, optional
    '''
    return cryptocurrency.get_domain_correlation_dict(domain, correlation_type=currencies_type)

def get_domain_pgp(domain, currencies_type=None):
    '''
    Retun all pgp of a given domain.

    :param domain: crawled domain
    :param currencies_type: list of pgp type
    :type currencies_type: list, optional
    '''
    return pgp.get_domain_correlation_dict(domain, correlation_type=currencies_type)

def get_domain_all_correlation(domain, correlation_type=None):
    '''
    Retun all correlation of a given domain.

    :param domain: crawled domain
    :type domain: str

    :return: a dict of all correlation for a given domain
    :rtype: dict
    '''
    domain_correl = {}
    res = get_domain_cryptocurrency(domain)
    if res:
        domain_correl['cryptocurrency'] = res
    res = get_domain_pgp(domain)
    if res:
        domain_correl['pgp'] = res
    return domain_correl


class Domain(object):
    """docstring for Domain."""

    def __init__(self, domain, port=80):
        self.domain = str(domain)
        ## TODO: handle none port
        self.type = get_domain_type(domain)
