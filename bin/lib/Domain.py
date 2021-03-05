#!/usr/bin/python3

"""
The ``Domain``
===================


"""

import os
import sys
import itertools
import re
import redis
import random
import time

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Cryptocurrency
import Pgp
import Date
import Decoded
import Item
import Tag

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import Correlate_object
import Language
import Screenshot
import Username

config_loader = ConfigLoader.ConfigLoader()
r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
config_loader = None


######## DB KEYS ########
def get_db_keys_domain_up(domain_type, date_type): # sanitise domain_type
    # get key name
    if date_type=='day':
        key_value = "{}_up:".format(domain_type)
        key_value += "{}"
    elif date_type=='month':
        key_value = "month_{}_up:".format(domain_type)
        key_value += "{}"
    else:
        key_value = None
    return key_value

def get_list_db_keys_domain_up(domain_type, l_dates, date_type):
    l_keys_name = []
    if domain_type=='all':
        domains_types = get_all_domains_type()
    else:
        domains_types = [domain_type]

    for dom_type in domains_types:
        key_name = get_db_keys_domain_up(dom_type, date_type)
        if key_name:
            for str_date in l_dates:
                l_keys_name.append(key_name.format(str_date))
    return l_keys_name

######## UTIL ########
def sanitize_domain_type(domain_type):
    if domain_type in get_all_domains_type():
        return domain_type
    else:
        return 'regular'

def sanitize_domain_types(l_domain_type):
    all_domain_types = get_all_domains_type()
    if not l_domain_type:
        return all_domain_types
    for domain_type in l_domain_type:
        if domain_type not in all_domain_types:
            return all_domain_types
    return l_domain_type

######## DOMAINS ########
def get_all_domains_type():
    return ['onion', 'regular']

def get_all_domains_up(domain_type, r_list=True):
    '''
    Get all domain up (at least one time)

    :param domain_type: domain type
    :type domain_type: str

    :return: list of domain
    :rtype: list
    '''
    domains = r_serv_onion.smembers("full_{}_up".format(domain_type))
    if r_list:
        if domains:
            list(domains)
        else:
            domains = []
    return domains

def get_domains_up_by_month(date_year_month, domain_type, rlist=False):
    '''
    Get all domain up (at least one time)

    :param domain_type: date_year_month YYYYMM
    :type domain_type: str

    :return: list of domain
    :rtype: list
    '''
    res = r_serv_onion.smembers( get_db_keys_domain_up(domain_type, "month").format(date_year_month) )
    if rlist:
        return list(res)
    else:
        return res

def get_domain_up_by_day(date_year_month, domain_type, rlist=False):
    '''
    Get all domain up (at least one time)

    :param domain_type: date YYYYMMDD
    :type domain_type: str

    :return: list of domain
    :rtype: list
    '''
    res = r_serv_onion.smembers(get_db_keys_domain_up(domain_type, "day").format(date_year_month))
    if rlist:
        return list(res)
    else:
        return res

def get_domains_up_by_daterange(date_from, date_to, domain_type):
    '''
    Get all domain up (at least one time) by daterange

    :param domain_type: domain_type
    :type domain_type: str

    :return: list of domain
    :rtype: list
    '''
    days_list, month_list = Date.get_date_range_full_month_and_days(date_from, date_to)
    l_keys_name = get_list_db_keys_domain_up(domain_type, days_list, 'day')
    l_keys_name.extend(get_list_db_keys_domain_up(domain_type, month_list, 'month'))

    if len(l_keys_name) > 1:
        domains_up = list(r_serv_onion.sunion(l_keys_name[0], *l_keys_name[1:]))
    elif l_keys_name:
        domains_up = list(r_serv_onion.smembers(l_keys_name[0]))
    else:
        domains_up = []
    return domains_up

def paginate_iterator(iter_elems, nb_obj=50, page=1):
    dict_page = {}
    dict_page['nb_all_elem'] = len(iter_elems)
    nb_pages = dict_page['nb_all_elem'] / nb_obj
    if not nb_pages.is_integer():
        nb_pages = int(nb_pages)+1
    else:
        nb_pages = int(nb_pages)
    if page > nb_pages:
        page = nb_pages

    # multiple pages
    if nb_pages > 1:
        dict_page['list_elem'] = []
        start = nb_obj*(page -1)
        stop = (nb_obj*page) -1
        current_index = 0
        for elem in iter_elems:
            if current_index > stop:
                break
            if start <= current_index and stop >= current_index:
                dict_page['list_elem'].append(elem)
            current_index += 1
        stop += 1
        if stop > dict_page['nb_all_elem']:
            stop = dict_page['nb_all_elem']

    else:
        start = 0
        stop = dict_page['nb_all_elem']
        dict_page['list_elem'] = list(iter_elems)
    dict_page['page'] = page
    dict_page['nb_pages'] = nb_pages
    # UI
    dict_page['nb_first_elem'] = start+1
    dict_page['nb_last_elem'] = stop
    return dict_page

def domains_up_by_page(domain_type, nb_obj=28, page=1):
    '''
    Get a list of domains up (alpha sorted)

    :param domain_type: domain type
    :type domain_type: str

    :return: list of domain
    :rtype: list
    '''
    domains = sorted(get_all_domains_up(domain_type, r_list=False))
    domains = paginate_iterator(domains, nb_obj=nb_obj, page=page)
    domains['list_elem'] = create_domains_metadata_list(domains['list_elem'], domain_type)
    return domains

def get_domains_up_by_filers(domain_type, date_from=None, date_to=None, tags=[], nb_obj=28, page=1):
    if not tags:
        if not date_from and not date_to:
            return domains_up_by_page(domain_type, nb_obj=nb_obj, page=page)
        else:
            domains = sorted(get_domains_up_by_daterange(date_from, date_to, domain_type))
            domains = paginate_iterator(domains, nb_obj=nb_obj, page=page)
            domains['list_elem'] = create_domains_metadata_list(domains['list_elem'], domain_type)
            domains['domain_type'] = domain_type
            domains['date_from'] = date_from
            domains['date_to'] = date_to
            return domains
    else:
        return None



## TODO: filters:
#                   - tags
#                   - languages
#                   - daterange UP
def get_domains_by_filters():
    pass

def create_domains_metadata_list(list_domains, domain_type):
    l_domains = []
    for domain in list_domains:
        if domain_type=='all':
            dom_type = get_domain_type(domain)
        else:
            dom_type = domain_type
        l_domains.append(get_domain_metadata(domain, dom_type, first_seen=True, last_ckeck=True, status=True,
                            ports=True, tags=True, languages=True, screenshot=True, tags_safe=True))
    return l_domains

def sanithyse_domain_name_to_search(name_to_search, domain_type):
    if domain_type == 'onion':
        r_name = r'[a-z0-9\.]+'
    else:
        r_name = r'[a-zA-Z0-9-_\.]+'
    # invalid domain name
    if not re.fullmatch(r_name, name_to_search):
        res = re.match(r_name, name_to_search)
        return {'search': name_to_search, 'error': res.string.replace( res[0], '')}
    return name_to_search.replace('.', '\.')


def search_domains_by_name(name_to_search, domain_types, r_pos=False):
    domains_dict = {}
    for domain_type in domain_types:
        r_name = sanithyse_domain_name_to_search(name_to_search, domain_type)
        if not name_to_search or isinstance(r_name, dict):
            break
        r_name = re.compile(r_name)
        for domain in get_all_domains_up(domain_type):
            res = re.search(r_name, domain)
            if res:
                domains_dict[domain] = {}
                if r_pos:
                    domains_dict[domain]['hl-start'] = res.start()
                    domains_dict[domain]['hl-end'] = res.end()
    return domains_dict

def api_sanithyse_domain_name_to_search(name_to_search, domains_types):
    domains_types = sanitize_domain_types(domains_types)
    for domain_type in domains_types:
        r_name = sanithyse_domain_name_to_search(name_to_search, domain_type)
        if isinstance(r_name, dict):
            return ({'error': 'Invalid'}, 400)


def api_search_domains_by_name(name_to_search, domains_types, domains_metadata=False, page=1):
    domains_types = sanitize_domain_types(domains_types)
    domains_dict = search_domains_by_name(name_to_search, domains_types, r_pos=True)
    l_domains = sorted(domains_dict.keys())
    l_domains = paginate_iterator(l_domains, nb_obj=28, page=page)
    if not domains_metadata:
        return l_domains
    else:
        l_dict_domains = []
        for domain in l_domains['list_elem']:
            dict_domain = get_domain_metadata(domain, get_domain_type(domain), first_seen=True, last_ckeck=True,
                                                        status=True, ports=True, tags=True, tags_safe=True,
                                                        languages=True, screenshot=True)
            dict_domain = {**domains_dict[domain], **dict_domain}
            l_dict_domains.append(dict_domain)
        l_domains['list_elem'] = l_dict_domains
        l_domains['search'] = name_to_search
        return l_domains


######## LANGUAGES ########
def get_all_domains_languages():
    return r_serv_onion.smembers('all_domains_languages')

def get_domains_by_languages(languages, l_domain_type=[]):
    l_domain_type = sanitize_domain_types(l_domain_type)
    if not languages:
        return []
    elif len(languages) == 1:
        return get_all_domains_by_language(languages[0], l_domain_type=l_domain_type)
    else:
        all_domains_t = []
        for domain_type in l_domain_type:
            l_keys_name = []
            for language in languages:
                l_keys_name.append('language:domains:{}:{}'.format(domain_type, language))
            res = r_serv_onion.sinter(l_keys_name[0], *l_keys_name[1:])
            if res:
                all_domains_t.append(res)
        return list(itertools.chain.from_iterable(all_domains_t))

def get_all_domains_by_language(language, l_domain_type=[]):
    l_domain_type = sanitize_domain_types(l_domain_type)
    if len(l_domain_type) == 1:
        return r_serv_onion.smembers('language:domains:{}:{}'.format(l_domain_type[0], language))
    else:
        l_keys_name = []
        for domain_type in l_domain_type:
            l_keys_name.append('language:domains:{}:{}'.format(domain_type, language))
        return r_serv_onion.sunion(l_keys_name[0], *l_keys_name[1:])

def get_domain_languages(domain, r_list=False):
    res = r_serv_onion.smembers('domain:language:{}'.format(domain))
    if r_list:
        return list(res)
    else:
        return res

def add_domain_language(domain, language):
    language = language.split('-')[0]
    domain_type = get_domain_type(domain)
    r_serv_onion.sadd('all_domains_languages', language)
    r_serv_onion.sadd('all_domains_languages:{}'.format(domain_type), language)
    r_serv_onion.sadd('language:domains:{}:{}'.format(domain_type, language), domain)
    r_serv_onion.sadd('domain:language:{}'.format(domain), language)

def add_domain_languages_by_item_id(domain, item_id):
    for lang in Item.get_item_languages(item_id, min_proportion=0.2, min_probability=0.8):
        add_domain_language(domain, lang.language)

def delete_domain_languages(domain):
    domain_type = get_domain_type(domain)
    for language in get_domain_languages(domain):
        r_serv_onion.srem('language:domains:{}:{}'.format(domain_type, language), domain)
        if not r_serv_onion.exists('language:domains:{}:{}'.format(domain_type, language)):
            r_serv_onion.srem('all_domains_languages:{}'.format(domain_type), language)
            exist_domain_type_lang = False
            for domain_type in get_all_domains_type():
                if r_serv_onion.sismembers('all_domains_languages:{}'.format(domain_type), language):
                    exist_domain_type_lang = True
                    continue
            if not exist_domain_type_lang:
                r_serv_onion.srem('all_domains_languages', language)
    r_serv_onion.delete('domain:language:{}'.format(domain))

def _delete_all_domains_languages():
    for language in get_all_domains_languages():
        for domain in get_all_domains_by_language(language):
            delete_domain_languages(domain)

## API ##
## TODO: verify domains type + languages list
## TODO: add pagination
def api_get_domains_by_languages(domains_types, languages, domains_metadata=False, page=1):
    l_domains = sorted(get_domains_by_languages(languages, l_domain_type=domains_types))
    l_domains = paginate_iterator(l_domains, nb_obj=28, page=page)
    if not domains_metadata:
        return l_domains
    else:
        l_dict_domains = []
        for domain in l_domains['list_elem']:
            l_dict_domains.append(get_domain_metadata(domain, get_domain_type(domain), first_seen=True, last_ckeck=True,
                                                        status=True, ports=True, tags=True, tags_safe=True,
                                                        languages=True, screenshot=True))
        l_domains['list_elem'] = l_dict_domains
        return l_domains
####---- ----####

######## DOMAIN ########

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

def domain_was_up(domain, domain_type):
    return r_serv_onion.hexists('{}_metadata:{}'.format(domain_type, domain), 'ports')

def is_domain_up(domain, domain_type, ports=[]):
    if not ports:
        ports = get_domain_all_ports(domain, domain_type)
    for port in ports:
        res = r_serv_onion.zrevrange('crawler_history_{}:{}:{}'.format(domain_type, domain, port), 0, 0, withscores=True)
        if res:
            item_core, epoch = res[0]
            epoch = int(epoch)
            if item_core != str(epoch):
                return True
    return False

def get_domain_first_up(domain, domain_type, ports=None):
    '''
    Get all domain up (at least one time)

    :param ports: list of ports, optional
    :type ports: list

    :return: domain last up epoch
    :rtype: int
    '''
    if ports is None:
        ports = get_domain_all_ports(domain, domain_type)
    epoch_min = None
    for port in ports:
        res = r_serv_onion.zrange('crawler_history_{}:{}:{}'.format(domain_type, domain, port), 0, 0, withscores=True)[0]
        if not epoch_min:
            epoch_min = int(res[1])
        elif res[1] < epoch_min:
            epoch_min = int(res[1])
    return epoch_min

def get_last_domain_up_by_port(domain, domain_type, port):
    current_index = 0
    while True:
        res = r_serv_onion.zrevrange('crawler_history_{}:{}:{}'.format(domain_type, domain, port), current_index, current_index, withscores=True)
        # history found
        if res:
            item_core, epoch = res[0]
            epoch = int(epoch)
            if item_core == str(epoch):
                current_index +=1
            else:
                return epoch
        else:
            return None

def get_domain_last_up(domain, domain_type, ports=None):
    if ports is None:
        ports = get_domain_all_ports(domain, domain_type)
    epoch_max = 0
    for port in ports:
        last_epoch_up = get_last_domain_up_by_port(domain, domain_type, port)
        if last_epoch_up > epoch_max:
            epoch_max = last_epoch_up
    return epoch_max

def get_domain_up_range(domain, domain_type):
    domain_metadata = {}
    domain_metadata['first_seen'] = get_domain_first_up(domain, domain_type)
    domain_metadata['last_seen'] = get_domain_last_up(domain, domain_type)
    return domain_metadata

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

def get_domain_all_url(domain, domain_type, domain_ports=None):
    if not domain_ports:
        domain_ports = get_domain_all_ports(domain, domain_type)
    all_url = {}
    for port in domain_ports:
        for dict_history in get_domain_history_with_status(domain, domain_type, port, add_root_item=True):
            if dict_history['status']: # domain UP
                crawled_items = get_domain_items(domain, dict_history['root_item'])
                for item_id in crawled_items:
                    item_url = Item.get_item_link(item_id)
                    item_date = int(Item.get_item_date(item_id))
                    if item_url:
                        if item_url not in all_url:
                            all_url[item_url] = {'first_seen': item_date,'last_seen': item_date}
                        else: # update first_seen / last_seen
                            if item_date < all_url[item_url]['first_seen']:
                                all_url[item_url]['first_seen'] = item_date
                            if item_date > all_url[item_url]['last_seen']:
                                all_url[item_url]['last_seen'] = item_date
    return all_url


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
        if item_root['root_item'] != str(item_root['epoch']):
            for item in get_domain_items(domain, item_root['root_item']):
                dict_item = {"id": item}
                if items_link:
                    dict_item['link'] = Item.get_item_link(item)
                if item_screenshot:
                    dict_item['screenshot'] = Item.get_item_screenshot(item)
                if item_tag:
                    dict_item['tags'] = Tag.get_obj_tags_minimal(item)
                item_crawled['items'].append(dict_item)
    return item_crawled

def get_link_tree():
    pass

def get_domain_first_seen(domain, domain_type=None, r_format="str"):
    '''
    Get domain first seen date

    :param domain: crawled domain
    :type domain: str
    :param domain_type: domain type
    :type domain_type: str

    :return: domain first seen date
    :rtype: str
    '''
    if not domain_type:
        domain_type = get_domain_type(domain)
    first_seen = r_serv_onion.hget('{}_metadata:{}'.format(domain_type, domain), 'first_seen')
    if first_seen is not None:
        if r_format=="int":
            first_seen = int(first_seen)
        else:
            first_seen = '{}/{}/{}'.format(first_seen[0:4], first_seen[4:6], first_seen[6:8])
    return first_seen

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

def get_domain_father(domain, domain_type):
    dict_father = {}
    dict_father['item_father'] = r_serv_onion.hget('{}_metadata:{}'.format(domain_type, domain), 'paste_parent')
    if dict_father['item_father'] != 'auto' and dict_father['item_father'] != 'manual':
        if Item.is_crawled(dict_father['item_father']):
            dict_father['domain_father'] = Item.get_domain(dict_father['item_father'])
    return dict_father

def get_domain_tags(domain):
    '''
    Retun all tags of a given domain.

    :param domain: crawled domain
    '''
    return Tag.get_obj_tag(domain)

def get_domain_random_screenshot(domain):
    '''
    Retun last screenshot (core item).

    :param domain: crawled domain
    '''
    return Screenshot.get_randon_domain_screenshot(domain)

def get_domain_metadata(domain, domain_type, first_seen=True, last_ckeck=True, status=True, ports=True, tags=False, tags_safe=False, languages=False, screenshot=False):
    '''
    Get Domain basic metadata

    :param first_seen: get domain first_seen
    :type first_seen: boolean
    :param last_ckeck: get domain last_check
    :type last_ckeck: boolean
    :param ports: get all domain ports
    :type ports: boolean
    :param tags: get all domain tags
    :type tags: boolean

    :return: a dict of all metadata for a given domain
    :rtype: dict
    '''
    dict_metadata = {}
    dict_metadata['id'] = domain
    dict_metadata['type'] = domain_type
    if first_seen:
        res = get_domain_first_seen(domain, domain_type=domain_type)
        if res is not None:
            dict_metadata['first_seen'] = res
    if last_ckeck:
        res = get_domain_last_check(domain, domain_type=domain_type)
        if res is not None:
            dict_metadata['last_check'] = res
    if status:
        dict_metadata['status'] = is_domain_up(domain, domain_type)
    if ports:
        dict_metadata['ports'] = get_domain_all_ports(domain, domain_type)
    if tags:
        dict_metadata['tags'] = get_domain_tags(domain)
    if tags_safe:
        if tags:
            dict_metadata['is_tags_safe'] = Tag.is_tags_safe(dict_metadata['tags'])
        else:
            dict_metadata['is_tags_safe'] = Tag.is_tags_safe(get_domain_tags(domain))
    if languages:
        dict_metadata['languages'] = Language.get_languages_from_iso(get_domain_languages(domain, r_list=True), sort=True)
    if screenshot:
        dict_metadata['screenshot'] = get_domain_random_screenshot(domain)
    return dict_metadata

def get_domain_metadata_basic(domain, domain_type=None):
    if not domain_type:
        domain_type = get_domain_type(domain)
    return get_domain_metadata(domain, domain_type, first_seen=True, last_ckeck=True, status=True, ports=False)

def get_domain_cryptocurrency(domain, currencies_type=None, get_nb=False):
    '''
    Retun all cryptocurrencies of a given domain.

    :param domain: crawled domain
    :param currencies_type: list of cryptocurrencies type
    :type currencies_type: list, optional
    '''
    return Cryptocurrency.cryptocurrency.get_domain_correlation_dict(domain, correlation_type=currencies_type, get_nb=get_nb)

def get_domain_pgp(domain, currencies_type=None, get_nb=False):
    '''
    Retun all pgp of a given domain.

    :param domain: crawled domain
    :param currencies_type: list of pgp type
    :type currencies_type: list, optional
    '''
    return Pgp.pgp.get_domain_correlation_dict(domain, correlation_type=currencies_type, get_nb=get_nb)

def get_domain_username(domain, currencies_type=None, get_nb=False):
    '''
    Retun all pgp of a given domain.

    :param domain: crawled domain
    :param currencies_type: list of pgp type
    :type currencies_type: list, optional
    '''
    return Username.correlation.get_domain_correlation_dict(domain, correlation_type=currencies_type, get_nb=get_nb)

def get_domain_decoded(domain):
    '''
    Retun all decoded item of a given domain.

    :param domain: crawled domain
    '''
    return Decoded.get_domain_decoded_item(domain)

def get_domain_screenshot(domain):
    '''
    Retun all decoded item of a given domain.

    :param domain: crawled domain
    '''
    return Screenshot.get_domain_screenshot(domain)


def get_domain_all_correlation(domain, correlation_names=[], get_nb=False):
    '''
    Retun all correlation of a given domain.

    :param domain: crawled domain
    :type domain: str

    :return: a dict of all correlation for a given domain
    :rtype: dict
    '''
    if not correlation_names:
        correlation_names = Correlate_object.get_all_correlation_names()
    domain_correl = {}
    for correlation_name in correlation_names:
        if correlation_name=='cryptocurrency':
            res = get_domain_cryptocurrency(domain, get_nb=get_nb)
        elif correlation_name=='pgp':
            res = get_domain_pgp(domain, get_nb=get_nb)
        elif correlation_name=='username':
            res = get_domain_username(domain, get_nb=get_nb)
        elif correlation_name=='decoded':
            res = get_domain_decoded(domain)
        elif correlation_name=='screenshot':
            res = get_domain_screenshot(domain)
        else:
            res = None
        # add correllation to dict
        if res:
            domain_correl[correlation_name] = res

    return domain_correl

def get_domain_total_nb_correlation(correlation_dict):
    total_correlation = 0
    if 'decoded' in correlation_dict:
        total_correlation += len(correlation_dict['decoded'])
    if 'screenshot' in correlation_dict:
        total_correlation += len(correlation_dict['screenshot'])
    if 'cryptocurrency' in correlation_dict:
        total_correlation += correlation_dict['cryptocurrency'].get('nb', 0)
    if 'pgp' in correlation_dict:
        total_correlation += correlation_dict['pgp'].get('nb', 0)
    return total_correlation

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

def get_domain_history_with_status(domain, domain_type, port, add_root_item=False): # TODO: add date_range: from to + nb_elem
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
        dict_history = {"epoch": epoch_val, "date": time.strftime('%Y/%m/%d - %H:%M.%S', time.gmtime(epoch_val))}
        # domain down, root_item==epoch_val
        try:
            int(root_item)
            dict_history['status'] = False
        # domain up, root_item=str
        except ValueError:
            dict_history['status'] = True
            if add_root_item:
                dict_history['root_item'] = root_item
        l_history.append(dict_history)
    return l_history

def verify_if_domain_exist(domain):
    return r_serv_onion.exists('{}_metadata:{}'.format(get_domain_type(domain), domain))

## API ##

def api_verify_if_domain_exist(domain):
    if not verify_if_domain_exist(domain):
        return {'status': 'error', 'reason': 'Domain not found'}, 404
    else:
        return None

def api_get_domain_up_range(domain, domain_type=None):
    res = api_verify_if_domain_exist(domain)
    if res:
        return res
    if not domain_type:
        domain_type = get_domain_type(domain)
    res = get_domain_up_range(domain, domain_type)
    res['domain'] = domain
    return res, 200

def api_get_domains_by_status_daterange(date_from, date_to, domain_type):
    sanitize_domain_type(domain_type)
    res = {'domains': get_domains_up_by_daterange(date_from, date_to, domain_type)}
    return res, 200

## CLASS ##
class Domain(object):
    """docstring for Domain."""

    def __init__(self, domain, port=None):
        self.domain = str(domain)
        self.type = get_domain_type(domain)
        if self.domain_was_up():
            self.current_port = sanathyse_port(port, self.domain, self.type)

    def get_domain_name(self):
        return self.domain

    def get_domain_type(self):
        return self.type

    def get_current_port(self):
        return self.current_port

    def get_domain_first_seen(self):
        '''
        Get domain first seen date

        :return: domain first seen date
        :rtype: str
        '''
        return get_domain_first_seen(self.domain, domain_type=self.type)

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

    def get_domain_father(self):
        return get_domain_father(self.domain, self.type)

    def domain_was_up(self):
        '''
        Return True if this domain was UP at least one time
        '''
        return domain_was_up(self.domain, self.type)

    def is_domain_up(self): # # TODO: handle multiple ports
        '''
        Return True if this domain is UP
        '''
        return is_domain_up(self.domain, self.type)

    def get_domain_all_ports(self):
        return get_domain_all_ports(self.domain, self.type)

    def get_domain_metadata(self, first_seen=True, last_ckeck=True, status=True, ports=True, tags=False):
        '''
        Get Domain basic metadata

        :param first_seen: get domain first_seen
        :type first_seen: boolean
        :param last_ckeck: get domain last_check
        :type last_ckeck: boolean
        :param ports: get all domain ports
        :type ports: boolean
        :param tags: get all domain tags
        :type tags: boolean

        :return: a dict of all metadata for a given domain
        :rtype: dict
        '''
        return get_domain_metadata(self.domain, self.type, first_seen=first_seen, last_ckeck=last_ckeck, status=status, ports=ports, tags=tags)

    def get_domain_tags(self):
        '''
        Retun all tags of a given domain.

        :param domain: crawled domain
        '''
        return get_domain_tags(self.domain)

    def get_domain_languages(self):
        '''
        Retun all languages of a given domain.

        :param domain: domain name
        '''
        return get_domain_languages(self.domain)

    def get_domain_correlation(self):
        '''
        Retun all correlation of a given domain.
        '''
        return get_domain_all_correlation(self.domain, get_nb=True)

    def get_domain_history(self):
        '''
        Retun the full history of a given domain and port.
        '''
        return get_domain_history(self.domain, self.type, 80)

    def get_domain_history_with_status(self):
        '''
        Retun the full history (with status) of a given domain and port.
        '''
        return get_domain_history_with_status(self.domain, self.type, 80)

    def get_domain_items_crawled(self, port=None, epoch=None, items_link=False, item_screenshot=False, item_tag=False):
        '''
        Return ........................
        '''
        port = sanathyse_port(port, self.domain, self.type, strict=True, current_port=self.current_port)
        return get_domain_items_crawled(self.domain, self.type, port, epoch=epoch, items_link=items_link, item_screenshot=item_screenshot, item_tag=item_tag)

if __name__ == '__main__':
    search_domains_by_name('c', 'onion')
