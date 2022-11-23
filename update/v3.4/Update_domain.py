#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader
from lib.objects.Items import Item
from lib import Domain

def get_domain_type(domain_name):
    if str(domain_name).endswith('.onion'):
        return 'onion'
    else:
        return 'regular'

def add_domain_language(domain_name, language):
    language = language.split('-')[0]
    domain_type = get_domain_type(domain_name)
    r_serv_onion.sadd('all_domains_languages', language)
    r_serv_onion.sadd(f'all_domains_languages:{domain_type}', language)
    r_serv_onion.sadd(f'language:domains:{domain_type}:{language}', domain_name)
    r_serv_onion.sadd(f'domain:language:{domain_name}', language)

def add_domain_languages_by_item_id(domain_name, item_id):
    item = Item(item_id)
    for lang in item.get_languages():
        add_domain_language(domain_name, lang.language)

def update_update_stats():
    nb_updated = int(r_serv_db.get('update:nb_elem_converted'))
    progress = int((nb_updated * 100) / nb_elem_to_update)
    print(f'{nb_updated}/{nb_elem_to_update}    updated    {progress}%')
    r_serv_db.set('ail:current_background_script_stat', progress)

def update_domain_language(domain_obj, item_id):
    domain_name = domain_obj.get_domain_name()
    add_domain_languages_by_item_id(domain_name, item_id)

def get_domain_history(domain_type, domain_name):
    return r_serv_onion.zrange(f'crawler_history_{domain_type}:{domain_name}:80', 0, -1, withscores=True)


def get_item_children(item_id):
    return r_serv_metadata.smembers(f'paste_children:{item_id}')

def get_domain_items(domain_name, root_item_id):
    dom_item = get_domain_item_children(domain_name, root_item_id)
    dom_item.append(root_item_id)
    return dom_item

def is_item_in_domain(domain_name, item_id):
    is_in_domain = False
    domain_length = len(domain_name)
    if len(item_id) > (domain_length+48):
        if item_id[-36-domain_length:-36] == domain_name:
            is_in_domain = True
    return is_in_domain

def get_domain_item_children(domain_name, root_item_id):
    all_items = []
    for item_id in get_item_children(root_item_id):
        if is_item_in_domain(domain_name, item_id):
            all_items.append(item_id)
            all_items.extend(get_domain_item_children(domain_name, item_id))
    return all_items

def get_domain_crawled_item_root(domain_name, domain_type, epoch):
    res = r_serv_onion.zrevrangebyscore(f'crawler_history_{domain_type}:{domain_name}:80', int(epoch), int(epoch))
    return {"root_item": res[0], "epoch": int(epoch)}

def get_domain_items_crawled(domain_name, domain_type, epoch):
    item_crawled = []
    item_root = get_domain_crawled_item_root(domain_name, domain_type, epoch)
    if item_root:
        if item_root['root_item'] != str(item_root['epoch']) and item_root['root_item']:
            for item_id in get_domain_items(domain_name, item_root['root_item']):
                item_crawled.append(item_id)
    return item_crawled


if __name__ == '__main__':

    start_deb = time.time()
    config_loader = ConfigLoader.ConfigLoader()
    r_serv_db = config_loader.get_redis_conn("ARDB_DB")
    r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
    r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
    config_loader = None

    r_serv_db.set('ail:current_background_script', 'domain languages update')

    nb_elem_to_update = r_serv_db.get('update:nb_elem_to_convert')
    if not nb_elem_to_update:
        nb_elem_to_update = 1
    else:
        nb_elem_to_update = int(nb_elem_to_update)

    # _delete_all_domains_languages()

    while True:
        domain = r_serv_onion.spop('domain_update_v3.4')
        if domain is not None:
            print(domain)
            domain = str(domain)
            domain_t = get_domain_type(domain)
            domain = Domain.Domain(domain)
            for domain_history in get_domain_history(domain_t, domain):
                domain_items = get_domain_items_crawled(domain, domain_t, domain_history[1])
                for id_item in domain_items:
                    update_domain_language(domain, id_item)

            r_serv_db.incr('update:nb_elem_converted')
            update_update_stats()

        else:
            r_serv_db.set('ail:current_background_script_stat', 100)
            sys.exit(0)
