#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import datetime
import configparser

def substract_date(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from # timedelta
    l_date = []
    for i in range(delta.days + 1):
        date = date_from + datetime.timedelta(i)
        l_date.append( date.strftime('%Y%m%d') )
    return l_date

def get_date_epoch(date):
    return int(datetime.datetime(int(date[0:4]), int(date[4:6]), int(date[6:8])).timestamp())

def get_domain_root_from_paste_childrens(item_father, domain):
    item_children = r_serv_metadata.smembers('paste_children:{}'.format(item_father))
    domain_root = ''
    for item_path in item_children:
        # remove absolute_path
        if PASTES_FOLDER in item_path:
            r_serv_metadata.srem('paste_children:{}'.format(item_father), item_path)
            item_path = item_path.replace(PASTES_FOLDER, '', 1)
            r_serv_metadata.sadd('paste_children:{}'.format(item_father), item_path)
        if domain in item_path:
            domain_root = item_path
    return domain_root


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

    r_serv_onion = redis.StrictRedis(
        host=cfg.get("ARDB_Onion", "host"),
        port=cfg.getint("ARDB_Onion", "port"),
        db=cfg.getint("ARDB_Onion", "db"),
        decode_responses=True)

    r_serv.set('ail:current_background_script', 'onions')
    r_serv.set('ail:current_background_script_stat', 0)

    ## Update Onion ##
    print('Updating ARDB_Onion ...')
    index = 0
    start = time.time()

    # clean down domain from db
    date_from = '20180929'
    date_today = datetime.date.today().strftime("%Y%m%d")
    for date in substract_date(date_from, date_today):

        onion_down = r_serv_onion.smembers('onion_down:{}'.format(date))
        #print(onion_down)
        for onion_domain in onion_down:
            if not r_serv_onion.sismember('full_onion_up', onion_domain):
                # delete history
                all_onion_history = r_serv_onion.lrange('onion_history:{}'.format(onion_domain), 0 ,-1)
                if all_onion_history:
                    for date_history in all_onion_history:
                        #print('onion_history:{}:{}'.format(onion_domain, date_history))
                        r_serv_onion.delete('onion_history:{}:{}'.format(onion_domain, date_history))
                    r_serv_onion.delete('onion_history:{}'.format(onion_domain))

    #stats
    total_domain = r_serv_onion.scard('full_onion_up')
    nb_updated = 0
    last_progress = 0

    # clean up domain
    all_domain_up = r_serv_onion.smembers('full_onion_up')
    for onion_domain in all_domain_up:
        # delete history
        all_onion_history = r_serv_onion.lrange('onion_history:{}'.format(onion_domain), 0 ,-1)
        if all_onion_history:
            for date_history in all_onion_history:
                print('--------')
                print('onion_history:{}:{}'.format(onion_domain, date_history))
                item_father = r_serv_onion.lrange('onion_history:{}:{}'.format(onion_domain, date_history), 0, 0)
                print('item_father: {}'.format(item_father))
                try:
                    item_father = item_father[0]
                except IndexError:
                    r_serv_onion.delete('onion_history:{}:{}'.format(onion_domain, date_history))
                    continue
                #print(item_father)
                # delete old history
                r_serv_onion.delete('onion_history:{}:{}'.format(onion_domain, date_history))
                # create new history
                root_key = get_domain_root_from_paste_childrens(item_father, onion_domain)
                if root_key:
                    r_serv_onion.zadd('crawler_history_onion:{}:80'.format(onion_domain), get_date_epoch(date_history), root_key)
                    print('crawler_history_onion:{}:80   {}   {}'.format(onion_domain, get_date_epoch(date_history), root_key))
                    #update service metadata: paste_parent
                    r_serv_onion.hset('onion_metadata:{}'.format(onion_domain), 'paste_parent', root_key)

            r_serv_onion.delete('onion_history:{}'.format(onion_domain))

        r_serv_onion.hset('onion_metadata:{}'.format(onion_domain), 'ports', '80')
        r_serv_onion.hdel('onion_metadata:{}'.format(onion_domain), 'last_seen')

        nb_updated += 1
        progress = int((nb_updated * 100) /total_domain)
        print('{}/{}    updated    {}%'.format(nb_updated, total_domain, progress))
        # update progress stats
        if progress != last_progress:
            r_serv.set('ail:current_background_script_stat', progress)
            last_progress = progress


    end = time.time()
    print('Updating ARDB_Onion Done => {} paths: {} s'.format(index, end - start))
    print()
    print('Done in {} s'.format(end - start_deb))

    r_serv.sadd('ail:update_v1.5', 'onions')
