#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
from lib import ConfigLoader

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()

    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'

    r_serv = config_loader.get_redis_conn("ARDB_DB")
    r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
    r_serv_tag = config_loader.get_redis_conn("ARDB_Tags")
    r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
    r_important_paste_2018 = redis.StrictRedis(
        host=config_loader.get_config_str("ARDB_Metadata", "host"),
        port=config_loader.get_config_int("ARDB_Metadata", "port"),
        db=2018,
        decode_responses=True)

    r_important_paste_2019 = redis.StrictRedis(
        host=config_loader.get_config_str("ARDB_Metadata", "host"),
        port=config_loader.get_config_int("ARDB_Metadata", "port"),
        db=2019,
        decode_responses=True)

    config_loader = None

    r_serv.set('ail:current_background_script', 'tags')
    r_serv.set('ail:current_background_script_stat', 0)

    if r_serv.sismember('ail:update_v1.5', 'onions') and r_serv.sismember('ail:update_v1.5', 'metadata'):

        print('Updating ARDB_Tags ...')
        index = 0
        nb_tags_to_update = 0
        nb_updated = 0
        last_progress = 0
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
            nb_tags_to_update += r_serv_tag.scard(tag)

        if nb_tags_to_update == 0:
            nb_tags_to_update = 1

        for tag in tags_list:

            all_item =  r_serv_tag.smembers(tag)
            for item_path in all_item:
                splitted_item_path = item_path.split('/')
                #print(tag)
                #print(item_path)
                try:
                    item_date = int( ''.join([splitted_item_path[-4], splitted_item_path[-3], splitted_item_path[-2]]) )
                except IndexError:
                    r_serv_tag.srem(tag, item_path)
                    continue

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
                    last_seen_db = r_serv_tag.hget('tag_metadata:{}'.format(tag), 'last_seen')
                    if last_seen_db:
                        if item_date > int(last_seen_db):
                            r_serv_tag.hset('tag_metadata:{}'.format(tag), 'last_seen', item_date)
                        else:
                            tag_metadata[tag]['last_seen'] = last_seen_db

                r_serv_tag.sadd('{}:{}'.format(tag, item_date), new_path)
                r_serv_tag.hincrby('daily_tags:{}'.format(item_date), tag, 1)

                # clean db
                r_serv_tag.srem(tag, item_path)
                index = index + 1

            nb_updated += 1
            progress = int((nb_updated * 100) /nb_tags_to_update)
            print('{}/{}    updated    {}%'.format(nb_updated, nb_tags_to_update, progress))
            # update progress stats
            if progress != last_progress:
                r_serv.set('ail:current_background_script_stat', progress)
                last_progress = progress

        #flush browse importante pastes db
        try:
            r_important_paste_2018.flushdb()
        except Exception:
            pass
            
        try:
            r_important_paste_2019.flushdb()
        except Exception:
            pass

        end = time.time()

        print('Updating ARDB_Tags Done => {} paths: {} s'.format(index, end - start))

        r_serv.sadd('ail:update_v1.5', 'tags')
