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

    if r_serv.sismember('ail:update_v1.5', 'tags'):

        r_serv.set('ail:current_background_script', 'tags_background')
        r_serv.set('ail:current_background_script_stat', 0)

        print('Updating ARDB_Tags ...')
        start = time.time()

        #update item metadata tags
        tag_not_updated = True
        total_to_update = r_serv_tag.scard('maj:v1.5:absolute_path_to_rename')
        nb_updated = 0
        last_progress = 0
        if total_to_update > 0:
            while tag_not_updated:
                item_path = r_serv_tag.srandmember('maj:v1.5:absolute_path_to_rename')
                old_tag_item_key = 'tag:{}'.format(item_path)
                new_item_path = item_path.replace(PASTES_FOLDER, '', 1)
                new_tag_item_key = 'tag:{}'.format(new_item_path)
                res = r_serv_metadata.renamenx(old_tag_item_key, new_tag_item_key)
                if res == 0:
                    tags_key_fusion(old_tag_item_key, new_tag_item_key)
                nb_updated += 1
                r_serv_tag.srem('maj:v1.5:absolute_path_to_rename', item_path)
                if r_serv_tag.scard('maj:v1.5:absolute_path_to_rename') == 0:
                    tag_not_updated = False
                else:
                    progress = int((nb_updated * 100) /total_to_update)
                    print('{}/{}    Tags updated    {}%'.format(nb_updated, total_to_update, progress))
                    # update progress stats
                    if progress != last_progress:
                        r_serv.set('ail:current_background_script_stat', progress)
                        last_progress = progress

        end = time.time()


        print('Updating ARDB_Tags Done: {} s'.format(end - start))

        r_serv.sadd('ail:update_v1.5', 'tags_background')
