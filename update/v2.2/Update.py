#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import time
import redis
import datetime
import configparser

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item
import Term


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


if __name__ == '__main__':

    start_deb = time.time()

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg.sample')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    r_serv_term_stats = redis.StrictRedis(
        host=cfg.get("ARDB_Trending", "host"),
        port=cfg.getint("ARDB_Trending", "port"),
        db=cfg.getint("ARDB_Trending", "db"),
        decode_responses=True)

    r_serv_termfreq = redis.StrictRedis(
        host=cfg.get("ARDB_TermFreq", "host"),
        port=cfg.getint("ARDB_TermFreq", "port"),
        db=cfg.getint("ARDB_TermFreq", "db"),
        decode_responses=True)

    r_serv_term_stats.flushdb()

    #convert all regex:
    all_regex = r_serv_termfreq.smembers('TrackedRegexSet')
    for regex in all_regex:
        tags = list( r_serv_termfreq.smembers('TrackedNotificationTags_{}'.format(regex)) )
        mails = list( r_serv_termfreq.smembers('TrackedNotificationEmails_{}'.format(regex)) )

        new_term = regex[1:-1]
        res = Term.parse_json_term_to_add({"term": new_term, "type": 'regex', "tags": tags, "mails": mails, "level": 1}, 'admin@admin.test')
        if res[1] == 200:
            term_uuid = res[0]['uuid']
            list_items = r_serv_termfreq.smembers('regex_{}'.format(regex))
            for paste_item in list_items:
                item_id = Item.get_item_id(paste_item)
                item_date = Item.get_item_date(item_id)
                Term.add_tracked_item(term_uuid, item_id, item_date)

        # Invalid Tracker => remove it
        else:
            print('Invalid Regex Removed: {}'.format(regex))
        print(res[0])
        # allow reprocess
        r_serv_termfreq.srem('TrackedRegexSet', regex)

    all_tokens = r_serv_termfreq.smembers('TrackedSetTermSet')
    for token in all_tokens:
        tags = list( r_serv_termfreq.smembers('TrackedNotificationTags_{}'.format(token)) )
        mails = list( r_serv_termfreq.smembers('TrackedNotificationEmails_{}'.format(token)) )

        res = Term.parse_json_term_to_add({"term": token, "type": 'word', "tags": tags, "mails": mails, "level": 1}, 'admin@admin.test')
        if res[1] == 200:
            term_uuid = res[0]['uuid']
            list_items = r_serv_termfreq.smembers('tracked_{}'.format(token))
            for paste_item in list_items:
                item_id = Item.get_item_id(paste_item)
                item_date = Item.get_item_date(item_id)
                Term.add_tracked_item(term_uuid, item_id, item_date)
        # Invalid Tracker => remove it
        else:
            print('Invalid Token Removed: {}'.format(token))
        print(res[0])
        # allow reprocess
        r_serv_termfreq.srem('TrackedSetTermSet', token)

    all_set = r_serv_termfreq.smembers('TrackedSetSet')
    for curr_set in all_set:
        tags = list( r_serv_termfreq.smembers('TrackedNotificationTags_{}'.format(curr_set)) )
        mails = list( r_serv_termfreq.smembers('TrackedNotificationEmails_{}'.format(curr_set)) )

        to_remove = ',{}'.format(curr_set.split(',')[-1])
        new_set = rreplace(curr_set, to_remove, '', 1)
        new_set = new_set[2:]
        new_set = new_set.replace(',', '')

        res = Term.parse_json_term_to_add({"term": new_set, "type": 'set', "nb_words": 1, "tags": tags, "mails": mails, "level": 1}, 'admin@admin.test')
        if res[1] == 200:
            term_uuid = res[0]['uuid']
            list_items = r_serv_termfreq.smembers('tracked_{}'.format(curr_set))
            for paste_item in list_items:
                item_id = Item.get_item_id(paste_item)
                item_date = Item.get_item_date(item_id)
                Term.add_tracked_item(term_uuid, item_id, item_date)
        # Invalid Tracker => remove it
        else:
            print('Invalid Set Removed: {}'.format(curr_set))
        print(res[0])
        # allow reprocess
        r_serv_termfreq.srem('TrackedSetSet', curr_set)

    r_serv_termfreq.flushdb()

    #Set current ail version
    r_serv.set('ail:version', 'v2.2')

    #Set current ail version
    r_serv.hset('ail:update_date', 'v2.2', datetime.datetime.now().strftime("%Y%m%d"))
