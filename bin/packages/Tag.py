#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import redis

import Flask_config
import Date
import Item

from pytaxonomies import Taxonomies
from pymispgalaxies import Galaxies, Clusters

r_serv_tags = Flask_config.r_serv_tags
r_serv_metadata = Flask_config.r_serv_metadata

def get_taxonomie_from_tag(tag):
    return tag.split(':')[0]

def get_galaxy_from_tag(tag):
    galaxy = tag.split(':')[1]
    galaxy = galaxy.split('=')[0]
    return galaxy

def get_active_taxonomies():
    return r_serv_tags.smembers('active_taxonomies')

def get_active_galaxies():
    return r_serv_tags.smembers('active_galaxies')

def is_taxonomie_tag_enabled(taxonomie, tag):
    if tag in r_serv_tags.smembers('active_tag_' + taxonomie):
        return True
    else:
        return False

def is_galaxy_tag_enabled(galaxy, tag):
    if tag in r_serv_tags.smembers('active_tag_galaxies_' + galaxy):
        return True
    else:
        return False

# Check if tags are enabled in AIL
def is_valid_tags_taxonomies_galaxy(list_tags, list_tags_galaxy):
    print(list_tags)
    print(list_tags_galaxy)
    if list_tags:
        active_taxonomies = get_active_taxonomies()

        for tag in list_tags:
            taxonomie = get_taxonomie_from_tag(tag)
            if taxonomie not in active_taxonomies:
                return False
            if not is_taxonomie_tag_enabled(taxonomie, tag):
                return False

    if list_tags_galaxy:
        active_galaxies = get_active_galaxies()

        for tag in list_tags_galaxy:
            galaxy = get_galaxy_from_tag(tag)
            if galaxy not in active_galaxies:
                return False
            if not is_galaxy_tag_enabled(galaxy, tag):
                return False
    return True

def get_item_tags(item_id):
    tags = r_serv_metadata.smembers('tag:'+item_id)
    if tags:
        return list(tags)
    else:
        return '[]'

# TEMPLATE + API QUERY
def add_items_tag(tags=[], galaxy_tags=[], item_id=None):
    res_dict = {}
    if item_id == None:
        return ({'status': 'error', 'reason': 'Item id not found'}, 404)
    if not tags and not galaxy_tags:
        return ({'status': 'error', 'reason': 'Tags or Galaxy not specified'}, 400)

    res_dict['tags'] = []
    for tag in tags:
        taxonomie = get_taxonomie_from_tag(tag)
        if is_taxonomie_tag_enabled(taxonomie, tag):
            add_item_tag(tag, item_id)
            res_dict['tags'].append(tag)
        else:
            return ({'status': 'error', 'reason': 'Tags or Galaxy not enabled'}, 400)

    for tag in galaxy_tags:
        galaxy = get_galaxy_from_tag(tag)
        if is_galaxy_tag_enabled(galaxy, tag):
            add_item_tag(tag, item_id)
            res_dict['tags'].append(tag)
        else:
            return ({'status': 'error', 'reason': 'Tags or Galaxy not enabled'}, 400)

    res_dict['id'] = item_id
    return (res_dict, 200)


def add_item_tag(tag, item_path):

    item_date = int(Item.get_item_date(item_path))

    #add tag
    r_serv_metadata.sadd('tag:{}'.format(item_path), tag)
    r_serv_tags.sadd('{}:{}'.format(tag, item_date), item_path)

    r_serv_tags.hincrby('daily_tags:{}'.format(item_date), tag, 1)

    tag_first_seen = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')
    if tag_first_seen is None:
        tag_first_seen = 99999999
    else:
        tag_first_seen = int(tag_first_seen)
    tag_last_seen = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')
    if tag_last_seen is None:
        tag_last_seen = 0
    else:
        tag_last_seen = int(tag_last_seen)

    #add new tag in list of all used tags
    r_serv_tags.sadd('list_tags', tag)

    # update fisrt_seen/last_seen
    if item_date < tag_first_seen:
        r_serv_tags.hset('tag_metadata:{}'.format(tag), 'first_seen', item_date)

    # update metadata last_seen
    if item_date > tag_last_seen:
        r_serv_tags.hset('tag_metadata:{}'.format(tag), 'last_seen', item_date)

# API QUERY
def remove_item_tags(tags=[], item_id=None):
    if item_id == None:
        return ({'status': 'error', 'reason': 'Item id not found'}, 404)
    if not tags:
        return ({'status': 'error', 'reason': 'No Tag(s) specified'}, 400)

    dict_res = {}
    dict_res['tags'] = []
    for tag in tags:
        res = remove_item_tag(tag, item_id)
        if res[1] != 200:
            return res
        else:
            dict_res[tags].append(tag)
    dict_res['id'] = item_id
    return (dict_res, 200)

# TEMPLATE + API QUERY
def remove_item_tag(tag, item_id):
    item_date = int(Item.get_item_date(item_id))

    #remove tag
    r_serv_metadata.srem('tag:{}'.format(item_id), tag)
    res = r_serv_tags.srem('{}:{}'.format(tag, item_date), item_id)

    if res ==1:
        # no tag for this day
        if int(r_serv_tags.hget('daily_tags:{}'.format(item_date), tag)) == 1:
            r_serv_tags.hdel('daily_tags:{}'.format(item_date), tag)
        else:
            r_serv_tags.hincrby('daily_tags:{}'.format(item_date), tag, -1)

        tag_first_seen = int(r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen'))
        tag_last_seen = int(r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen'))
        # update fisrt_seen/last_seen
        if item_date == tag_first_seen:
            update_tag_first_seen(tag, tag_first_seen, tag_last_seen)
        if item_date == tag_last_seen:
            update_tag_last_seen(tag, tag_first_seen, tag_last_seen)
        return ({'status': 'success'}, 200)
    else:
        return ({'status': 'error', 'reason': 'Item id or tag not found'}, 400)

def update_tag_first_seen(tag, tag_first_seen, tag_last_seen):
    if tag_first_seen == tag_last_seen:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_first_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'first_seen', tag_first_seen)
        # no tag in db
        else:
            r_serv_tags.srem('list_tags', tag)
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'first_seen')
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'last_seen')
    else:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_first_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'first_seen', tag_first_seen)
        else:
            tag_first_seen = Date.date_add_day(tag_first_seen)
            update_tag_first_seen(tag, tag_first_seen, tag_last_seen)

def update_tag_last_seen(tag, tag_first_seen, tag_last_seen):
    if tag_first_seen == tag_last_seen:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_last_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'last_seen', tag_last_seen)
        # no tag in db
        else:
            r_serv_tags.srem('list_tags', tag)
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'first_seen')
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'last_seen')
    else:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_last_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'last_seen', tag_last_seen)
        else:
            tag_last_seen = Date.date_substract_day(tag_last_seen)
            update_tag_last_seen(tag, tag_first_seen, tag_last_seen)
