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
    for key in r_serv_metadata.scan_iter('*'):
        if not 'dup:' in key:
            if PASTES_FOLDER in key:
                new_key = key.replace(PASTES_FOLDER, '', 1)

                # a set with this key already exist
                if r_serv_metadata.exists(new_key):
                    # save data
                    for new_key_value in r_serv_metadata.smembers(key):
                        r_serv_metadata.sadd(new_key, new_key_value)
                r_serv_metadata.delete(key)
                index = index + 1

            type = r_serv_metadata.type(key)
            print(type)
            if type == 'hash':
                list_data = r_serv_metadata.hscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)
                print(key)
                while list_data[1]:
                    print(list_data[1])
                    for hash_key, value in list_data[1].items():
                        print('-----------------------------')
                        print(key)
                        print(hash_key)
                        print(value)
                        r_serv_metadata.hdel(key, hash_key)
                        new_hash = hash_key.replace(PASTES_FOLDER, '', 1)
                        new_value = value.replace(PASTES_FOLDER, '', 1)
                        index = index +1
                        r_serv_metadata.hset(key, new_hash, new_value)

                    list_data = r_serv_metadata.hscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)
            elif type == 'zset':
                list_data = r_serv_metadata.zscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)
                while list_data[1]:
                    for elem in list_data[1]:
                        zset_key = elem[0]
                        value =  int(elem[1])
                        r_serv_metadata.zrem(key, zset_key)
                        new_key = zset_key.replace(PASTES_FOLDER, '', 1)
                        index = index +1
                        r_serv_metadata.zincrby(key, new_key, value)

                    list_data = r_serv_metadata.zscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)

            elif type == 'set':
                list_data = r_serv_metadata.sscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)
                while list_data[1]:
                    for set_value in list_data[1]:
                        r_serv_metadata.srem(key, set_value)
                        r_serv_metadata.sadd(key, set_value.replace(PASTES_FOLDER, '', 1))
                        index = index + 1

                    list_data = r_serv_metadata.sscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)

    end = time.time()


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
    for key in r_serv_onion.scan_iter('*'):

        if key != 'mess_onion':
            list_data = r_serv_onion.hscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)
            while list_data[1]:
                for hash_key, value in list_data[1].items():
                    r_serv_onion.hdel(key, hash_key)
                    new_hash = hash_key.replace(PASTES_FOLDER, '', 1)
                    new_value = value.replace(PASTES_FOLDER, '', 1)
                    index = index +1
                    r_serv_onion.hset(key, new_hash, new_value)

                list_data = r_serv_onion.hscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)

            list_data = r_serv_onion.sscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)
            while list_data[1]:
                for set_value in list_data[1]:
                    r_serv_onion.srem(key, set_value)
                    r_serv_onion.sadd(key, set_value.replace(PASTES_FOLDER, '', 1))
                    index = index + 1

                list_data = r_serv_onion.sscan(key, 0, '*{}*'.format(PASTES_FOLDER), 1000)

    end = time.time()
    print('Updating ARDB_Onion Done => {} paths: {} s'.format(index, end - start))
    print()
    print('Done in {} s'.format(end - start_deb))
