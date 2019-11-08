#!/usr/bin/python3

"""
The ``Domain``
===================


"""

import os
import sys
import time
import redis
import random

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

def sanathyse_port(port, domain, domain_type, strict=False, current_port=None):
    '''
    Retun a port number, If the port number is invalid, a port of the provided domain is randomly selected
    '''
    try:
        port = int(port)
    except (TypeError, ValueError):
        if strict:
            port = current_port
        else:
            port = get_random_domain_port(domain, domain_type)
    return port

def is_domain_up(domain, domain_type):
    return r_serv_onion.hexists('{}_metadata:{}'.format(domain_type, domain), 'ports')

def get_domain_all_ports(domain, domain_type):
    '''
    Return a list of all crawled ports
    '''
    l_ports = r_serv_onion.hget('{}_metadata:{}'.format(domain_type, domain), 'ports')
    if l_ports:
        return l_ports.split(";")
    return []

def get_random_domain_port(domain, domain_type):
    return random.choice(get_domain_all_ports(domain, domain_type))

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

def get_domain_last_crawled_item_root(domain, domain_type, port):
    '''
    Retun last_crawled_item_core dict
    '''
    res = r_serv_onion.zrevrange('crawler_history_{}:{}:{}'.format(domain_type, domain, port), 0, 0, withscores=True)
    if res:
        return {"root_item": res[0][0], "epoch": int(res[0][1])}
    else:
        return {}

def get_domain_crawled_item_root(domain, domain_type, port, epoch=None):
    '''
    Retun the first item crawled for a given domain:port (and epoch)
    '''
    if epoch:
        res = r_serv_onion.zrevrangebyscore('crawler_history_{}:{}:{}'.format(domain_type, domain, port), int(epoch), int(epoch))
        if res:
            return {"root_item": res[0], "epoch": int(epoch)}
        # invalid epoch
        epoch = None

    if not epoch:
        return get_domain_last_crawled_item_root(domain, domain_type, port)


def get_domain_items_crawled(domain, domain_type, port, epoch=None, items_link=False, item_screenshot=False, item_tag=False):
    '''

    '''
    item_crawled = {}
    item_root = get_domain_crawled_item_root(domain, domain_type, port, epoch=epoch)
    if item_root:
        item_crawled['port'] = port
        item_crawled['epoch'] = item_root['epoch']
        item_crawled['date'] = time.strftime('%Y/%m/%d - %H:%M.%S', time.gmtime(item_root['epoch']))
        item_crawled['items'] = []
        for item in get_domain_items(domain, item_root['root_item']):
            dict_item = {"id": item}
            if items_link:
                dict_item['link'] = Item.get_item_link(item)
            if item_screenshot:
                dict_item['screenshot'] = Item.get_item_screenshot(item)
            if item_tag:
                dict_item['tags'] = Tag.get_item_tags_minimal(item)
            item_crawled['items'].append(dict_item)
    return item_crawled

def get_link_tree():
    pass

def get_domain_last_check(domain, domain_type=None, r_format="str"):
    '''
    Get domain last check date

    :param domain: crawled domain
    :type domain: str
    :param domain_type: domain type
    :type domain_type: str

    :return: domain last check date
    :rtype: str
    '''
    if not domain_type:
        domain_type = get_domain_type(domain)
    last_check = r_serv_onion.hget('{}_metadata:{}'.format(domain_type, domain), 'last_check')
    if last_check is not None:
        if r_format=="int":
            last_check = int(last_check)
        # str
        else:
            last_check = '{}/{}/{}'.format(last_check[0:4], last_check[4:6], last_check[6:8])
    return last_check

def get_domain_last_origin(domain, domain_type):
    '''
    Get domain last origin

    :param domain: crawled domain
    :type domain: str
    :param domain_type: domain type
    :type domain_type: str

    :return: last orgin item_id
    :rtype: str
    '''
    origin_item = r_serv_onion.hget('{}_metadata:{}'.format(domain_type, domain), 'paste_parent')
    return origin_item

def get_domain_tags(domain):
    '''
    Retun all tags of a given domain.

    :param domain: crawled domain
    '''
    return Tag.get_item_tags(domain)

def get_domain_cryptocurrency(domain, currencies_type=None, get_nb=False):
    '''
    Retun all cryptocurrencies of a given domain.

    :param domain: crawled domain
    :param currencies_type: list of cryptocurrencies type
    :type currencies_type: list, optional
    '''
    return cryptocurrency.get_domain_correlation_dict(domain, correlation_type=currencies_type, get_nb=get_nb)

def get_domain_pgp(domain, currencies_type=None, get_nb=False):
    '''
    Retun all pgp of a given domain.

    :param domain: crawled domain
    :param currencies_type: list of pgp type
    :type currencies_type: list, optional
    '''
    return pgp.get_domain_correlation_dict(domain, correlation_type=currencies_type, get_nb=get_nb)

def get_domain_all_correlation(domain, correlation_type=None, get_nb=False):
    '''
    Retun all correlation of a given domain.

    :param domain: crawled domain
    :type domain: str

    :return: a dict of all correlation for a given domain
    :rtype: dict
    '''
    domain_correl = {}
    res = get_domain_cryptocurrency(domain, get_nb=get_nb)
    if res:
        domain_correl['cryptocurrency'] = res
    res = get_domain_pgp(domain, get_nb=get_nb)
    if res:
        domain_correl['pgp'] = res
    return domain_correl

 # TODO: handle port
def get_domain_history(domain, domain_type, port): # TODO: add date_range: from to + nb_elem
    '''
    Retun .

    :param domain: crawled domain
    :type domain: str

    :return:
    :rtype: list of tuple (item_core, epoch)
    '''
    return r_serv_onion.zrange('crawler_history_{}:{}:{}'.format(domain_type, domain, port), 0, -1, withscores=True)

def get_domain_history_with_status(domain, domain_type, port): # TODO: add date_range: from to + nb_elem
    '''
    Retun .

    :param domain: crawled domain
    :type domain: str

    :return:
    :rtype: list of dict (epoch, date: %Y/%m/%d - %H:%M.%S, boolean status)
    '''
    l_history = []
    history = get_domain_history(domain, domain_type, port)
    for root_item, epoch_val in history:
        epoch_val = int(epoch_val) # force int
        # domain down, root_item==epoch_val
        try:
            int(root_item)
            status = False
        # domain up, root_item=str
        except ValueError:
            status = True
        l_history.append({"epoch": epoch_val, "date": time.strftime('%Y/%m/%d - %H:%M.%S', time.gmtime(epoch_val)), "status": status})
    return l_history

def verify_if_domain_exist(domain):
    return r_serv_onion.exists('{}_metadata:{}'.format(get_domain_type(domain), domain))

def api_verify_if_domain_exist(domain):
    if not verify_if_domain_exist(domain):
        return ({'status': 'error', 'reason': 'Unknow Domain'}, 404)
    else:
        return None

class Domain(object):
    """docstring for Domain."""

    def __init__(self, domain, port=None):
        self.domain = str(domain)
        self.type = get_domain_type(domain)
        if self.is_domain_up():
            self.current_port = sanathyse_port(port, self.domain, self.type)

    def get_current_port(self):
        return self.current_port

    def get_domain_first_seen(self):
        '''
        Get domain first seen date

        :return: domain first seen date
        :rtype: str
        '''
        first_seen = r_serv_onion.hget('{}_metadata:{}'.format(self.type, self.domain), 'first_seen')
        if first_seen is not None:
            first_seen = '{}/{}/{}'.format(first_seen[0:4], first_seen[4:6], first_seen[6:8])
        return first_seen

    def get_domain_last_check(self):
        '''
        Get domain last check date

        :return: domain last check date
        :rtype: str
        '''
        return get_domain_last_check(self.domain, domain_type=self.type)

    def get_domain_last_origin(self):
        '''
        Get domain last origin

        :param domain: crawled domain
        :type domain: str
        :param domain_type: domain type
        :type domain_type: str

        :return: last orgin item_id
        :rtype: str
        '''
        return get_domain_last_origin(self.domain, self.type)

    def is_domain_up(self): # # TODO: handle multiple ports
        '''
        Return True if this domain is UP
        '''
        return is_domain_up(self.domain, self.type)

    def get_domain_all_ports(self):
        return get_domain_all_ports(self.domain, self.type)

    def get_domain_metadata(self, first_seen=True, last_ckeck=True, status=True, ports=True):
        '''
        Get Domain basic metadata

        :param first_seen: get domain first_seen
        :type first_seen: boolean
        :param last_ckeck: get domain last_check
        :type last_ckeck: boolean
        :param ports: get all domain ports
        :type ports: boolean

        :return: a dict of all metadata for a given domain
        :rtype: dict
        '''
        dict_metadata = {}
        if first_seen:
            res = self.get_domain_first_seen()
            if res is not None:
                dict_metadata['first_seen'] = res
        if last_ckeck:
            res = self.get_domain_last_check()
            if res is not None:
                dict_metadata['last_check'] = res
        if status:
            dict_metadata['status'] = self.is_domain_up()
        if ports:
            dict_metadata['ports'] = self.get_domain_all_ports()
        return dict_metadata

    def get_domain_tags(self):
        '''
        Retun all tags of a given domain.

        :param domain: crawled domain
        '''
        return get_domain_tags(self.domain)

    def get_domain_correlation(self):
        '''
        Retun all cryptocurrencies of a given domain.
        '''
        return get_domain_all_correlation(self.domain, get_nb=True)

    def get_domain_history_with_status(self):
        '''
        Retun the full history of a given domain and port.
        '''
        return get_domain_history_with_status(self.domain, self.type, 80)

    def get_domain_items_crawled(self, port=None, epoch=None, items_link=False, item_screenshot=False, item_tag=False):
        '''
        Return ........................
        '''
        port = sanathyse_port(port, self.domain, self.type, strict=True, current_port=self.current_port)
        return get_domain_items_crawled(self.domain, self.type, port, epoch=epoch, items_link=items_link, item_screenshot=item_screenshot, item_tag=item_tag)
