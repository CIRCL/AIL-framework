#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis
import datetime

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib import ail_core
from lib import item_basic
from packages import Date

from pytaxonomies import Taxonomies
from pymispgalaxies import Galaxies, Clusters

config_loader = ConfigLoader()
r_tags = config_loader.get_db_conn("Kvrocks_Tags")
config_loader = None

#### CORE FUNCTIONS ####

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

# # TODO: verify tags + object_type
# get set_keys: intersection
def get_obj_keys_by_tags(tags, obj_type, subtype='', date=None):
    l_set_keys = []
    if obj_type=='item':
        for tag in tags:
            l_set_keys.append(f'{obj_type}:{subtype}:{tag}:{date}')
    else:
        for tag in tags:
            l_set_keys.append(f'{obj_type}:{subtype}:{tag}')
    return l_set_keys

def get_obj_by_tag(key_tag):
    return r_tags.smembers(key_tag)

##-- CORE FUNCTIONS --##

################################################################################
################################################################################
################################################################################
################################################################################
################################################################################

def is_obj_tagged(obj_type, obj_id, subtype=''):
    '''
    Check if a object is tagged

    :param object_id: object id
    :type domain: str

    :return: is object tagged
    :rtype: boolean
    '''
    return r_tags.exists(f'tag:{obj_type}:{subtype}:{obj_id}')

def is_obj_tagged_by_tag(obj_type, obj_id, tag, subtype=''):
    '''
    Check if a object is tagged

    :param object_id: object id
    :type domain: str
    :param tag: object type
    :type domain: str

    :return: is object tagged
    :rtype: boolean
    '''
    return r_tags.sismember(f'tag:{obj_type}:{subtype}:{obj_id}', tag)




#
#   f'tag:{obj_type}:{subtype}:{id}'              f'tag:{id}'
#
#   f'list_tags:{obj_type}:{subtype}'             f'list_tags:{obj_type}'
#
#       graph tags by days ???????????????????????????????
#
#

#               # TODO: metadata by object type ????????????
#               tag_metadata:
#               f'{tag}:{date}' -> set of item_id

#               # TODO: ADD subtype support
#               f'{obj_type}:{tag}' -> set of item_id

def get_tag_first_seen(tag, object_type=None, r_int=False):
    first_seen = r_tags.hget(f'tag_metadata:{tag}', 'first_seen')
    if r_int:
        if first_seen:
            first_seen = int(first_seen)
        else:
            first_seen = 99999999
    return first_seen
    # # TODO: LATER ADD object metadata
    # if not object_type:
    #     r_tags.hget(f'tag_metadata:{tag}', 'first_seen')
    # else:
    #     r_tags.hget(f'tag_metadata:{tag}', 'first_seen:{object_type}')

def get_tag_last_seen(tag, object_type=None, r_int=False):
    last_seen = r_tags.hget(f'tag_metadata:{tag}', 'last_seen')
    if r_int:
        if last_seen:
            last_seen = int(last_seen)
        else:
            last_seen = 0
    return last_seen

def get_tag_metadata_date(tag, r_int=False):
    return {'first_seen': get_tag_first_seen(tag, r_int=r_int), 'last_seen': get_tag_last_seen(tag, r_int=r_int)}

def set_tag_first_seen(tag, date):
    r_tags.hset(f'tag_metadata:{tag}', 'first_seen', date)

def set_tag_last_seen(tag, date):
    r_tags.hset(f'tag_metadata:{tag}', 'last_seen', date)

# # TODO: handle others objects date
def _update_tag_first_seen(tag, first_seen, last_seen):
    if first_seen == last_seen:
        if r_tags.scard(f'item::{tag}:{first_seen}') > 0:
            r_tags.hset(f'tag_metadata:{tag}', 'first_seen', first_seen)
        # no tag in db
        else:
            r_tags.hdel(f'tag_metadata:{tag}', 'first_seen')
            r_tags.hdel(f'tag_metadata:{tag}', 'last_seen')
    else:
        if r_tags.scard(f'item::{tag}:{first_seen}') > 0:
            r_tags.hset(f'tag_metadata:{tag}', 'first_seen', first_seen)
        else:
            first_seen = Date.date_add_day(first_seen)
            if int(last_seen) >= int(first_seen):
                _update_tag_first_seen(tag, first_seen, last_seen)

# # TODO:
def _update_tag_last_seen(tag, first_seen, last_seen):
    if first_seen == last_seen:
        if r_tags.scard(f'item::{tag}:{last_seen}') > 0:
            r_tags.hset(f'tag_metadata:{tag}', 'last_seen', last_seen)
        # no tag in db
        else:
            r_tags.hdel(f'tag_metadata:{tag}', 'first_seen')
            r_tags.hdel(f'tag_metadata:{tag}', 'last_seen')
    else:
        if r_tags.scard(f'item::{tag}:{last_seen}') > 0:
            r_tags.hset(f'tag_metadata:{tag}', 'last_seen', last_seen)
        else:
            last_seen = Date.date_substract_day(str(last_seen))
            if int(last_seen) >= int(first_seen):
                _update_tag_last_seen(tag, first_seen, last_seen)


def update_tag_metadata(tag, date, delete=False): # # TODO: delete Tags
    date = int(date)
    tag_date = get_tag_metadata_date(tag, r_int=True)
    # Add Tag
    if not delete:
        # update first_seen
        if date < tag_date['first_seen']:
            set_tag_first_seen(tag, date)
        # update last_seen
        if date > tag_date['last_seen']:
            set_tag_last_seen(tag, date)
    # Delete Tag
    else:
        if date == tag_date['first_seen']:
            _update_tag_first_seen(tag, tag_date['first_seen'], tag_date['last_seen'])
        if date == tag_date['last_seen']:
            _update_tag_last_seen(tag, tag_date['first_seen'], tag_date['last_seen'])



# old
# r_tags.smembers(f'{tag}:{date}')
# r_tags.smembers(f'{obj_type}:{tag}')
def get_tag_objects(obj_type, subtype='', date=''):
    if obj_type == 'item':
        return r_tags.smembers(f'{obj_type}:{subtype}:{tag}:{date}')
    else:
        return r_tags.smembers(f'{obj_type}:{subtype}:{tag}')

def get_object_tags(obj_type, obj_id, subtype=''):
    return r_tags.smembers(f'tag:{obj_type}:{subtype}:{obj_id}')

def add_object_tag(tag, obj_type, id, subtype=''): #############################
    if r_tags.sadd(f'tag:{obj_type}:{subtype}:{id}', tag) == 1:
        r_tags.sadd('list_tags', tag)
        r_tags.sadd(f'list_tags:{obj_type}', tag)
        r_tags.sadd(f'list_tags:{obj_type}:{subtype}', tag)
        if obj_type == 'item':
            date = item_basic.get_item_date(id)
            r_tags.sadd(f'{obj_type}:{subtype}:{tag}:{date}', id)

            # add domain tag
            if item_basic.is_crawled(id) and tag!='infoleak:submission="crawler"' and tag != 'infoleak:submission="manual"':
                domain = item_basic.get_item_domain(id)
                add_object_tag(tag, "domain", domain)

            update_tag_metadata(tag, date)
        else:
            r_tags.sadd(f'{obj_type}:{subtype}:{tag}', id)

        r_tags.hincrby(f'daily_tags:{datetime.date.today().strftime("%Y%m%d")}', tag, 1)

def update_tag_global_by_obj_type(tag, object_type, subtype=''):
    tag_deleted = False
    if object_type=='item':
        if not r_tags.exists(f'tag_metadata:{tag}'):
            tag_deleted = True
    else:
        if not r_tags.exists(f'{object_type}:{subtype}:{tag}'):
            r_tags.srem(f'list_tags:{obj_type}:{subtype}', tag)
            # Iterate on all subtypes
            delete_global_obj_tag = True
            for obj_subtype in ail_core.get_object_all_subtypes():
                if r_tags.exists(f'list_tags:{obj_type}:{subtype}'):
                    delete_global_obj_tag = False
                    break
            if delete_global_obj_tag:
                r_tags.srem(f'list_tags:{obj_type}', tag)
                tag_deleted = True
    if tag_deleted:
        # update global tags
        for obj_type in ail_core.get_all_objects():
            if r_tags.exists(f'{obj_type}:{tag}'):
                tag_deleted = False
        if tag_deleted:
            r_tags.srem('list_tags', tag)

def delete_object_tag(tag, obj_type, id, subtype=''):
    if is_obj_tagged_by_tag(obj_type, id, tag, subtype=subtype):
        r_tags.sadd('list_tags', tag)
        r_tags.sadd(f'list_tags:{obj_type}', tag)
        r_tags.sadd(f'list_tags:{obj_type}:{subtype}', tag)
        if obj_type == 'item':
            date = item_basic.get_item_date(id)
            r_tags.srem(f'{obj_type}:{subtype}:{tag}:{date}', id)

            update_tag_metadata(tag, date, delete=True)
        else:
            r_tags.srem(f'{obj_type}:{subtype}:{tag}', id)

        r_tags.srem(f'tag:{obj_type}:{subtype}:{id}', tag)
        update_tag_global_by_obj_type(tag, obj_type, subtype=subtype)

################################################################################################################

# TODO: rewrite me
# TODO: other objects
def get_obj_by_tags(obj_type, l_tags, date_from=None, date_to=None, nb_obj=50, page=1):
    # with daterange
    l_tagged_obj = []
    if obj_type=='item':
        #sanityze date
        date_range = sanitise_tags_date_range(l_tags, date_from=date_from, date_to=date_to)
        l_dates = Date.substract_date(date_range['date_from'], date_range['date_to'])
        for date_day in l_dates:
            l_set_keys = get_obj_keys_by_tags(l_tags, obj_type, date=date_day)
            # if len(l_set_keys) > nb_obj:
            #     return l_tagged_obj
            if len(l_set_keys) < 2:
                date_day_obj = get_obj_by_tag(l_set_keys[0])
            else:
                date_day_obj = r_tags.sinter(l_set_keys[0], *l_set_keys[1:])

            # next_nb_start = len(l_tagged_obj) + len(date_day_obj) - nb_obj
            # if next_nb_start > 0:
            #  get + filter nb_start
            l_tagged_obj.extend( date_day_obj )

        # handle pagination
        nb_all_elem = len(l_tagged_obj)
        nb_pages = nb_all_elem / nb_obj
        if not nb_pages.is_integer():
            nb_pages = int(nb_pages)+1
        else:
            nb_pages = int(nb_pages)
        if page > nb_pages:
            page = nb_pages

        start = nb_obj*(page -1)
        if nb_pages > 1:
            stop = (nb_obj*page)
            l_tagged_obj = l_tagged_obj[start:stop]
        # only one page
        else:
            stop = nb_all_elem
            l_tagged_obj = l_tagged_obj[start:]

        if stop > nb_all_elem:
            stop = nb_all_elem
        stop = stop -1

        return {"tagged_obj":l_tagged_obj, "date" : date_range,
                "page":page, "nb_pages":nb_pages, "nb_first_elem":start+1, "nb_last_elem":stop+1, "nb_all_elem":nb_all_elem}

    # without daterange
    else:
        l_set_keys = get_obj_keys_by_tags(l_tags, obj_type)
        if len(l_set_keys) < 2:
            l_tagged_obj = get_obj_by_tag(l_set_keys[0])
        else:
            l_tagged_obj = r_tags.sinter(l_set_keys[0], *l_set_keys[1:])

        if not l_tagged_obj:
            return {"tagged_obj":l_tagged_obj, "page":0, "nb_pages":0}

        # handle pagination
        nb_all_elem = len(l_tagged_obj)
        nb_pages = nb_all_elem / nb_obj
        if not nb_pages.is_integer():
            nb_pages = int(nb_pages)+1
        else:
            nb_pages = int(nb_pages)
        if page > nb_pages:
            page = nb_pages

        # multiple pages
        if nb_pages > 1:
            start = nb_obj*(page -1)
            stop = (nb_obj*page) -1
            current_index = 0
            l_obj = []
            for elem in l_tagged_obj:
                if current_index > stop:
                    break
                if start <= current_index and stop >= current_index:
                    l_obj.append(elem)
                current_index += 1
            l_tagged_obj = l_obj
            stop += 1
            if stop > nb_all_elem:
                stop = nb_all_elem
        # only one page
        else:
            start = 0
            stop = nb_all_elem
            l_tagged_obj = list(l_tagged_obj)

        return {"tagged_obj":l_tagged_obj, "page":page, "nb_pages":nb_pages, "nb_first_elem":start+1, "nb_last_elem":stop, "nb_all_elem":nb_all_elem}



################################################################################
################################################################################
################################################################################
################################################################################

#### Taxonomies - Galaxies ####

################################################################################
# galaxies = Galaxies()
# clusters = Clusters(skip_duplicates=True)
#
# list_all_tags = {}
# for name, c in clusters.items(): #galaxy name + tags
#     list_all_tags[name] = c
#
# list_galaxies = []
# for g in galaxies.values():
#     list_galaxies.append(g.to_json())
#
# list_clusters = []
# for c in clusters.values():
#     list_clusters.append(c.to_json())
#
# # tags numbers in galaxies
# total_tags = {}
# for name, tags in clusters.items(): #galaxie name + tags
#     total_tags[name] = len(tags)
################################################################################

#### Taxonomies ####

def get_taxonomy_tags_from_cluster(taxonomy_name):
    taxonomies = Taxonomies()
    taxonomy = taxonomies[taxonomy_name]
    return taxonomy.machinetags()

# TODO: ADD api handler
def enable_taxonomy(taxonomy):
    tags = get_taxonomy_tags_from_cluster(taxonomy)
    r_tags.sadd('active_taxonomies', taxonomy)
    for tag in tags:
        r_tags.sadd(f'active_tag_{taxonomy}', tag)

# def enable_taxonomy(taxonomie, enable_tags=True):
#     '''
#     Enable a taxonomy. (UI)
#
#     :param taxonomie: MISP taxonomy
#     :type taxonomie: str
#     :param enable_tags: crawled domain
#     :type enable_tags: boolean
#     '''
#     taxonomies = Taxonomies()
#     if enable_tags:
#         taxonomie_info = taxonomies.get(taxonomie)
#         if taxonomie_info:
#             # activate taxonomie
#             r_tags.sadd('active_taxonomies', taxonomie)
#             # activate taxonomie tags
#             for tag in taxonomie_info.machinetags():
#                 r_tags.sadd('active_tag_{}'.format(taxonomie), tag)
#                 #r_tags.sadd('active_taxonomies_tags', tag)
#         else:
#             print('Error: {}, please update pytaxonomies'.format(taxonomie))

#### Galaxies ####

def get_galaxy_tags_from_cluster(galaxy_name):
    clusters = Clusters(skip_duplicates=True)
    cluster = clusters[galaxy_name]
    return cluster.machinetags()

def get_galaxy_tags_with_sysnonym_from_cluster(galaxy_name):
    tags = {}
    clusters = Clusters(skip_duplicates=True)
    cluster = clusters[galaxy_name]
    for data in cluster.to_dict()['values']:
        tag = f'misp-galaxy:{cluster.type}="{data.value}"'
        synonyms = data.meta.synonyms
        if not synonyms:
            synonyms = []
        tags[tag] = synonyms
    return tags

def enable_galaxy(galaxy):
    tags = get_galaxy_tags_with_sysnonym_from_cluster(galaxy)
    r_tags.sadd('active_galaxies', galaxy)
    for tag in tags:
        r_tags.sadd(f'active_tag_galaxies_{galaxy}', tag)
        # synonyms
        for synonym in tags[tag]:
            r_tags.sadd(f'synonym_tag_{tag}', synonym)



################################################################################
################################################################################
################################################################################
################################################################################

def get_taxonomie_from_tag(tag):
    try:
        return tag.split(':')[0]
    except IndexError:
        return None

def get_galaxy_from_tag(tag):
    try:
        galaxy = tag.split(':')[1]
        galaxy = galaxy.split('=')[0]
        return galaxy
    except IndexError:
        return None

def get_taxonomies():
    return Taxonomies().keys()

def is_taxonomie(taxonomie, taxonomies=[]):
    if not taxonomies:
        taxonomies = get_taxonomies()
    return taxonomie in taxonomies

def get_active_taxonomies(r_set=False):
    res = r_tags.smembers('active_taxonomies')
    if r_set:
        return set(res)
    return res

def get_active_galaxies(r_set=False):
    res = r_tags.smembers('active_galaxies')
    if r_set:
        return set(res)
    return res

def get_all_taxonomies_tags(): # # TODO: add + REMOVE + Update
    return r_tags.smembers('active_taxonomies_tags')

def get_all_galaxies_tags(): # # TODO: add + REMOVE + Update
    return r_tags.smembers('active_galaxies_tags')

def get_all_custom_tags(): # # TODO: add + REMOVE + Update
    return r_tags.smembers('tags:custom')

def get_taxonomies_enabled_tags(r_list=False):
    l_tag_keys = []
    for taxonomie in get_active_taxonomies():
        l_tag_keys.append(f'active_tag_{taxonomie}')
    if len(l_tag_keys) > 1:
        res = r_tags.sunion(l_tag_keys[0], *l_tag_keys[1:])
    elif l_tag_keys:
        res = r_tags.smembers(l_tag_keys[0])
    #### # WARNING: # TODO: DIRTY FIX, REPLACE WITH LOCAL TAGS ####


    if r_list:
        return list(res)
    else:
        return res

def get_galaxies_enabled_tags():
    l_tag_keys = []
    for galaxy in get_active_galaxies():
        l_tag_keys.append(f'active_tag_galaxies_{galaxy}')
    if len(l_tag_keys) > 1:
        return r_tags.sunion(l_tag_keys[0], *l_tag_keys[1:])
    elif l_tag_keys:
        return r_tags.smembers(l_tag_keys[0])
    else:
        return []

def get_custom_enabled_tags(r_list=False):
    res = r_tags.smembers('tags:custom:enabled_tags')
    if r_list:
        return list(res)
    else:
        return res

def get_taxonomies_customs_tags(r_list=False):
    tags = get_custom_enabled_tags().union(get_taxonomies_enabled_tags())
    if r_list:
        tags = list(tags)
    return tags

def get_taxonomie_enabled_tags(taxonomie, r_list=False):
    res = r_tags.smembers(f'active_tag_{taxonomie}')
    if r_list:
        return list(res)
    else:
        return res

def get_galaxy_enabled_tags(galaxy, r_list=False):
    res = r_tags.smembers(f'active_tag_galaxies_{galaxy}')
    if r_list:
        return list(res)
    else:
        return res

def is_taxonomie_tag_enabled(taxonomie, tag):
    if tag in r_tags.smembers('active_tag_' + taxonomie):
        return True
    else:
        return False

def is_galaxy_tag_enabled(galaxy, tag):
    if tag in r_tags.smembers('active_tag_galaxies_' + galaxy):
        return True
    else:
        return False

def is_custom_tag_enabled(tag):
    return r_tags.sismember('tags:custom:enabled_tags', tag)

# Check if tags are enabled in AIL
def is_valid_tags_taxonomies_galaxy(list_tags, list_tags_galaxy):
    if list_tags:
        active_taxonomies = get_active_taxonomies()

        for tag in list_tags:
            taxonomie = get_taxonomie_from_tag(tag)
            if taxonomie is None:
                return False
            if taxonomie not in active_taxonomies:
                return False
            if not is_taxonomie_tag_enabled(taxonomie, tag):
                return False

    if list_tags_galaxy:
        active_galaxies = get_active_galaxies()

        for tag in list_tags_galaxy:
            galaxy = get_galaxy_from_tag(tag)
            if galaxy is None:
                return False
            if galaxy not in active_galaxies:
                return False
            if not is_galaxy_tag_enabled(galaxy, tag):
                return False
    return True

def is_taxonomie_tag(tag, namespace=None):
    if not namespace:
        namespace = tag.split(':')[0]
    if namespace != 'misp-galaxy':
        return is_taxonomie(namespace)
    else:
        return False

def is_galaxy_tag(tag, namespace=None):
    if not namespace:
        namespace = tag.split(':')[0]
    if namespace == 'misp-galaxy':
        return True
    else:
        return False

def is_custom_tag(tag):
    return r_tags.sismember('tags:custom', tag)

# # TODO:
# def is_valid_tag(tag):
#     pass

def is_enabled_tag(tag, enabled_namespace=None):
    if is_taxonomie_tag(tag):
        return is_enabled_taxonomie_tag(tag, enabled_taxonomies=enabled_namespace)
    else:
        return is_enabled_galaxy_tag(tag, enabled_galaxies=enabled_namespace)

def are_enabled_tags(tags):
    enabled_taxonomies = get_active_taxonomies(r_set=True)
    enabled_galaxies = get_active_galaxies(r_set=True)
    for tag in tags:
        if is_taxonomie_tag(tag):
            res = is_enabled_taxonomie_tag(tag, enabled_taxonomies=enabled_taxonomies)
        else:
            res = is_enabled_galaxy_tag(tag, enabled_galaxies=enabled_galaxies)
        if not res:
            return False
    return True

def is_enabled_taxonomie_tag(tag, enabled_taxonomies=None):
    if not enabled_taxonomies:
        enabled_taxonomies = get_active_taxonomies()
    taxonomie = get_taxonomie_from_tag(tag)
    if taxonomie is None:
        return False
    if taxonomie not in enabled_taxonomies:
        return False
    if not is_taxonomie_tag_enabled(taxonomie, tag):
        return False
    return True

def is_enabled_galaxy_tag(tag, enabled_galaxies=None):
    if not enabled_galaxies:
        enabled_galaxies = get_active_galaxies()
    galaxy = get_galaxy_from_tag(tag)
    if galaxy is None:
        return False
    if galaxy not in enabled_galaxies:
        return False
    if not is_galaxy_tag_enabled(galaxy, tag):
        return False
    return True

def sort_tags_taxonomies_galaxies(tags):
    taxonomies_tags = []
    galaxies_tags = []
    for tag in tags:
        if is_taxonomie_tag(tag):
            taxonomies_tags.append(tag)
        else:
            galaxies_tags.append(tag)
    return taxonomies_tags, galaxies_tags

##-- Taxonomies - Galaxies --##

def is_tag_in_all_tag(tag):
    if r_tags.sismember('list_tags', tag):
        return True
    else:
        return False

def get_tag_synonyms(tag):
    return r_tags.smembers(f'synonym_tag_{tag}')

def get_tag_dislay_name(tag):
    tag_synonyms = get_tag_synonyms(tag)
    if not tag_synonyms:
        return tag
    else:
        return tag + ', '.join(tag_synonyms)

def get_tags_selector_dict(tags):
    list_tags = []
    for tag in tags:
        list_tags.append(get_tag_selector_dict(tag))
    return list_tags

def get_tag_selector_dict(tag):
    return {'name':get_tag_dislay_name(tag),'id':tag}

def get_tags_selector_data():
    dict_selector = {}
    dict_selector['active_taxonomies'] = get_active_taxonomies()
    dict_selector['active_galaxies'] = get_active_galaxies()
    return dict_selector

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

# TODO: ADD object type
def get_obj_tags_minimal(item_id): ####?
    return [ {"tag": tag, "min_tag": get_min_tag(tag)} for tag in get_object_tags('item', item_id) ]

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
def create_custom_tag(tag):
    r_tags.sadd('tags:custom', tag)
    r_tags.sadd('tags:custom:enabled_tags', tag)

# # TODO: ADD color
def get_tag_metadata(tag, r_int=False):
    '''
    Get tag metadata (current: item only)
    '''
    tag_metadata = {"tag": tag}
    tag_metadata['first_seen'] = get_tag_first_seen(tag, r_int=r_int)
    tag_metadata['last_seen'] = get_tag_last_seen(tag, r_int=r_int)
    return tag_metadata

def get_tags_min_last_seen(l_tags, r_int=False):
    '''
    Get max last seen from a list of tags (current: item only)
    '''
    min_last_seen = 99999999
    for tag in l_tags:
        last_seen = get_tag_last_seen(tag, r_int=True)
        if last_seen < min_last_seen:
                min_last_seen = last_seen
    if r_int:
        return min_last_seen
    else:
        return str(min_last_seen)

def get_all_tags():
    return list(r_tags.smembers('list_tags'))

def get_all_obj_tags(obj_type):
    return list(r_tags.smembers(f'list_tags:{obj_type}'))

## Objects tags ##

###################################################################################
###################################################################################
###################################################################################
###################################################################################
###################################################################################
###################################################################################
###################################################################################
###################################################################################
###################################################################################

def add_global_tag(tag, object_type=None):
    '''
    Create a set of all tags used in AIL (all + by object)

    :param tag: tag
    :type domain: str
    :param object_type: object type
    :type domain: str
    '''
    r_tags.sadd('list_tags', tag)
    if object_type:
        r_tags.sadd('list_tags:{}'.format(object_type), tag)

def add_obj_tags(object_id, object_type, tags=[], galaxy_tags=[]):
    obj_date = get_obj_date(object_type, object_id)
    for tag in tags:
        if tag:
            taxonomie = get_taxonomie_from_tag(tag)
            if is_taxonomie_tag_enabled(taxonomie, tag):
                add_object_tag(tag, object_type, object_id)
            else:
                return ({'status': 'error', 'reason': 'Tags or Galaxy not enabled', 'value': tag}, 400)

    for tag in galaxy_tags:
        if tag:
            galaxy = get_galaxy_from_tag(tag)
            if is_galaxy_tag_enabled(galaxy, tag):
                add_object_tag(tag, object_type, object_id)
            else:
                return ({'status': 'error', 'reason': 'Tags or Galaxy not enabled', 'value': tag}, 400)

# TEMPLATE + API QUERY
def api_add_obj_tags(tags=[], galaxy_tags=[], object_id=None, object_type="item"):
    res_dict = {}
    if object_id == None:
        return ({'status': 'error', 'reason': 'object_id id not found'}, 404)
    if not tags and not galaxy_tags:
        return ({'status': 'error', 'reason': 'Tags or Galaxy not specified'}, 400)
    if object_type not in ('item', 'domain', 'image', 'decoded'):  # # TODO: put me in another file
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

# def add_tag(object_type, tag, object_id, obj_date=None):
#     # new tag
#     if not is_obj_tagged(object_id, tag):
#         # # TODO: # FIXME: sanityze object_type
#         if obj_date:
#             try:
#                 obj_date = int(obj_date)
#             except:
#                 obj_date = None
#         if not obj_date:
#             obj_date = get_obj_date(object_type, object_id)
#         add_global_tag(tag, object_type=object_type)
#         add_obj_tag(object_type, object_id, tag, obj_date=obj_date)
#         update_tag_metadata(tag, obj_date, object_type=object_type)
#
#     # create tags stats  # # TODO:  put me in cache
#     r_tags.hincrby('daily_tags:{}'.format(datetime.date.today().strftime("%Y%m%d")), tag, 1)

# def delete_obj_tag(object_type, object_id, tag, obj_date):
#     if object_type=="item": # # TODO: # FIXME: # REVIEW: !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#         obj_date = get_obj_date(object_type, object_id)
#         r_serv_metadata.srem('tag:{}'.format(object_id), tag)
#         r_tags.srem('{}:{}'.format(tag, obj_date), object_id)
#     else:
#         r_serv_metadata.srem('tag:{}'.format(object_id), tag)
#         r_tags.srem('{}:{}'.format(object_type, tag), object_id)

def delete_tag(object_type, tag, object_id, obj_date=None): ################################ # TODO:
    # tag exist
    if is_obj_tagged(object_id, tag):
        if not obj_date:
            obj_date = get_obj_date(object_type, object_id)
        delete_obj_tag(object_type, object_id, tag, obj_date)
        update_tag_metadata(tag, obj_date, object_type=object_type, add_tag=False)
        update_tag_global_by_obj_type(object_type, tag)

    else:
        return ({'status': 'error', 'reason': 'object id or tag not found', 'value': tag}, 400)

# # TODO: move me
def get_obj_date(object_type, object_id):
    if object_type == "item":
        return int(item_basic.get_item_date(object_id))
    else:
        return None

# API QUERY
def api_delete_obj_tags(tags=[], object_id=None, object_type="item"):
    if not object_id:
        return ({'status': 'error', 'reason': 'object id not found'}, 404)
    if not tags:
        return ({'status': 'error', 'reason': 'No Tag(s) specified'}, 400)

    for tag in tags:
        res = delete_object_tag(tag, object_type, object_id, subtype='')
        if res:
            return res

    dict_res = {}
    dict_res['tags'] = tags
    dict_res['id'] = object_id
    return (dict_res, 200)


# def delete_obj_tags(object_id, object_type, tags):
#     obj_date = get_obj_date(object_type, object_id)
#     for tag in tags:
#         res = delete_tag(object_type, tag, object_id, obj_date=obj_date)
#         if res:
#             return res
#
# def delete_obj_all_tags(obj_id, obj_type):
#     delete_obj_tags(obj_id, obj_type, get_obj_tag(obj_id))

def sanitise_tags_date_range(l_tags, date_from=None, date_to=None):
    if date_from is None or date_to is None:
        date_from = get_tags_min_last_seen(l_tags, r_int=False)
        date_to = date_from
    return Date.sanitise_date_range(date_from, date_to)


#### TAGS EXPORT ####
# # TODO:
def is_updated_tags_to_export(): # by type
    return False

def get_list_of_solo_tags_to_export_by_type(export_type): # by type
    if export_type in ['misp', 'thehive']:
        return r_serv_db.smembers('whitelist_{}'.format(export_type))
    else:
        return None
    #r_serv_db.smembers('whitelist_hive')

# if __name__ == '__main__':
#     galaxy = 'infoleak'
#     get_taxonomy_tags_from_cluster(galaxy)
