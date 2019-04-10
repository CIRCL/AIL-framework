#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import configparser

def tags_key_fusion(old_item_path_key, new_item_path_key):
    print('fusion:')
    print(old_item_path_key)
    print(new_item_path_key)
    for tag in r_serv_metadata.smembers(old_item_path_key):
        r_serv_metadata.sadd(new_item_path_key, tag)
        r_serv_metadata.srem(old_item_path_key, tag)

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

    r_serv_onion = redis.StrictRedis(
        host=cfg.get("ARDB_Onion", "host"),
        port=cfg.getint("ARDB_Onion", "port"),
        db=cfg.getint("ARDB_Onion", "db"),
        decode_responses=True)

    r_important_paste_2018 = redis.StrictRedis(
        host=cfg.get("ARDB_Metadata", "host"),
        port=cfg.getint("ARDB_Metadata", "port"),
        db=2018,
        decode_responses=True)

    r_important_paste_2019 = redis.StrictRedis(
        host=cfg.get("ARDB_Metadata", "host"),
        port=cfg.getint("ARDB_Metadata", "port"),
        db=2018,
        decode_responses=True)

    print('Updating ARDB_Tags ...')
    index = 0
    start = time.time()

    tags_list = r_serv_tag.smembers('list_tags')
    # create temp tags metadata
    tag_metadata = {}
    for tag in tags_list:
        tag_metadata[tag] = {}
        tag_metadata[tag]['first_seen'] = r_serv_tag.hget('tag_metadata:{}'.format(tag), 'first_seen')
        if tag_metadata[tag]['first_seen'] is None:
            tag_metadata[tag]['first_seen'] = 99999999
        else:
            tag_metadata[tag]['first_seen'] = int(tag_metadata[tag]['first_seen'])

        tag_metadata[tag]['last_seen'] = r_serv_tag.hget('tag_metadata:{}'.format(tag), 'last_seen')
        if tag_metadata[tag]['last_seen'] is None:
            tag_metadata[tag]['last_seen'] = 0
        else:
            tag_metadata[tag]['last_seen'] = int(tag_metadata[tag]['last_seen'])

    for tag in tags_list:

        all_item =  r_serv_tag.smembers(tag)
        for item_path in all_item:
            splitted_item_path = item_path.split('/')
            #print(tag)
            #print(item_path)
            item_date = int( ''.join([splitted_item_path[-4], splitted_item_path[-3], splitted_item_path[-2]]) )

            # remove absolute path
            new_path = item_path.replace(PASTES_FOLDER, '', 1)
            if new_path != item_path:
                # save in queue absolute path to remove
                r_serv_tag.sadd('maj:v1.5:absolute_path_to_rename', item_path)

            # update metadata first_seen
            if item_date < tag_metadata[tag]['first_seen']:
                tag_metadata[tag]['first_seen'] = item_date
                r_serv_tag.hset('tag_metadata:{}'.format(tag), 'first_seen', item_date)

            # update metadata last_seen
            if item_date > tag_metadata[tag]['last_seen']:
                tag_metadata[tag]['last_seen'] = item_date
                r_serv_tag.hset('tag_metadata:{}'.format(tag), 'last_seen', item_date)


            r_serv_tag.sadd('{}:{}'.format(tag, item_date), new_path)
            r_serv_tag.hincrby('daily_tags:{}'.format(item_date), tag, 1)

            # clean db
            r_serv_tag.srem(tag, item_path)
            index = index + 1

    #flush browse importante pastes db
    r_important_paste_2018.flushdb()
    r_important_paste_2019.flushdb()

    #update item metadata tags
    tag_not_updated = True
    total_to_update = r_serv_tag.scard('maj:v1.5:absolute_path_to_rename')
    nb_updated = 0
    while tag_not_updated:
        item_path = r_serv_tag.spop('maj:v1.5:absolute_path_to_rename')
        old_tag_item_key = 'tag:{}'.format(item_path)
        new_item_path = item_path.replace(PASTES_FOLDER, '', 1)
        new_tag_item_key = 'tag:{}'.format(new_item_path)
        res = r_serv_metadata.renamenx(old_tag_item_key, new_tag_item_key)
        if res == 0:
            tags_key_fusion(old_tag_item_key, new_tag_item_key)
        nb_updated += 1
        if r_serv_tag.scard('maj:v1.5:absolute_path_to_rename') == 0:
            tag_not_updated = false
        else:
            print('{}/{}    Tags updated'.format(nb_updated, total_to_update))

    end = time.time()


    print('Updating ARDB_Tags Done => {} paths: {} s'.format(index, end - start))
