#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import time
import redis
import datetime

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import Domain

def update_update_stats():
    nb_updated = int(r_serv_db.get('update:nb_elem_converted'))
    progress = int((nb_updated * 100) / nb_elem_to_update)
    print('{}/{}    updated    {}%'.format(nb_updated, nb_elem_to_update, progress))
    r_serv_db.set('ail:current_background_script_stat', progress)

def update_domain_language(domain_obj, item_id):
    domain_name = domain_obj.get_domain_name()
    Domain.add_domain_languages_by_item_id(domain_name, item_id)

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()
    r_serv_db = config_loader.get_redis_conn("ARDB_DB")
    r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
    config_loader = None

    r_serv.set('ail:current_background_script', 'domain languages update')

    nb_elem_to_update = r_serv_db.get('update:nb_elem_to_convert')
    if not nb_elem_to_update:
        nb_elem_to_update = 1
    else:
        nb_elem_to_update = int(nb_elem_to_update)

    #Domain._delete_all_domains_languages()

    while True:
        domain = r_serv_onion.spop('domain_update_v3.4')
        if domain is not None:
            print(domain)
            domain = Domain.Domain(domain)
            for domain_history in domain.get_domain_history():
                domain_item = domain.get_domain_items_crawled(epoch=domain_history[1]) # item_tag
                if "items" in domain_item:
                    for item_dict in domain_item['items']:
                        update_domain_language(domain, item_dict['id'])

            r_serv_db.incr('update:nb_elem_converted')
            update_update_stats()

        else:
            r_serv_db.set('ail:current_background_script_stat', 100)
            sys.exit(0)
