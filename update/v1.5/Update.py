#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import configparser

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

    set_keys_to_rename = ['tag:{}*'.format(PASTES_FOLDER), 'hash_paste:{}*'.format(PASTES_FOLDER), 'base64_paste:{}*'.format(PASTES_FOLDER), 'binary_paste:{}*'.format(PASTES_FOLDER), 'hexadecimal_paste:{}*'.format(PASTES_FOLDER), 'paste_regular_external_links:{}*'.format(PASTES_FOLDER), 'paste_onion_external_links:{}*'.format(PASTES_FOLDER), 'paste_children:{}*'.format(PASTES_FOLDER)]
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
                #print(key)
                #print(zset_key)
                #print(value)
                new_key = zset_key.replace(PASTES_FOLDER, '', 1)
                index = index +1
                temp.append((key, zset_key))
                keys_to_add.append((key, new_key, value))
            if 0 < len(temp) < r_serv_metadata.zcard(key):
                #print(key)
                #print(len(temp))
                #print(temp)
                #print(r_serv_metadata.zcard(key))
                #print('---------------')
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
                print(key)
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


    end = time.time()

    ''''
    for key in r_serv_metadata.scan_iter('*{}*'.format(PASTES_FOLDER)):
        if not 'dup:' in key:
            if not 'paste_i2p_external_links:' in key:
                if not 'base64:' in key:
                    print(key)
    '''

    print('Updating ARDB_Metadata Done => {} paths: {} s'.format(index, end - start))

    print()
    print('Updating ARDB_Tags ...')
    index = 0
    start = time.time()

    tags_list = r_serv_tag.smembers('list_tags')
    for tag in tags_list:
        res = False

        list_pastes = r_serv_tag.sscan(tag, 0, '*{}*'.format(PASTES_FOLDER), 1000)
        while list_pastes[1]:
            for paste in list_pastes[1]:
                r_serv_tag.srem(tag, paste)
                r_serv_tag.sadd(tag, paste.replace(PASTES_FOLDER, '', 1))
                index = index + 1

            list_pastes = r_serv_tag.sscan(tag, 0, '*{}*'.format(PASTES_FOLDER), 1000)

    end = time.time()
    print('Updating ARDB_Tags Done => {} paths: {} s'.format(index, end - start))

    print()
    print('Updating ARDB_Onion ...')
    index = 0
    start = time.time()

    hset_keys_to_rename = ['onion_metadata:*']
    for key_to_rename in hset_keys_to_rename:
        for key in r_serv_onion.scan_iter(key_to_rename):
            list_data = r_serv_onion.hscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)
            while list_data[1]:
                for hash_key, value in list_data[1].items():
                    r_serv_onion.hdel(key, hash_key)
                    new_hash = hash_key.replace(PASTES_FOLDER, '', 1)
                    new_value = value.replace(PASTES_FOLDER, '', 1)
                    index = index +1
                    r_serv_onion.hset(key, new_hash, new_value)

                list_data = r_serv_onion.hscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)

    for elem in r_serv_onion.smembers('onion_crawler_queue'):
        if PASTES_FOLDER in elem:
            r_serv_onion.srem('onion_crawler_queue', elem)
            r_serv_onion.sadd('onion_crawler_queue', elem.replace(PASTES_FOLDER, '', 1))
            index = index +1


    end = time.time()
    print('Updating ARDB_Onion Done => {} paths: {} s'.format(index, end - start))
    print()
    print('Done in {} s'.format(end - start_deb))
