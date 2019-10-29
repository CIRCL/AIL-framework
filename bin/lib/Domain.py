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
import Cryptocurrency
import Item

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


###
### correlation
###
"""
def _get_domain_correlation(domain, correlation_name=None, correlation_type=None):
    res = r_serv_metadata.smembers('item_{}_{}:{}'.format(correlation_name, correlation_type, item_id))
    if res:
        return list(res)
    else:
        return []

def get_item_bitcoin(item_id):
    return _get_item_correlation('cryptocurrency', 'bitcoin', item_id)

def get_item_pgp_key(item_id):
    return _get_item_correlation('pgpdump', 'key', item_id)

def get_item_pgp_name(item_id):
    return _get_item_correlation('pgpdump', 'name', item_id)

def get_item_pgp_mail(item_id):
    return _get_item_correlation('pgpdump', 'mail', item_id)

def get_item_pgp_correlation(item_id):
    pass
"""

def _get_domain_correlation(domain, correlation_list):
    return Cryptocurrency.get_cryptocurrency_domain(domain)

class Domain(object):
    """docstring for Domain."""

    def __init__(self, domain, port=80):
        self.domain = str(domain)
        ## TODO: handle none port
        self.type = get_domain_type(domain)
