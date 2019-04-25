#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import configparser

def update_tracked_terms(main_key, tracked_container_key):
    for tracked_item in r_serv_term.smembers(main_key):
        all_items = r_serv_term.smembers(tracked_container_key.format(tracked_item))
        for item_path in all_items:
            if PASTES_FOLDER in item_path:
                new_item_path = item_path.replace(PASTES_FOLDER, '', 1)
                r_serv_term.sadd(tracked_container_key.format(tracked_item), new_item_path)
                r_serv_term.srem(tracked_container_key.format(tracked_item), item_path)

def update_hash_item(has_type):
    #get all hash items:
    all_hash_items = r_serv_tag.smembers('infoleak:automatic-detection=\"{}\"'.format(has_type))
    for item_path in all_hash_items:
        if PASTES_FOLDER in item_path:
            base64_key = '{}_paste:{}'.format(has_type, item_path)
            hash_key = 'hash_paste:{}'.format(item_path)

            if r_serv_metadata.exists(base64_key):
                new_base64_key = base64_key.replace(PASTES_FOLDER, '', 1)
                res = r_serv_metadata.renamenx(base64_key, new_base64_key)
                if res == 0:
                    print('same key, double name: {}'.format(item_path))
                    # fusion
                    all_key = r_serv_metadata.smembers(base64_key)
                    for elem in all_key:
                        r_serv_metadata.sadd(new_base64_key, elem)
                        r_serv_metadata.srem(base64_key, elem)

            if r_serv_metadata.exists(hash_key):
                new_hash_key = hash_key.replace(PASTES_FOLDER, '', 1)
                res = r_serv_metadata.renamenx(hash_key, new_hash_key)
                if res == 0:
                    print('same key, double name: {}'.format(item_path))
                    # fusion
                    all_key = r_serv_metadata.smembers(hash_key)
                    for elem in all_key:
                        r_serv_metadata.sadd(new_hash_key, elem)
                        r_serv_metadata.srem(hash_key, elem)

if __name__ == '__main__':

    start_deb = time.time()

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "pastes")) + '/'

    r_serv = redis.StrictRedis(
        host=cfg.get("ARDB_DB", "host"),
        port=cfg.getint("ARDB_DB", "port"),
        db=cfg.getint("ARDB_DB", "db"),
        decode_responses=True)

    r_serv_metadata = redis.StrictRedis(
        host=cfg.get("ARDB_Metadata", "host"),
        port=cfg.getint("ARDB_Metadata", "port"),
        db=cfg.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    r_serv_tag = redis.StrictRedis(
        host=cfg.get("ARDB_Tags", "host"),
        port=cfg.getint("ARDB_Tags", "port"),
        db=cfg.getint("ARDB_Tags", "db"),
        decode_responses=True)

    r_serv_term = redis.StrictRedis(
        host=cfg.get("ARDB_TermFreq", "host"),
        port=cfg.getint("ARDB_TermFreq", "port"),
        db=cfg.getint("ARDB_TermFreq", "db"),
        decode_responses=True)

    r_serv_onion = redis.StrictRedis(
        host=cfg.get("ARDB_Onion", "host"),
        port=cfg.getint("ARDB_Onion", "port"),
        db=cfg.getint("ARDB_Onion", "db"),
        decode_responses=True)

    r_serv.set('ail:current_background_script', 'metadata')

    ## Update metadata ##
    print('Updating ARDB_Metadata ...')
    index = 0
    start = time.time()

    #update stats
    r_serv.set('ail:current_background_script_stat', 0)

    # Update base64
    update_hash_item('base64')

    #update stats
    r_serv.set('ail:current_background_script_stat', 20)
    # Update binary
    update_hash_item('binary')

    #update stats
    r_serv.set('ail:current_background_script_stat', 40)
    # Update binary
    update_hash_item('hexadecimal')

    #update stats
    r_serv.set('ail:current_background_script_stat', 60)

    total_onion = r_serv_tag.scard('infoleak:submission=\"crawler\"')
    nb_updated = 0
    last_progress = 0

    # Update onion metadata
    all_crawled_items = r_serv_tag.smembers('infoleak:submission=\"crawler\"')
    for item_path in all_crawled_items:
        domain = None
        if PASTES_FOLDER in item_path:
            old_item_metadata = 'paste_metadata:{}'.format(item_path)
            item_path = item_path.replace(PASTES_FOLDER, '', 1)
            new_item_metadata = 'paste_metadata:{}'.format(item_path)
            res = r_serv_metadata.renamenx(old_item_metadata, new_item_metadata)
            #key already exist
            if res == 0:
                r_serv_metadata.delete(old_item_metadata)

        # update domain port
        domain = r_serv_metadata.hget(new_item_metadata, 'domain')
        if domain:
            if domain[-3:] != ':80':
                r_serv_metadata.hset(new_item_metadata, 'domain', '{}:80'.format(domain))
        super_father = r_serv_metadata.hget(new_item_metadata, 'super_father')
        if super_father:
            if PASTES_FOLDER in super_father:
                r_serv_metadata.hset(new_item_metadata, 'super_father', super_father.replace(PASTES_FOLDER, '', 1))
        father = r_serv_metadata.hget(new_item_metadata, 'father')
        if father:
            if PASTES_FOLDER in father:
                r_serv_metadata.hset(new_item_metadata, 'father', father.replace(PASTES_FOLDER, '', 1))

        nb_updated += 1
        progress = int((nb_updated * 30) /total_onion)
        print('{}/{}    updated    {}%'.format(nb_updated, total_onion, progress + 60))
        # update progress stats
        if progress != last_progress:
            r_serv.set('ail:current_background_script_stat', progress + 60)
            last_progress = progress

    #update stats
    r_serv.set('ail:current_background_script_stat', 90)

    ## update tracked term/set/regex
    # update tracked term
    update_tracked_terms('TrackedSetTermSet', 'tracked_{}')

    #update stats
    r_serv.set('ail:current_background_script_stat', 93)
    # update tracked set
    update_tracked_terms('TrackedSetSet', 'set_{}')

    #update stats
    r_serv.set('ail:current_background_script_stat', 96)
    # update tracked regex
    update_tracked_terms('TrackedRegexSet', 'regex_{}')

    #update stats
    r_serv.set('ail:current_background_script_stat', 100)
    ##

    end = time.time()

    print('Updating ARDB_Metadata Done => {} paths: {} s'.format(index, end - start))
    print()

    r_serv.sadd('ail:update_v1.5', 'metadata')

    ##
    #Key, Dynamic Update
    ##
    #paste_children
    #nb_seen_hash, base64_hash, binary_hash
    #paste_onion_external_links
    #misp_events, hive_cases
    ##
