#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import datetime

from hashlib import sha256

from pyfaup.faup import Faup

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Date

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import Tag

def sanitize_domain(domain):
    faup.decode(domain)
    domain_sanitized = faup.get()
    domain_sanitized = domain_sanitized['domain']
    try:
        domain_sanitized = domain_sanitized.decode()
    except:
        pass
    return domain_sanitized.lower()

def delete_domain_tag_daterange():
    all_domains_tags = Tag.get_all_obj_tags('domain')
    nb_updated = 0
    nb_to_update = len(all_domains_tags)
    if nb_to_update == 0:
        nb_to_update = 1
    refresh_time = time.time()
    l_dates = Date.substract_date('20191008', Date.get_today_date_str())
    for tag in all_domains_tags:
        for date_day in l_dates:
            r_serv_tags.delete('domain:{}:{}'.format(tag, date_day))
        nb_updated += 1
        refresh_time = update_progress(refresh_time, nb_updated, nb_to_update)
    r_serv_db.delete('ail:update_v2.7:deletetagrange')

def update_domain_tags(domain):
    domain_sanitized = sanitize_domain(domain)
    if domain != domain_sanitized:
        r_serv_onion.sadd('incorrect_domain', domain)
        domain = domain_sanitized

    domain_tags = Tag.get_obj_tag(domain)
    for tag in domain_tags:
        # delete incorrect tags
        if tag == 'infoleak:submission="crawler"' or tag == 'infoleak:submission="manual"':
            r_serv_metadata.srem('tag:{}'.format(domain), tag)
        else:
            Tag.add_global_tag(tag, object_type='domain')
            r_serv_tags.sadd('{}:{}'.format('domain', tag), domain)

def update_progress(refresh_time, nb_updated, nb_elem_to_update):
    if time.time() - refresh_time > 10:
        progress = int((nb_updated * 100) / nb_elem_to_update)
        print('{}/{}    updated    {}%'.format(nb_updated, nb_elem_to_update, progress))
        r_serv_db.set('ail:current_background_script_stat', progress)
        refresh_time = time.time()

    return refresh_time

def update_db():
    nb_updated = 0
    nb_to_update = r_serv_onion.scard('domain_update_v2.7')
    refresh_time = time.time()
    r_serv_db.set('ail:current_background_script_stat', 0)
    r_serv_db.set('ail:current_background_script', 'domain tags update')
    domain = r_serv_onion.spop('domain_update_v2.7')
    while domain is not None:
        update_domain_tags(domain)
        nb_updated += 1
        refresh_time = update_progress(refresh_time, nb_updated, nb_to_update)
        domain = r_serv_onion.spop('domain_update_v2.7')
    if r_serv_db.exists('ail:update_v2.7:deletetagrange'):
        r_serv_db.set('ail:current_background_script_stat', 0)
        r_serv_db.set('ail:current_background_script', 'tags: remove deprecated keys')
        delete_domain_tag_daterange()

    # sort all crawled domain
    r_serv_onion.sort('full_onion_up', alpha=True)
    r_serv_onion.sort('full_regular_up', alpha=True)

if __name__ == '__main__':

    start_deb = time.time()
    faup = Faup()

    config_loader = ConfigLoader.ConfigLoader()

    r_serv_db = config_loader.get_redis_conn("ARDB_DB")
    r_serv_tags = config_loader.get_redis_conn("ARDB_Tags")
    r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
    r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
    config_loader = None

    update_version = 'v2.7'

    r_serv_db.set('ail:update_in_progress', update_version)
    r_serv_db.set('ail:current_background_update', update_version)

    r_serv_db.set('ail:current_background_script_stat', 0)
    r_serv_db.set('ail:current_background_script', 'tags update')

    update_db()

    r_serv_db.set('ail:current_background_script_stat', 100)


    end = time.time()
    print('ALL domains tags updated in {} s'.format(end - start_deb))
