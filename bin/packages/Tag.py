#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

import Date
import Item

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import Domain

from pytaxonomies import Taxonomies
from pymispgalaxies import Galaxies, Clusters

config_loader = ConfigLoader.ConfigLoader()
r_serv_tags = config_loader.get_redis_conn("ARDB_Tags")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

def build_unsafe_tags():
    unsafe_tags = set()
    ## CE content
    unsafe_tags.add('dark-web:topic="pornography-child-exploitation"')
    # add copine-scale tags
    taxonomies = Taxonomies()
    copine_scale = taxonomies.get('copine-scale')
    if copine_scale:
        for tag in copine_scale.machinetags():
            unsafe_tags.add(tag)
    return unsafe_tags

# set of unsafe tags
unsafe_tags = build_unsafe_tags()

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

def enable_taxonomy(taxonomie, enable_tags=True):
    '''
    Enable a taxonomy. (UI)

    :param taxonomie: MISP taxonomy
    :type taxonomie: str
    :param enable_tags: crawled domain
    :type enable_tags: boolean
    '''
    taxonomies = Taxonomies()
    if enable_tags:
        taxonomie_info = taxonomies.get(taxonomie)
        if taxonomie_info:
            # activate taxonomie
            r_serv_tags.sadd('active_taxonomies', taxonomie)
            # activate taxonomie tags
            for tag in taxonomie_info.machinetags():
                r_serv_tags.sadd('active_tag_{}'.format(taxonomie), tag)
        else:
            print('Error: {}, please update pytaxonomies'.format(taxonomie))

# Check if tags are enabled in AIL
def is_valid_tags_taxonomies_galaxy(list_tags, list_tags_galaxy):
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

def get_tag_metadata(tag):
    first_seen = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'first_seen')
    last_seen = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')
    return {'tag': tag, 'first_seen': first_seen, 'last_seen': last_seen}

def is_tags_safe(ltags):
    '''
    Check if a list of tags contain an unsafe tag (CE, ...)

    :param ltags: list of tags
    :type ltags: list
    :return: is a tag in the unsafe set
    :rtype: boolean
    '''
    return unsafe_tags.isdisjoint(ltags)

def is_tag_in_all_tag(tag):
    if r_serv_tags.sismember('list_tags', tag):
        return True
    else:
        return False

def get_all_tags():
    return list(r_serv_tags.smembers('list_tags'))

'''
Retun all the tags of a given item.
:param item_id: (Paste or domain)
'''
def get_item_tags(item_id):
    tags = r_serv_metadata.smembers('tag:{}'.format(item_id))
    if tags:
        return list(tags)
    else:
        return []

def get_min_tag(tag):
    tag = tag.split('=')
    if len(tag) > 1:
        if tag[1] != '':
            tag = tag[1][1:-1]
        # no value
        else:
            tag = tag[0][1:-1]
    # custom tags
    else:
        tag = tag[0]
    return tag

def get_item_tags_minimal(item_id):
    return [ {"tag": tag, "min_tag": get_min_tag(tag)} for tag in get_item_tags(item_id) ]

# TEMPLATE + API QUERY
def add_items_tag(tags=[], galaxy_tags=[], item_id=None): ## TODO: remove me
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


# TEMPLATE + API QUERY
def add_items_tags(tags=[], galaxy_tags=[], item_id=None, item_type="paste"):
    res_dict = {}
    if item_id == None:
        return ({'status': 'error', 'reason': 'Item id not found'}, 404)
    if not tags and not galaxy_tags:
        return ({'status': 'error', 'reason': 'Tags or Galaxy not specified'}, 400)
    if item_type not in ('paste', 'domain'):
        return ({'status': 'error', 'reason': 'Incorrect item_type'}, 400)

    res_dict['tags'] = []
    for tag in tags:
        if tag:
            taxonomie = get_taxonomie_from_tag(tag)
            if is_taxonomie_tag_enabled(taxonomie, tag):
                add_item_tag(tag, item_id, item_type=item_type)
                res_dict['tags'].append(tag)
            else:
                return ({'status': 'error', 'reason': 'Tags or Galaxy not enabled'}, 400)

    for tag in galaxy_tags:
        if tag:
            galaxy = get_galaxy_from_tag(tag)
            if is_galaxy_tag_enabled(galaxy, tag):
                add_item_tag(tag, item_id, item_type=item_type)
                res_dict['tags'].append(tag)
            else:
                return ({'status': 'error', 'reason': 'Tags or Galaxy not enabled'}, 400)

    res_dict['id'] = item_id
    res_dict['type'] = item_type
    return (res_dict, 200)

def add_domain_tag(tag, domain, item_date):
    r_serv_metadata.sadd('tag:{}'.format(domain), tag)
    r_serv_tags.sadd('domain:{}:{}'.format(tag, item_date), domain)

def add_item_tag(tag, item_path, item_type="paste", tag_date=None):

    if item_type=="paste":
        item_date = int(Item.get_item_date(item_path))

        #add tag
        r_serv_metadata.sadd('tag:{}'.format(item_path), tag)
        r_serv_tags.sadd('{}:{}'.format(tag, item_date), item_path)

        if Item.is_crawled(item_path):
            domain = Item.get_item_domain(item_path)
            r_serv_metadata.sadd('tag:{}'.format(domain), tag)
            r_serv_tags.sadd('domain:{}:{}'.format(tag, item_date), domain)
    # domain item
    else:
        item_date = int(Domain.get_domain_last_check(item_path, r_format="int"))
        add_domain_tag(tag, item_path, item_date)

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
            dict_res['tags'].append(tag)
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


# used by modal
def get_modal_add_tags(item_id, tag_type='paste'):
    '''
    Modal: add tags to domain or Paste
    '''
    return {"active_taxonomies": get_active_taxonomies(), "active_galaxies": get_active_galaxies(),
            "item_id": item_id, "type": tag_type}
