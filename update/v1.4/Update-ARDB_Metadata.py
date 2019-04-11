#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import configparser


def update_hash_item(has_type):
    #get all hash items:
    #all_base64 = r_serv_tag.smembers('infoleak:automatic-detection=\"{}\"'.format(has_type))
    all_hash_items = r_serv_tag.smembers('infoleak:automatic-detection=\"{}\":20180925'.format(has_type))
    for item_path in all_hash_items:
        item_path = '/home/aurelien/git/python3/AIL-framework/PASTES/archive/pastebin.com_pro/2018/09/25/Fu9akJaz.gz'
        if PASTES_FOLDER in item_path:
            base64_key = '{}_paste:{}'.format(has_type, item_path)
            hash_key = 'hash_paste:{}'.format(item_path)

            ## TODO: catch error
            if r_serv_metadata.exists(base64_key):
                res = r_serv_metadata.renamenx(base64_key, base64_key.replace(PASTES_FOLDER, '', 1))
                ## TODO: key merge
                if not res:
                    print('same key, double name: {}'.format(item_path))

            if r_serv_metadata.exists(hash_key):
                ## TODO: catch error
                res = r_serv_metadata.renamenx(hash_key, hash_key.replace(PASTES_FOLDER, '', 1))
                ## TODO: key merge
                if not res:
                    print('same key, double name: {}'.format(item_path))

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

    r_serv_onion = redis.StrictRedis(
        host=cfg.get("ARDB_Onion", "host"),
        port=cfg.getint("ARDB_Onion", "port"),
        db=cfg.getint("ARDB_Onion", "db"),
        decode_responses=True)

    ## Update metadata ##
    print('Updating ARDB_Metadata ...')
    index = 0
    start = time.time()

    # Update base64
    update_hash_item('base64')
    # Update binary
    update_hash_item('binary')
    # Update binary
    update_hash_item('hexadecimal')

    # Update onion metadata
    all_crawled_items = r_serv_tag.smembers('infoleak:submission=\"crawler\"')
    for item_path in all_crawled_items:
        domain = None
        if PASTES_FOLDER in item_path:
            old_item_metadata = 'paste_metadata:{}'.format(item_path)
            item_path = item_path.replace(PASTES_FOLDER, '', 1)
            new_item_metadata = 'paste_metadata:{}'.format(item_path)
            ## TODO: catch error
            res = r_serv_metadata.renamenx(old_item_metadata, new_item_metadata)
        # update domain port
        domain = r_serv_metadata.hget(new_item_metadata, 'domain')
        if domain:
            r_serv_metadata.hset(new_item_metadata, 'domain', '{}:80'.format(domain))
        super_father = r_serv_metadata.hget(new_item_metadata, 'super_father')
        if super_father:
            if PASTES_FOLDER in super_father:
                r_serv_metadata.hset(new_item_metadata, 'super_father', super_father.replace(PASTES_FOLDER, '', 1))
        father = r_serv_metadata.hget(new_item_metadata, 'father')
        if father:
            if PASTES_FOLDER in father:
                r_serv_metadata.hset(new_item_metadata, 'father', father.replace(PASTES_FOLDER, '', 1))




    ######################################################################################################################
    ######################################################################################################################
    ######################################################################################################################
    ######################################################################################################################
    ######################################################################################################################
    ######################################################################################################################
    '''

    string_keys_to_rename = ['misp_events:{}*'.format(PASTES_FOLDER), 'hive_cases:{}*'.format(PASTES_FOLDER)]
    for key_to_rename in string_keys_to_rename:

        keys_to_rename = []
        for key in r_serv_metadata.scan_iter(key_to_rename):
            new_key = key.replace(PASTES_FOLDER, '', 1)
            keys_to_rename.append( (key, new_key) )
            index = index + 1
        for key, new_key in keys_to_rename:
            r_serv_metadata.rename(key, new_key)

    keys_to_rename = None

    set_keys_to_rename = ['tag:{}*'.format(PASTES_FOLDER), 'paste_regular_external_links:{}*'.format(PASTES_FOLDER), 'paste_onion_external_links:{}*'.format(PASTES_FOLDER), 'paste_children:{}*'.format(PASTES_FOLDER)]
    for key_to_rename in set_keys_to_rename:

        keys_to_remove = []
        keys_to_rename = []
        for key in r_serv_metadata.scan_iter(key_to_rename):
            new_key = key.replace(PASTES_FOLDER, '', 1)
            # a set with this key already exist
            if r_serv_metadata.exists(new_key):
                # save data
                for new_key_value in r_serv_metadata.smembers(key):
                    r_serv_metadata.sadd(new_key, new_key_value)
                    keys_to_remove.append(key)
            else:
                keys_to_rename.append( (key, new_key) )
            index = index + 1
        for key in keys_to_remove:
            r_serv_metadata.delete(key)
        for key, new_key in keys_to_rename:
            r_serv_metadata.rename(key, new_key)

    keys_to_remove = None
    keys_to_rename = None


    zset_keys_to_rename = ['nb_seen_hash:*', 'base64_hash:*', 'binary_hash:*']
    for key_to_rename in zset_keys_to_rename:

        keys_to_remove = []
        zkeys_to_remove = []
        keys_to_add = []
        for key in r_serv_metadata.scan_iter(key_to_rename):
            temp = []
            for zset_key, value in r_serv_metadata.zscan_iter(key, '*{}*'.format(PASTES_FOLDER)):
                new_key = zset_key.replace(PASTES_FOLDER, '', 1)
                index = index +1
                temp.append((key, zset_key))
                keys_to_add.append((key, new_key, value))
            if 0 < len(temp) < r_serv_metadata.zcard(key):
                zkeys_to_remove.extend(temp)
            else:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            r_serv_metadata.delete(key)
        for key, zset_key in zkeys_to_remove:
            r_serv_metadata.zrem(key, zset_key)
        for key, new_key, value in keys_to_add:
            r_serv_metadata.zincrby(key, new_key, int(value))
    keys_to_remove = None
    zkeys_to_remove = None
    keys_to_add = None

    set_keys_to_rename = ['paste_children:*']
    for key_to_rename in set_keys_to_rename:
        keys_to_remove = []
        skeys_to_remove = []
        keys_to_add = []
        for key in r_serv_metadata.scan_iter(key_to_rename):
            temp = []
            for set_key in r_serv_metadata.sscan_iter(key, '*{}*'.format(PASTES_FOLDER)):
                new_key = set_key.replace(PASTES_FOLDER, '', 1)
                index = index +1
                temp.append((key, set_key))
                keys_to_add.append((key, new_key))
            if 0 < len(temp) < r_serv_metadata.scard(key):
                skeys_to_remove.extend(temp)
            else:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            r_serv_metadata.delete(key)
        for key, set_key in skeys_to_remove:
            r_serv_metadata.srem(key, set_key)
        for key, new_key in keys_to_add:
            r_serv_metadata.sadd(key, new_key)
    keys_to_remove = None
    skeys_to_remove = None
    keys_to_add = None

    hset_keys_to_rename = ['paste_metadata:{}*'.format(PASTES_FOLDER)]
    for key_to_rename in hset_keys_to_rename:

        keys_to_rename = []
        for key in r_serv_metadata.scan_iter(key_to_rename):
            new_key = key.replace(PASTES_FOLDER, '', 1)
            # a hset with this key already exist
            if r_serv_metadata.exists(new_key):
                pass
            else:
                keys_to_rename.append((key, new_key))
                index = index + 1
        for key, new_key in keys_to_rename:
            r_serv_metadata.rename(key, new_key)
    keys_to_rename = None

    # to verify 120/100 try with scan
    hset_keys_to_rename = ['paste_metadata:*']
    for key_to_rename in hset_keys_to_rename:
        for key in r_serv_metadata.scan_iter(key_to_rename):
            father = r_serv_metadata.hget(key, 'father')
            super_father = r_serv_metadata.hget(key, 'super_father')

            if father:
                if PASTES_FOLDER in father:
                    index = index + 1
                    r_serv_metadata.hdel(key, 'father')
                    r_serv_metadata.hset(key, 'father', father.replace(PASTES_FOLDER, '', 1))

            if super_father:
                if PASTES_FOLDER in super_father:
                    index = index + 1
                    r_serv_metadata.hdel(key, 'super_father')
                    r_serv_metadata.hset(key, 'super_father', super_father.replace(PASTES_FOLDER, '', 1))

    keys_to_rename = None
    '''


    end = time.time()

    print('Updating ARDB_Metadata Done => {} paths: {} s'.format(index, end - start))
    print()
