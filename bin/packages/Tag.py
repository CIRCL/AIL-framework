#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis
import datetime

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Date
import Item

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import Correlate_object

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

def is_tags_safe(ltags):
    '''
    Check if a list of tags contain an unsafe tag (CE, ...)

    :param ltags: list of tags
    :type ltags: list
    :return: is a tag in the unsafe set
    :rtype: boolean
    '''
    return unsafe_tags.isdisjoint(ltags)

#### Taxonomies - Galaxies ####

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

def get_all_taxonomies_tags(): # # TODO: add + REMOVE + Update
    return r_serv_tags.smembers('active_taxonomies_tags')

def get_all_galaxies_tags(): # # TODO: add + REMOVE + Update
    return r_serv_tags.smembers('active_galaxies_tags')

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
                #r_serv_tags.sadd('active_taxonomies_tags', tag)
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

####  ####

def is_tag_in_all_tag(tag):
    if r_serv_tags.sismember('list_tags', tag):
        return True
    else:
        return False

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

def get_obj_tags_minimal(item_id):
    return [ {"tag": tag, "min_tag": get_min_tag(tag)} for tag in get_obj_tag(item_id) ]

def unpack_str_tags_list(str_tags_list):
    str_tags_list = str_tags_list.replace('"','\"')
    if str_tags_list:
        return str_tags_list.split(',')
    else:
        return []

# used by modal
def get_modal_add_tags(item_id, object_type='item'):
    '''
    Modal: add tags to domain or Paste
    '''
    return {"active_taxonomies": get_active_taxonomies(), "active_galaxies": get_active_galaxies(),
            "object_id": item_id, "object_type": object_type}

######## NEW VERSION ########
def get_tag_first_seen(tag, r_int=False):
    '''
    Get tag first seen (current: item only)
    '''
    res = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'first_seen')
    if r_int:
        if res is None:
            return 99999999
        else:
            return int(res)
    return res

def get_tag_last_seen(tag, r_int=False):
    '''
    Get tag last seen (current: item only)
    '''
    res = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')
    if r_int:
        if res is None:
            return 0
        else:
            return int(res)
    return res

def get_tag_metadata(tag, r_int=False):
    '''
    Get tag metadata (current: item only)
    '''
    tag_metadata = {"tag": tag}
    tag_metadata['first_seen'] = get_tag_first_seen(tag)
    tag_metadata['last_seen'] = get_tag_last_seen(tag)
    return tag_metadata

def is_obj_tagged(object_id, tag):
    '''
    Check if a object is tagged

    :param object_id: object id
    :type domain: str
    :param tag: object type
    :type domain: str

    :return: is object tagged
    :rtype: boolean
    '''
    return r_serv_metadata.sismember('tag:{}'.format(object_id), tag)

def get_all_tags():
    return list(r_serv_tags.smembers('list_tags'))

def get_all_obj_tags(object_type):
    return list(r_serv_tags.smembers('list_tags:{}'.format(object_type)))

def get_obj_tag(object_id):
    '''
    Retun all the tags of a given object.
    :param object_id: (item_id, domain, ...)
    '''
    res = r_serv_metadata.smembers('tag:{}'.format(object_id))
    if res:
        return list(res)
    else:
        return []

def update_tag_first_seen(tag, tag_first_seen, tag_last_seen):
    if tag_first_seen == tag_last_seen:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_first_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'first_seen', tag_first_seen)
        # no tag in db
        else:
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
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'first_seen')
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'last_seen')
    else:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_last_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'last_seen', tag_last_seen)
        else:
            tag_last_seen = Date.date_substract_day(tag_last_seen)
            update_tag_last_seen(tag, tag_first_seen, tag_last_seen)

def update_tag_metadata(tag, tag_date, object_type=None, add_tag=True):
    '''
    Update tag metadata (current: item only)
    '''
    if object_type=="item":
        # get object metadata
        tag_metadata = get_tag_metadata(tag, r_int=True)
        #############
        ## ADD tag ##
        if add_tag:
            # update fisrt_seen
            if tag_date < tag_metadata['first_seen']:
                r_serv_tags.hset('tag_metadata:{}'.format(tag), 'first_seen', tag_date)
            # update last_seen
            if tag_date > tag_metadata['last_seen']:
                r_serv_tags.hset('tag_metadata:{}'.format(tag), 'last_seen', tag_date)
        ################
        ## REMOVE tag ##
        else:
            if tag_date == tag_metadata['first_seen']:
                update_tag_first_seen(object_type, tag, tag_metadata['first_seen'], tag_metadata['last_seen'])
            if tag_date == tag_metadata['last_seen']:
                update_tag_last_seen(tag, tag_metadata['first_seen'], tag_metadata['last_seen'])

def update_tag_global_by_obj_type(object_type, tag):
    tag_deleted = False
    if object_type=='item':
        if not r_serv_tags.exists('tag_metadata:{}'.format(tag)):
            tag_deleted = True
    else:
        if not r_serv_tags.exists('{}:{}'.format(object_type, tag)):
            tag_deleted = True
    if tag_deleted:
        # update object global tags
        r_serv_tags.srem('list_tags:{}'.format(object_type), tag)
        # update global tags
        for obj_type in Correlate_object.get_all_objects():
            if r_serv_tags.exists('{}:{}'.format(obj_type, tag)):
                tag_deleted = False
        if tag_deleted:
            r_serv_tags.srem('list_tags', tag)

def add_global_tag(tag, object_type=None):
    '''
    Create a set of all tags used in AIL (all + by object)

    :param tag: tag
    :type domain: str
    :param object_type: object type
    :type domain: str
    '''
    r_serv_tags.sadd('list_tags', tag)
    if object_type:
        r_serv_tags.sadd('list_tags:{}'.format(object_type), tag)

def add_obj_tags(object_id, object_type, tags=[], galaxy_tags=[]):
    obj_date = get_obj_date(object_type, object_id)
    for tag in tags:
        if tag:
            taxonomie = get_taxonomie_from_tag(tag)
            if is_taxonomie_tag_enabled(taxonomie, tag):
                add_tag(object_type, tag, object_id, obj_date=obj_date)
            else:
                return ({'status': 'error', 'reason': 'Tags or Galaxy not enabled', 'value': tag}, 400)

    for tag in galaxy_tags:
        if tag:
            galaxy = get_galaxy_from_tag(tag)
            if is_galaxy_tag_enabled(galaxy, tag):
                add_tag(object_type, tag, object_id, obj_date=obj_date)
            else:
                return ({'status': 'error', 'reason': 'Tags or Galaxy not enabled', 'value': tag}, 400)

# TEMPLATE + API QUERY
def api_add_obj_tags(tags=[], galaxy_tags=[], object_id=None, object_type="item"):
    res_dict = {}
    if object_id == None:
        return ({'status': 'error', 'reason': 'object_id id not found'}, 404)
    if not tags and not galaxy_tags:
        return ({'status': 'error', 'reason': 'Tags or Galaxy not specified'}, 400)
    if object_type not in ('item', 'domain'):  # # TODO: put me in another file
        return ({'status': 'error', 'reason': 'Incorrect object_type'}, 400)

    # remove empty tags
    tags = list(filter(bool, tags))
    galaxy_tags = list(filter(bool, galaxy_tags))

    res = add_obj_tags(object_id, object_type, tags=tags, galaxy_tags=galaxy_tags)
    if res:
        return res

    res_dict['tags'] = tags + galaxy_tags
    res_dict['id'] = object_id
    res_dict['type'] = object_type
    return (res_dict, 200)

def add_obj_tag(object_type, object_id, tag, obj_date=None):
    if object_type=="item": # # TODO: # FIXME: # REVIEW: rename me !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if obj_date is None:
            raise ValueError("obj_date is None")

        # add tag
        r_serv_metadata.sadd('tag:{}'.format(object_id), tag)
        r_serv_tags.sadd('{}:{}'.format(tag, obj_date), object_id)

        # add domain tag
        if Item.is_crawled(object_id) and tag!='infoleak:submission="crawler"' and tag != 'infoleak:submission="manual"':
            domain = Item.get_item_domain(object_id)
            add_tag("domain", tag, domain)
    else:
        r_serv_metadata.sadd('tag:{}'.format(object_id), tag)
        r_serv_tags.sadd('{}:{}'.format(object_type, tag), object_id)

def add_tag(object_type, tag, object_id, obj_date=None):
    # new tag
    if not is_obj_tagged(object_id, tag):
        # # TODO: # FIXME: sanityze object_type
        if not obj_date:
            obj_date = get_obj_date(object_type, object_id)
        add_global_tag(tag, object_type=object_type)
        add_obj_tag(object_type, object_id, tag, obj_date=obj_date)
        update_tag_metadata(tag, obj_date)

    # create tags stats  # # TODO:  put me in cache
    r_serv_tags.hincrby('daily_tags:{}'.format(datetime.date.today().strftime("%Y%m%d")), tag, 1)

def delete_obj_tag(object_type, object_id, tag, obj_date):
    if object_type=="item": # # TODO: # FIXME: # REVIEW: rename me !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        obj_date = get_obj_date(object_type, object_id)
        r_serv_metadata.srem('tag:{}'.format(object_id), tag)
        r_serv_tags.srem('{}:{}'.format(tag, obj_date), object_id)
    else:
        r_serv_metadata.srem('tag:{}'.format(object_id), tag)
        r_serv_tags.srem('{}:{}'.format(object_type, tag), object_id)

def delete_tag(object_type, tag, object_id, obj_date=None):
    # tag exist
    if is_obj_tagged(object_id, tag):
        if not obj_date:
            obj_date = get_obj_date(object_type, object_id)
        delete_obj_tag(object_type, object_id, tag, obj_date)
        update_tag_metadata(tag, obj_date, object_type=object_type, add_tag=False)
        update_tag_global_by_obj_type(object_type, tag)

    else:
        return ({'status': 'error', 'reason': 'object id or tag not found', 'value': tag}, 400)

# API QUERY
def api_delete_obj_tags(tags=[], object_id=None, object_type="item"):
    if not object_id:
        return ({'status': 'error', 'reason': 'object id not found'}, 404)
    if not tags:
        return ({'status': 'error', 'reason': 'No Tag(s) specified'}, 400)

    res = delete_obj_tags(object_id, object_type, tags=tags)
    if res:
        return res

    dict_res = {}
    dict_res['tags'] = tags
    dict_res['id'] = object_id
    return (dict_res, 200)

def delete_obj_tags(object_id, object_type, tags=[]):
    obj_date = get_obj_date(object_type, object_id)
    for tag in tags:
        res = delete_tag(object_type, tag, object_id, obj_date=obj_date)
        if res:
            return res

def get_obj_date(object_type, object_id): # # TODO: move me in another file
    if object_type == "item":
        return Item.get_item_date(object_id)
    else:
        return None
