#!/usr/bin/env python3
# -*-coding:UTF-8 -*
import time

import redis
import datetime

import os
import json
import sys

from glob import glob

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
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None

TAGS_TO_EXCLUDE_FROM_DASHBOARD = {'infoleak:submission="crawler"', 'infoleak:submission="manual"'}

#### CORE FUNCTIONS ####

# # # # UNSAFE TAGS # # # #

# set of unsafe tags
UNSAFE_TAGS = None

def build_unsafe_tags():
    tags = set()
    # violence
    tags.add('dark-web:topic="violence"')
    tags.add('dark-web:topic="pornography-illicit-or-illegal"')
    # CE content
    tags.add('dark-web:topic="pornography-child-exploitation"')
    # add copine-scale tags
    taxonomies = Taxonomies()
    copine_scale = taxonomies.get('copine-scale')
    if copine_scale:
        for tag in copine_scale.machinetags():
            tags.add(tag)
    return tags

def is_tags_safe(ltags):
    """
    Check if a list of tags contain unsafe tags (CE, ...)
    :param ltags: list of tags
    :type ltags: list
    :return: is a tag in the set unsafe
    :rtype: boolean
    """
    global UNSAFE_TAGS
    if UNSAFE_TAGS is None:
        UNSAFE_TAGS = build_unsafe_tags()
    return UNSAFE_TAGS.isdisjoint(ltags)


# - - - UNSAFE TAGS - - - #

# # TODO: verify tags + object_type
# get set_keys: intersection
def get_obj_keys_by_tags(tags, obj_type, subtype='', date=None):
    l_set_keys = []
    if obj_type == 'item' or obj_type == 'message':
        for tag in tags:
            l_set_keys.append(f'{obj_type}:{subtype}:{tag}:{date}')
    else:
        for tag in tags:
            l_set_keys.append(f'{obj_type}:{subtype}:{tag}')
    return l_set_keys

def get_obj_by_tag(key_tag):
    return r_tags.smembers(key_tag)

# -- CORE FUNCTIONS -- #


#### Taxonomies ####

TAXONOMIES = None
def load_taxonomies():
    global TAXONOMIES
    manifest = os.path.join(os.environ['AIL_HOME'], 'files/misp-taxonomies/MANIFEST.json')
    TAXONOMIES = Taxonomies(manifest_path=manifest)

def get_taxonomies():
    if TAXONOMIES is None:
        load_taxonomies()
    return TAXONOMIES.keys()

# TODO rename me to get enabled_taxonomies
def get_active_taxonomies():
    return r_tags.smembers('taxonomies:enabled')

def is_taxonomy_enabled(taxonomy):
    # enabled = r_tags.sismember('taxonomies:enabled', taxonomy)
    try:
        enabled = r_tags.sismember('taxonomies:enabled', taxonomy)
    except redis.exceptions.ResponseError:
        enabled = False
    return enabled

def enable_taxonomy(taxonomy):
    r_tags.sadd('taxonomies:enabled', taxonomy)

def disable_taxonomy(taxonomy):
    r_tags.srem('taxonomies:enabled', taxonomy)

def exists_taxonomy(taxonomy):
    if TAXONOMIES is None:
        load_taxonomies()
    return TAXONOMIES.get(taxonomy) is not None

def get_taxonomy_description(taxonomy):
    if TAXONOMIES is None:
        load_taxonomies()
    return TAXONOMIES.get(taxonomy).description

def get_taxonomy_name(taxonomy):
    if TAXONOMIES is None:
        load_taxonomies()
    return TAXONOMIES.get(taxonomy).name

def get_taxonomy_predicates(taxonomy):
    meta = {}
    predicates = taxonomy.predicates
    for predicate in predicates:
        meta[predicate] = {}
        expanded = predicates[predicate].expanded
        if expanded:
            meta[predicate]['expanded'] = expanded
        description = predicates[predicate].description
        if description:
            meta[predicate]['description'] = description
    return meta

def get_taxonomy_refs(taxonomy):
    if TAXONOMIES is None:
        load_taxonomies()
    return TAXONOMIES.get(taxonomy).refs

def get_taxonomy_version(taxonomy):
    if TAXONOMIES is None:
        load_taxonomies()
    return TAXONOMIES.get(taxonomy).version

def get_taxonomy_tags(taxonomy, enabled=False):
    if TAXONOMIES is None:
        load_taxonomies()
    taxonomy_obj = TAXONOMIES.get(taxonomy)
    tags = []
    for p, content in taxonomy_obj.items():
        if content:
            for k, entry in content.items():
                tag = f'{taxonomy_obj.name}:{p}="{k}"'
                expanded = entry.expanded
                meta_tag = {'tag': tag, 'expanded': expanded}
                if enabled:
                    meta_tag['enabled'] = is_taxonomy_tag_enabled(taxonomy, tag)
                tags.append(meta_tag)
        else:
            tag = f'{taxonomy_obj.name}:{p}'
            expanded = content.expanded
            meta_tag = {'tag': tag, 'expanded': expanded}
            if enabled:
                meta_tag['enabled'] = is_taxonomy_tag_enabled(taxonomy, tag)
            tags.append(meta_tag)
    return tags

# TODO GET ACTIVE TAGS
# TODO GET IF TAXONOMY IS ACTIVATED
def get_taxonomy_meta(taxonomy_name, enabled=False, enabled_tags=False, nb_active_tags=False, predicates=False, tags=False, expanded=True):
    meta = {}
    if not exists_taxonomy(taxonomy_name):
        return meta
    if TAXONOMIES is None:
        load_taxonomies()
    taxonomy = TAXONOMIES.get(taxonomy_name)
    meta['description'] = taxonomy.description
    meta['name'] = taxonomy.name
    meta['version'] = taxonomy.version
    if enabled:
        meta['enabled'] = is_taxonomy_enabled(taxonomy_name)
    if predicates:
        meta['predicates'] = get_taxonomy_predicates(taxonomy)
    if taxonomy.expanded:
        meta['expanded'] = taxonomy.expanded
    if taxonomy.refs:
        meta['refs'] = taxonomy.refs

    # TODO PERF SAVE IN DB ?????
    if tags:
        if expanded:
            meta['tags'] = get_taxonomy_tags(taxonomy_name, enabled=enabled_tags)
        else:
            meta['tags'] = taxonomy.machinetags()
        meta['nb_tags'] = len(meta['tags'])
    if nb_active_tags:
        meta['nb_active_tags'] = get_taxonomy_nb_tags_enabled(taxonomy_name)
        if not tags:
            meta['nb_tags'] = len(taxonomy.machinetags())
    return meta

def get_taxonomies_meta():
    meta = {}
    for taxonomy in get_taxonomies():
        meta[taxonomy] = get_taxonomy_meta(taxonomy, enabled=True, nb_active_tags=True)
    return meta

    #### Enabled Tags ####
# r_tags.sadd('active_taxonomies', taxonomy)
def get_taxonomy_tags_enabled(taxonomy):
    return r_tags.smembers(f'taxonomy:tags:enabled:{taxonomy}')

def get_taxonomy_nb_tags_enabled(taxonomy):
    return r_tags.scard(f'taxonomy:tags:enabled:{taxonomy}')

def is_taxonomy_tag_enabled(taxonomy, tag):
    # r_tags.sismember('list_tags', tag)
    try:
        enabled = r_tags.sismember(f'taxonomy:tags:enabled:{taxonomy}', tag)
    except redis.exceptions.ResponseError:
        enabled = False
    return enabled

def add_taxonomy_tag_enabled(taxonomy, tag):
    r_tags.sadd(f'taxonomy:tags:enabled:{taxonomy}', tag)

def remove_taxonomy_tag_enabled(taxonomy, tag):
    r_tags.srem(f'taxonomy:tags:enabled:{taxonomy}', tag)

def disable_taxonomy_tags_enabled(taxonomy):
    r_tags.delete(f'taxonomy:tags:enabled:{taxonomy}')

def update_taxonomy_tag_enabled(taxonomy, tags):
    if not tags:
        return None
    enable_taxonomy(taxonomy)
    tags = set(tags)
    enabled_tags = get_taxonomy_tags_enabled(taxonomy)
    if tags != enabled_tags:
        # disable tags
        for tag in enabled_tags.difference(tags):
            remove_taxonomy_tag_enabled(taxonomy, tag)
        # enable tags
        for tag in tags:
            add_taxonomy_tag_enabled(taxonomy, tag)

def api_update_taxonomy_tag_enabled(data):
    taxonomy = data.get('taxonomy')
    if not exists_taxonomy(taxonomy):
        return {'error': f'taxonomy {taxonomy} not found'}, 404
    tags = data.get('tags', [])
    if TAXONOMIES is None:
        load_taxonomies()
    taxonomy_tags = set(TAXONOMIES.get(taxonomy).machinetags())
    for tag in tags:
        if tag not in taxonomy_tags:
            return {'error': f'tag {tag} not found'}, 404
    update_taxonomy_tag_enabled(taxonomy, tags)

def enable_taxonomy_tags(taxonomy):
    enable_taxonomy(taxonomy)
    if TAXONOMIES is None:
        load_taxonomies()
    for tag in TAXONOMIES.get(taxonomy).machinetags():
        add_taxonomy_tag_enabled(taxonomy, tag)

def api_enable_taxonomy_tags(data):
    taxonomy = data.get('taxonomy')
    if not exists_taxonomy(taxonomy):
        return {'error': f'taxonomy {taxonomy} not found'}, 404
    enable_taxonomy_tags(taxonomy)

def disable_taxonomy_tags(taxonomy):
    disable_taxonomy(taxonomy)
    disable_taxonomy_tags_enabled(taxonomy)

def api_disable_taxonomy_tags(data):
    taxonomy = data.get('taxonomy')
    if not exists_taxonomy(taxonomy):
        return {'error': f'taxonomy {taxonomy} not found'}, 404
    disable_taxonomy_tags(taxonomy)

    # -- Enabled Tags -- #

# -- Taxonomies -- #

#### GALAXIES ####

#
# var galaxy = galaxy type
#

# TODO Synonyms
GALAXIES = None
CLUSTERS = None
def load_galaxies():
    global GALAXIES
    galaxies = []
    root_dir_galaxies = os.path.join(os.environ['AIL_HOME'], 'files/misp-galaxy/galaxies')
    for galaxy_file in glob(os.path.join(root_dir_galaxies, '*.json')):
        with open(galaxy_file, 'r') as f:
            galaxies.append(json.load(f))
    GALAXIES = Galaxies(galaxies=galaxies)
    global CLUSTERS
    clusters = []
    root_dir_clusters = os.path.join(os.environ['AIL_HOME'], 'files/misp-galaxy/clusters')
    for cluster_file in glob(os.path.join(root_dir_clusters, '*.json')):
        with open(cluster_file, 'r') as f:
            clusters.append(json.load(f))
    CLUSTERS = Clusters(clusters)

def get_galaxies():
    if GALAXIES is None:
        # LOAD GALAXY + CLUSTERS
        load_galaxies()
    return GALAXIES.keys()

# TODO RENAME ME
def get_active_galaxies():
    return r_tags.smembers('galaxies:enabled')

def get_galaxy(galaxy_name):
    if GALAXIES is None:
        # LOAD GALAXY + CLUSTERS
        load_galaxies()
    return GALAXIES.get(galaxy_name)

def exists_galaxy(galaxy):
    if CLUSTERS is None:
        # LOAD GALAXY + CLUSTERS
        load_galaxies()
    return CLUSTERS.get(galaxy) is not None

def is_galaxy_enabled(galaxy):
    try:
        enabled = r_tags.sismember('galaxies:enabled', galaxy)
    except redis.exceptions.ResponseError:
        enabled = False
    return enabled

def enable_galaxy(galaxy):
    r_tags.sadd('galaxies:enabled', galaxy)

def disable_galaxy(galaxy):
    r_tags.srem('galaxies:enabled', galaxy)

def get_galaxy_meta(galaxy_name, nb_active_tags=False):
    galaxy = get_galaxy(galaxy_name)
    meta = {'name': galaxy.name, 'namespace': galaxy.namespace, 'description': galaxy.description,
            'type': galaxy.type, 'version': galaxy.version, 'enabled': is_galaxy_enabled(galaxy.type)}
    icon = galaxy.icon
    if icon == 'android' or icon == 'optin-monster' or icon == 'internet-explorer' or icon == 'btc':
        meta['icon'] = f'fab fa-{icon}'
    else:
        meta['icon'] = f'fas fa-{icon}'
    if nb_active_tags:
        meta['nb_active_tags'] = get_galaxy_nb_tags_enabled(galaxy.type)
        meta['nb_tags'] = len(get_galaxy_tags(galaxy.type))
    return meta

def get_galaxies_meta():
    galaxies = []
    for galaxy_name in get_galaxies():
        galaxies.append(get_galaxy_meta(galaxy_name, nb_active_tags=True))
    return galaxies

def get_galaxy_tag_meta(galaxy_type, tag):
    cluster = get_cluster(galaxy_type)
    if not cluster:
        return {}
    try:
        tag_val = tag.rsplit('=', 1)[1][1:-1]
    except:
        return {}
    cluster_val = cluster.cluster_values.get(tag_val)
    if not cluster_val:
        return {}
    meta = cluster_val.to_dict()
    if 'meta' in meta:
        meta['meta'] = json.loads(meta.get('meta').to_json())
        meta['meta'] = json.dumps(meta['meta'], ensure_ascii=False, indent=4)
    meta['tag'] = f'misp-galaxy:{galaxy_type}="{cluster_val.value}"'
    meta['enabled'] = is_galaxy_tag_enabled(galaxy_type, meta['tag'])
    return meta


def get_clusters():
    if CLUSTERS is None:
        # LOAD GALAXY + CLUSTERS
        load_galaxies()
    return CLUSTERS.keys()

def get_cluster(cluster_type):
    if CLUSTERS is None:
        # LOAD GALAXY + CLUSTERS
        load_galaxies()
    return CLUSTERS.get(cluster_type)

def get_galaxy_tags(galaxy_type):
    cluster = get_cluster(galaxy_type)
    return cluster.machinetags()

# TODO synonym
def get_cluster_tags(cluster_type, enabled=False):
    tags = []
    cluster = get_cluster(cluster_type)
    for cluster_val in cluster.values():
        tag = f'misp-galaxy:{cluster_type}="{cluster_val.value}"'
        meta_tag = {'tag': tag, 'description': cluster_val.description}
        if enabled:
            meta_tag['enabled'] = is_galaxy_tag_enabled(cluster_type, tag)
        cluster_val_meta = cluster_val.meta
        if cluster_val_meta:
            synonyms = cluster_val_meta.synonyms
            if not synonyms:
                synonyms = []
        else:
            synonyms = []
        meta_tag['synonyms'] = synonyms
        tags.append(meta_tag)
    return tags

def get_cluster_meta(cluster_type, tags=False, enabled=False):
    cluster = get_cluster(cluster_type)
    if not cluster:
        return {}
    meta = {'name': cluster.name, 'type': cluster.type, 'source': cluster.source,
            'authors': cluster.authors, 'description': cluster.description, 'version': cluster.version,
            'category': cluster.category}
    if enabled:
        meta['enabled'] = is_galaxy_enabled(cluster_type)
    if tags:
        meta['tags'] = get_cluster_tags(cluster_type, enabled=enabled)

    return meta

    #### Enabled Tags ####

def get_galaxy_tags_enabled(galaxy):
    return r_tags.smembers(f'galaxy:tags:enabled:{galaxy}')

def get_galaxy_nb_tags_enabled(galaxy):
    return r_tags.scard(f'galaxy:tags:enabled:{galaxy}')

def is_galaxy_tag_enabled(galaxy, tag):
    try:
        enabled = r_tags.sismember(f'galaxy:tags:enabled:{galaxy}', tag)
    except redis.exceptions.ResponseError:
        enabled = False
    return enabled

def add_galaxy_tag_enabled(galaxy, tag):
    r_tags.sadd(f'galaxy:tags:enabled:{galaxy}', tag)

def remove_galaxy_tag_enabled(galaxy, tag):
    r_tags.srem(f'galaxy:tags:enabled:{galaxy}', tag)

def disable_galaxy_tags_enabled(galaxy):
    r_tags.delete(f'galaxy:tags:enabled:{galaxy}')

def update_galaxy_tag_enabled(galaxy, tags):
    if not tags:
        return None
    enable_galaxy(galaxy)
    tags = set(tags)
    enabled_tags = get_galaxy_tags_enabled(galaxy)
    if tags != enabled_tags:
        # disable tags
        for tag in enabled_tags.difference(tags):
            remove_galaxy_tag_enabled(galaxy, tag)
        # enable tags
        for tag in tags:
            add_galaxy_tag_enabled(galaxy, tag)

def api_update_galaxy_tag_enabled(data):
    galaxy = data.get('galaxy')
    if not exists_galaxy(galaxy):
        return {'error': f'galaxy {galaxy} not found'}, 404
    tags = data.get('tags', [])
    galaxy_tags = set(get_galaxy_tags(galaxy))
    for tag in tags:
        if tag not in galaxy_tags:
            return {'error': f'tag {tag} not found'}, 404
    update_galaxy_tag_enabled(galaxy, tags)

def enable_galaxy_tags(galaxy):
    enable_galaxy(galaxy)
    for tag in get_galaxy_tags(galaxy):
        add_galaxy_tag_enabled(galaxy, tag)

def api_enable_galaxy_tags(data):
    galaxy = data.get('galaxy')
    if not exists_galaxy(galaxy):
        return {'error': f'galaxy {galaxy} not found'}, 404
    enable_galaxy_tags(galaxy)

def disable_galaxy_tags(galaxy):
    disable_galaxy(galaxy)
    disable_galaxy_tags_enabled(galaxy)

def api_disable_galaxy_tags(data):
    galaxy = data.get('galaxy')
    if not exists_galaxy(galaxy):
        return {'error': f'galaxy {galaxy} not found'}, 404
    disable_galaxy_tags(galaxy)

    # -- Enabled Tags -- #

# -- GALAXIES -- #

################################################################################
################################################################################
################################################################################
################################################################################
################################################################################

def is_obj_tagged(obj_type, obj_id, subtype=''):
    """
    Check if a object is tagged

    :param obj_type: object type
    :type obj_type: str
    :param subtype: object subtype
    :type subtype: str
    :param obj_id: object ID
    :type obj_id: str

    :return: is object tagged
    :rtype: boolean
    """
    return r_tags.exists(f'tag:{obj_type}:{subtype}:{obj_id}')

def is_obj_tagged_by_tag(obj_type, obj_id, tag, subtype=''):
    """
    Check if a object is tagged  by a specified tag

    :param obj_type: object type
    :type obj_type: str
    :param subtype: object subtype
    :type subtype: str
    :param obj_id: object ID
    :type obj_id: str
    :param tag: tag
    :type tag: str

    :return: is object tagged by a specified tag
    :rtype: boolean
    """
    return r_tags.sismember(f'tag:{obj_type}:{subtype}:{obj_id}', tag)


#
#   'tag:{obj_type}:{subtype}:{id}'              'tag:{id}'
#
#   'list_tags:{obj_type}:{subtype}'             'list_tags:{obj_type}'
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
    update = True
    while update:
        if first_seen == last_seen:
            if r_tags.scard(f'item::{tag}:{last_seen}') > 0:
                r_tags.hset(f'tag_metadata:{tag}', 'last_seen', last_seen)
                update = False
                break
            # no tag in db
            else:
                r_tags.hdel(f'tag_metadata:{tag}', 'first_seen')
                r_tags.hdel(f'tag_metadata:{tag}', 'last_seen')
                update = False
                break
        else:
            if r_tags.scard(f'item::{tag}:{last_seen}') > 0:
                r_tags.hset(f'tag_metadata:{tag}', 'last_seen', last_seen)
                update = False
                break
            else:
                last_seen = Date.date_substract_day(str(last_seen))
                if int(last_seen) < int(first_seen):
                    update = False
                    break


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
def get_tag_objects(tag, obj_type, subtype='', date=''):
    if obj_type == 'item' or obj_type == 'message':
        return r_tags.smembers(f'{obj_type}:{subtype}:{tag}:{date}')
    else:
        return r_tags.smembers(f'{obj_type}:{subtype}:{tag}')

def get_object_tags(obj_type, obj_id, subtype=''):
    return r_tags.smembers(f'tag:{obj_type}:{subtype}:{obj_id}')

def add_object_tag(tag, obj_type, obj_id, subtype=''):
    if r_tags.sadd(f'tag:{obj_type}:{subtype}:{obj_id}', tag) == 1:
        r_tags.sadd('list_tags', tag)
        r_tags.sadd(f'list_tags:{obj_type}', tag)
        r_tags.sadd(f'list_tags:{obj_type}:{subtype}', tag)
        if obj_type == 'item':
            date = item_basic.get_item_date(obj_id)
            r_tags.sadd(f'{obj_type}:{subtype}:{tag}:{date}', obj_id)

            # add domain tag
            if item_basic.is_crawled(obj_id) and tag != 'infoleak:submission="crawler"' and tag != 'infoleak:submission="manual"':
                domain = item_basic.get_item_domain(obj_id)
                add_object_tag(tag, "domain", domain)

            update_tag_metadata(tag, date)
        # MESSAGE
        elif obj_type == 'message':
            timestamp = obj_id.split('/')[1]
            date = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y%m%d')
            r_tags.sadd(f'{obj_type}:{subtype}:{tag}:{date}', obj_id)

            # TODO ADD CHAT TAGS ????

            update_tag_metadata(tag, date)
        else:
            r_tags.sadd(f'{obj_type}:{subtype}:{tag}', obj_id)

        # STATS
        r_tags.hincrby(f'daily_tags:{datetime.date.today().strftime("%Y%m%d")}', tag, 1)
        mess = f'{int(time.time())}:{obj_type}:{subtype}:{obj_id}'
        if tag not in TAGS_TO_EXCLUDE_FROM_DASHBOARD:
            r_tags.lpush('dashboard:tags', mess)
            r_tags.ltrim('dashboard:tags', 0, 19)

def get_tags_dashboard():
    return r_tags.lrange('dashboard:tags', 0, -1)


# obj -> Object()
def confirm_tag(tag, obj):
    if tag.startswith('infoleak:automatic-detection'):
        tag = tag.replace('automatic-detection', 'analyst-detection', 1)
        obj.add_tag(tag)
        return True
    return False

# FIXME
# TODO REVIEW ME
def update_tag_global_by_obj_type(tag, obj_type, subtype=''):
    tag_deleted = False
    if obj_type == 'item' or obj_type == 'message':
        if not r_tags.exists(f'tag_metadata:{tag}'): # TODO FIXME #################################################################
            tag_deleted = True
    else:
        if not r_tags.exists(f'{obj_type}:{subtype}:{tag}'):
            r_tags.srem(f'list_tags:{obj_type}:{subtype}', tag)
            # Iterate on all subtypes
            delete_global_obj_tag = True
            for obj_subtype in ail_core.get_object_all_subtypes(obj_type):
                if r_tags.exists(f'list_tags:{obj_type}:{obj_subtype}'):
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
        elif obj_type == 'message':
            timestamp = id.split('/')[1]
            date = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y%m%d')
            r_tags.srem(f'{obj_type}:{subtype}:{tag}:{date}', id)

            update_tag_metadata(tag, date, delete=True)
        else:
            r_tags.srem(f'{obj_type}:{subtype}:{tag}', id)

        r_tags.srem(f'tag:{obj_type}:{subtype}:{id}', tag)
        update_tag_global_by_obj_type(tag, obj_type, subtype=subtype)

def delete_object_tags(obj_type, subtype, obj_id):
    if not subtype:
        subtype = ''
    for tag in get_object_tags(obj_type, obj_id, subtype=subtype):
        delete_object_tag(tag, obj_type, obj_id, subtype=subtype)


def get_objs_by_date(obj_type, tags, date):
    objs = []
    if obj_type == 'item' or obj_type == 'message':
        l_set_keys = get_obj_keys_by_tags(tags, obj_type, date=date)
        if len(l_set_keys) < 2:
            objs = get_obj_by_tag(l_set_keys[0])
        else:
            objs = r_tags.sinter(l_set_keys[0], *l_set_keys[1:])
    return objs

################################################################################################################

# TODO: REWRITE OLD
# TODO: rewrite me
# TODO: other objects
def get_obj_by_tags(obj_type, l_tags, date_from=None, date_to=None, nb_obj=50, page=1):
    # with daterange
    l_tagged_obj = []
    if obj_type=='item' or obj_type=='message':
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
            return {"tagged_obj": l_tagged_obj, "page": 0, "nb_pages": 0}

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
                if start <= current_index <= stop:
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

def is_taxonomie(taxonomie, taxonomies=[]):
    if not taxonomies:
        taxonomies = get_taxonomies()
    return taxonomie in taxonomies

def get_all_taxonomies_tags(): # # TODO: add + REMOVE + Update
    return r_tags.smembers('active_taxonomies_tags')

def get_all_galaxies_tags(): # # TODO: add + REMOVE + Update
    return r_tags.smembers('active_galaxies_tags')

def get_all_custom_tags(): # # TODO: add + REMOVE + Update
    return r_tags.smembers('tags:custom')

def get_taxonomies_enabled_tags(r_list=False):
    l_tag_keys = []
    for taxonomy in get_active_taxonomies():
        l_tag_keys.append(f'taxonomy:tags:enabled:{taxonomy}')
    if len(l_tag_keys) > 1:
        res = r_tags.sunion(l_tag_keys[0], *l_tag_keys[1:])
    elif l_tag_keys:
        res = r_tags.smembers(l_tag_keys[0])
    else:
        res = []
    #### # WARNING: # TODO: DIRTY FIX, REPLACE WITH LOCAL TAGS ####

    if r_list:
        return list(res)
    else:
        return res

def get_galaxies_enabled_tags():
    l_tag_keys = []
    for galaxy in get_active_galaxies():
        l_tag_keys.append(f'galaxy:tags:enabled:{galaxy}')
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

# TODO MOVE ME
# TODO MOVE ME
# TODO MOVE ME
# TODO MOVE ME
def get_taxonomie_enabled_tags(taxonomy, r_list=False):
    res = get_taxonomy_tags_enabled(taxonomy)
    if r_list:
        return list(res)
    else:
        return res

# TODO MOVE ME
# TODO MOVE ME
# TODO MOVE ME
# TODO MOVE ME
def get_galaxy_enabled_tags(galaxy, r_list=False):
    res = get_galaxy_tags_enabled(galaxy)
    if r_list:
        return list(res)
    else:
        return res




# def is_galaxy_tag_enabled(galaxy, tag):
#     if tag in r_tags.smembers('active_tag_galaxies_' + galaxy):
#         return True
#     else:
#         return False

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
            if not is_taxonomy_tag_enabled(taxonomie, tag):
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
    try:
        return r_tags.sismember('tags:custom', tag)
    except:
        return False

# # TODO:
# def is_valid_tag(tag):
#     pass

def is_enabled_tag(tag, enabled_namespace=None):
    if is_taxonomie_tag(tag):
        return is_enabled_taxonomie_tag(tag, enabled_taxonomies=enabled_namespace)
    else:
        return is_enabled_galaxy_tag(tag, enabled_galaxies=enabled_namespace)

def are_enabled_tags(tags):
    enabled_taxonomies = get_active_taxonomies()
    enabled_galaxies = get_active_galaxies()
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
    if not is_taxonomy_tag_enabled(taxonomie, tag):
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

def sort_tags_taxonomies_galaxies_customs(tags):
    taxonomies_tags = []
    galaxies_tags = []
    customs_tags = []
    for tag in tags:
        if is_taxonomie_tag(tag):
            taxonomies_tags.append(tag)
        elif is_custom_tag(tag):
            print()
            customs_tags.append(tag)
        else:
            galaxies_tags.append(tag)
    return taxonomies_tags, galaxies_tags, customs_tags

##-- Taxonomies - Galaxies --##

def is_tag_in_all_tag(tag):
    if r_tags.sismember('list_tags', tag):
        return True
    else:
        return False

def get_tag_synonyms(tag): #####################################3
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
    return {'name': get_tag_dislay_name(tag), 'id': tag}

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
def get_modal_add_tags(object_id, object_type='item', object_subtype=''):
    '''
    Modal: add tags to domain or Paste
    '''
    return {"active_taxonomies": get_active_taxonomies(), "active_galaxies": get_active_galaxies(),
            "object_id": object_id, "object_type": object_type, "object_subtype": object_subtype}

#####################################################################################
#####################################################################################
#####################################################################################

######## NEW VERSION ########
def create_custom_tag(tag):
    if not is_taxonomie_tag(tag) and not is_galaxy_tag(tag):
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

def get_tags_min_first_seen(l_tags, r_int=False):
    """
    Get min first seen from a list of tags (current: daterange objs only)
    """
    min_first_seen = 99999999
    for tag in l_tags:
        first_seen = get_tag_first_seen(tag, r_int=True)
        if first_seen < min_first_seen:
            min_first_seen = first_seen
    if r_int:
        return min_first_seen
    else:
        return str(min_first_seen)

def get_all_tags():
    return list(r_tags.smembers('list_tags'))

def get_all_obj_tags(obj_type):
    return list(r_tags.smembers(f'list_tags:{obj_type}'))

# # # UI # # #

def get_enabled_tags_with_synonyms_ui():
    list_tags = []
    for tag in get_all_tags():
        t = tag.split(':')[0]
        # add synonym
        str_synonyms = ' - synonyms: '
        if t == 'misp-galaxy':
            synonyms = get_tag_synonyms(tag)
            for synonym in synonyms:
                str_synonyms = str_synonyms + synonym + ', '
        # add real tag
        if str_synonyms != ' - synonyms: ':
            list_tags.append({'name': tag + str_synonyms, 'id': tag})
        else:
            list_tags.append({'name': tag, 'id': tag})
    return list_tags

# - - UI - - #

## Objects tags ##

###################################################################################
###################################################################################
###################################################################################
###################################################################################
###################################################################################


# TODO FORBID Collision CUSTOM TAG or force custom:tag

# TYPE -> taxonomy/galaxy/custom

# TODO GET OBJ Types
class Tag:

    def __int__(self, name: str, local=False):  # TODO Get first seen by object, obj='item
        self.name = name
        self.local = local

    # TODO
    def exists(self):
        pass

    def is_local(self):
        return self.local

    # TODO custom / local
    def get_type(self):
        if self.name.startswith('misp-galaxy:'):
            return 'galaxy'
        else:
            return 'taxonomy'

    def is_taxonomy(self):
        return not self.local and self.is_galaxy()

    def is_galaxy(self):
        return not self.local and self.name.startswith('misp-galaxy:')

    def get_first_seen(self, r_int=False):
        first_seen = r_tags.hget(f'meta:tag:{self.name}', 'first_seen')
        if r_int:
            if first_seen:
                first_seen = int(first_seen)
            else:
                first_seen = 99999999
        return first_seen

    def set_first_seen(self, first_seen):
        return r_tags.hget(f'meta:tag:{self.name}', 'first_seen', int(first_seen))

    def get_last_seen(self, r_int=False):
        last_seen = r_tags.hget(f'meta:tag:{self.name}', 'last_seen')  # 'last_seen:object' -> only if date or daterange
        if r_int:
            if last_seen:
                last_seen = int(last_seen)
            else:
                last_seen = 0
        return last_seen

    def set_last_seen(self, last_seen):
        return r_tags.hset(f'meta:tag:{self.name}', 'last_seen', int(last_seen))

    def get_color(self):
        color = r_tags.hget(f'meta:tag:{self.name}', 'color')
        if not color:
            return '#ffffff'

    def set_color(self, color):
        r_tags.hget(f'meta:tag:{self.name}', 'color', color)

    def is_enabled(self):
        return r_tags.sismember(f'tags:enabled', self.name)

    def get_synonyms(self):
        return r_tags.smembers(f'synonyms:tag:{self.name}')

    # color
    def get_meta(self):
        meta = {'first_seen': self.get_first_seen(),
                'last_seen': self.get_last_seen(),
                'tag': self.name,
                'local': self.is_local()}
        return meta

    def update_obj_type_first_seen(self, obj_type, first_seen, last_seen): # TODO SUBTYPE ##################################
        if int(first_seen) > int(last_seen):
            raise Exception(f'INVALID first_seen/last_seen, {first_seen}/{last_seen}')

        for date in Date.get_daterange(first_seen, last_seen):
            date = int(date)
            if date == last_seen:
                if r_tags.scard(f'{obj_type}::{self.name}:{first_seen}') > 0:
                    r_tags.hset(f'tag_metadata:{self.name}', 'first_seen', first_seen)
                else:
                    r_tags.hdel(f'tag_metadata:{self.name}', 'first_seen')  # TODO SUBTYPE
                    r_tags.hdel(f'tag_metadata:{self.name}', 'last_seen')   # TODO SUBTYPE
                    r_tags.srem(f'list_tags:{obj_type}', self.name)         # TODO SUBTYPE

            elif r_tags.scard(f'{obj_type}::{self.name}:{first_seen}') > 0:
                r_tags.hset(f'tag_metadata:{self.name}', 'first_seen', first_seen)  # TODO METADATA OBJECT NAME


    def update_obj_type_last_seen(self, obj_type, first_seen, last_seen):  # TODO SUBTYPE ##################################
        if int(first_seen) > int(last_seen):
            raise Exception(f'INVALID first_seen/last_seen, {first_seen}/{last_seen}')

        for date in Date.get_daterange(first_seen, last_seen).reverse():
            date = int(date)
            if date == last_seen:
                if r_tags.scard(f'{obj_type}::{self.name}:{last_seen}') > 0:
                    r_tags.hset(f'tag_metadata:{self.name}', 'last_seen', last_seen)
                else:
                    r_tags.hdel(f'tag_metadata:{self.name}', 'first_seen')  # TODO SUBTYPE
                    r_tags.hdel(f'tag_metadata:{self.name}', 'last_seen')   # TODO SUBTYPE
                    r_tags.srem(f'list_tags:{obj_type}', self.name)         # TODO SUBTYPE

            elif r_tags.scard(f'{obj_type}::{self.name}:{last_seen}') > 0:
                r_tags.hset(f'tag_metadata:{self.name}', 'last_seen', last_seen)  # TODO METADATA OBJECT NAME

    # TODO
    # TODO Update First seen and last seen
    # TODO SUBTYPE CHATS ??????????????
    def update_obj_type_date(self, obj_type, date, op='add', first_seen=None, last_seen=None):
        date = int(date)
        if not first_seen:
            first_seen = self.get_first_seen(r_int=True)
        if not last_seen:
            last_seen = self.get_last_seen(r_int=True)

        # Add tag
        if op == 'add':
            if date < first_seen:
                self.set_first_seen(date)
            if date > last_seen:
                self.set_last_seen(date)

        # Delete tag
        else:
            if date == first_seen and date == last_seen:

                # TODO OBJECTS ##############################################################################################
                if r_tags.scard(f'{obj_type}::{self.name}:{first_seen}') < 1:   ####################### TODO OBJ SUBTYPE ???????????????????
                    r_tags.hdel(f'tag_metadata:{self.name}', 'first_seen')
                    r_tags.hdel(f'tag_metadata:{self.name}', 'last_seen')
                    # TODO CHECK IF DELETE FULL TAG LIST ############################

            elif date == first_seen:
                if r_tags.scard(f'{obj_type}::{self.name}:{first_seen}') < 1:
                    if int(last_seen) >= int(first_seen):
                        self.update_obj_type_first_seen(obj_type, first_seen, last_seen)  # TODO OBJ_TYPE

            elif date == last_seen:
                if r_tags.scard(f'{obj_type}::{self.name}:{last_seen}') < 1:
                    if int(last_seen) >= int(first_seen):
                        self.update_obj_type_last_seen(obj_type, first_seen, last_seen)  # TODO OBJ_TYPE

            # STATS
            nb = r_tags.hincrby(f'daily_tags:{date}', self.name, -1)
            if nb < 1:
                r_tags.hdel(f'daily_tags:{date}', self.name)

    # TODO -> CHECK IF TAG EXISTS + UPDATE FIRST SEEN/LAST SEEN
    def update(self, date=None):
        pass

    # TODO CHANGE ME TO SUB FUNCTION ##### add_object_tag(tag, obj_type, obj_id, subtype='')
    def add(self, obj_type, subtype, obj_id):
        if subtype is None:
            subtype = ''

        if r_tags.sadd(f'tag:{obj_type}:{subtype}:{obj_id}', self.name) == 1:
            r_tags.sadd('list_tags', self.name)
            r_tags.sadd(f'list_tags:{obj_type}', self.name)
            if subtype:
                r_tags.sadd(f'list_tags:{obj_type}:{subtype}', self.name)

            if obj_type == 'item':
                date = item_basic.get_item_date(obj_id)

                # add domain tag
                if item_basic.is_crawled(obj_id) and self.name != 'infoleak:submission="crawler"' and self.name != 'infoleak:submission="manual"':
                    domain = item_basic.get_item_domain(obj_id)
                    self.add('domain', '', domain)
            elif obj_type == 'message':
                timestamp = obj_id.split('/')[1]
                date = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y%m%d')
            else:
                date = None

            if date:
                r_tags.sadd(f'{obj_type}:{subtype}:{self.name}:{date}', obj_id)
                update_tag_metadata(self.name, date)
            else:
                r_tags.sadd(f'{obj_type}:{subtype}:{self.name}', obj_id)

            # TODO REPLACE ME BY DATE TAGS ????
            # STATS BY TYPE ???
            # DAILY STATS
            r_tags.hincrby(f'daily_tags:{datetime.date.today().strftime("%Y%m%d")}', self.name, 1)


    # TODO CREATE FUNCTION GET OBJECT DATE
    def remove(self, obj_type, subtype, obj_id):
        # TODO CHECK IN ALL OBJECT TO DELETE
        pass

    def delete(self):
        pass


#### TAG AUTO PUSH ####

def get_auto_push_status():
    meta = {}
    for name in ['misp', 'thehive']:
        meta[name] = r_cache.hget('auto:push:status', name)
    return meta

def set_auto_push_status(name, status):
    return r_cache.hset('auto:push:status', name, status)

def get_last_auto_push_refreshed():
    last = r_cache.get('auto:push:refreshed')
    if not last:
        return -1
    else:
        return int(last)

def _set_last_auto_push_refreshed():
    return r_cache.set('auto:push:refreshed', int(time.time()))

def is_auto_push_enabled(name):
    enabled = r_tags.hget('auto:push', name)
    if enabled:
        return int(enabled) == 1
    else:
        disable_auto_push(name)
        return False

def enable_auto_push(name):
    r_tags.hset('auto:push', name, 1)

def disable_auto_push(name):
    r_tags.hset('auto:push', name, 0)

def get_auto_push_enabled_tags(name):
    return r_tags.smembers(f'auto:push:tags:{name}')

def _add_auto_push_enabled_tags(name, tag):
    return r_tags.sadd(f'auto:push:tags:{name}', tag)

def _del_auto_push_enabled_tags(name):
    return r_tags.delete(f'auto:push:tags:{name}')

def api_add_auto_push_enabled_tags(data):
    misp_tags = data.get('misp_tags', [])
    thehive_tags = data.get('thehive_tags', [])
    for tag in misp_tags:
        if not is_taxonomie_tag(tag, 'infoleak') and not is_custom_tag(tag):
            return {'error': f'Invalid Tag: {tag}'}, 400
    for tag in thehive_tags:
        if not is_taxonomie_tag(tag, 'infoleak') and not is_custom_tag(tag):
            return {'error': f'Invalid Tag: {tag}'}, 400

    _del_auto_push_enabled_tags('misp')
    for tag in misp_tags:
        _add_auto_push_enabled_tags('misp', tag)
    _del_auto_push_enabled_tags('thehive')
    for tag in thehive_tags:
        _add_auto_push_enabled_tags('thehive', tag)

def get_auto_push_tags():
    tags = get_taxonomie_enabled_tags('infoleak', r_list=True)
    tags[0:0] = list(get_all_custom_tags())
    return tags

def get_auto_push_enabled_meta():
    meta = {}
    for name in ['misp', 'thehive']:
        meta[name] = {'enabled': is_auto_push_enabled(name)}
        meta[name]['tags'] = get_auto_push_enabled_tags(name)
    return meta

def refresh_auto_push():
    meta = {}
    for name in ['misp', 'thehive']:
        if is_auto_push_enabled(name):
            meta[name] = get_auto_push_enabled_tags(name)
        _set_last_auto_push_refreshed()
    return meta

# --- TAG AUTO PUSH --- #

def get_domain_vanity_tags():
    vanity = {}
    try:
        with open(os.path.join(os.environ['AIL_HOME'], 'files/vanity_tags')) as f:
            ltags = json.load(f)
            if ltags:
                for tag in ltags:
                    if is_taxonomie_tag(tag) or is_galaxy_tag(tag):
                        for s_vanity in ltags[tag]:
                            if s_vanity not in vanity:
                                vanity[s_vanity] = []
                            vanity[s_vanity].append(tag)
    except FileNotFoundError:
        pass
    except json.decoder.JSONDecodeError:
        print('Error files/vanity_tags, Invalid JSON')
    return vanity

###################################################################################
###################################################################################
###################################################################################
###################################################################################

def add_obj_tags(object_id, object_subtype, object_type, tags=[], galaxy_tags=[]):
    for tag in tags:
        if tag:
            taxonomy = get_taxonomie_from_tag(tag)
            if is_taxonomy_tag_enabled(taxonomy, tag):
                add_object_tag(tag, object_type, object_id, object_subtype)
            else:
                return {'status': 'error', 'reason': 'Tags or Galaxy not enabled', 'value': tag}, 400

    for tag in galaxy_tags:
        if tag:
            galaxy = get_galaxy_from_tag(tag)
            if is_galaxy_tag_enabled(galaxy, tag):
                add_object_tag(tag, object_type, object_id, object_subtype)
            else:
                return {'status': 'error', 'reason': 'Tags or Galaxy not enabled', 'value': tag}, 400

# TEMPLATE + API QUERY
# WARNING CHECK IF OBJECT EXISTS
def api_add_obj_tags(tags=[], galaxy_tags=[], object_id=None, object_type="item", object_subtype=''):
    res_dict = {}
    if not object_id:
        return {'status': 'error', 'reason': 'object_id id not found'}, 404
    if not tags and not galaxy_tags:
        return {'status': 'error', 'reason': 'Tags or Galaxy not specified'}, 400
    if object_type not in ail_core.get_all_objects():
        return {'status': 'error', 'reason': 'Incorrect object_type'}, 400

    # remove empty tags
    tags = list(filter(bool, tags))
    galaxy_tags = list(filter(bool, galaxy_tags))

    res = add_obj_tags(object_id, object_subtype, object_type, tags=tags, galaxy_tags=galaxy_tags)
    if res:
        return res

    res_dict['tags'] = tags + galaxy_tags
    res_dict['id'] = object_id
    res_dict['type'] = object_type
    return res_dict, 200


# def delete_obj_tag(object_type, object_id, tag, obj_date):
#     if object_type=="item": # # TODO: # FIXME: # REVIEW: !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#         obj_date = get_obj_date(object_type, object_id)
#         r_serv_metadata.srem('tag:{}'.format(object_id), tag)
#         r_tags.srem('{}:{}'.format(tag, obj_date), object_id)
#     else:
#         r_serv_metadata.srem('tag:{}'.format(object_id), tag)
#         r_tags.srem('{}:{}'.format(object_type, tag), object_id)

def delete_tag(object_type, tag, object_id, obj_date=None): ################################ # TODO: REMOVE ME
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
def api_delete_obj_tags(tags=[], object_id=None, object_type="item", subtype=''):
    if not object_id:
        return ({'status': 'error', 'reason': 'object id not found'}, 404)
    if not tags:
        return ({'status': 'error', 'reason': 'No Tag(s) specified'}, 400)

    for tag in tags:
        res = delete_object_tag(tag, object_type, object_id, subtype=subtype)
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

def _fix_tag_obj_id(date_from):
    date_to = datetime.date.today().strftime("%Y%m%d")
    for obj_type in ail_core.get_all_objects():
        print(obj_type)
        for tag in get_all_obj_tags(obj_type):
            if ';' in tag:
                print(tag)
                new_tag = tag.split(';')[0]
                tag = tag.replace('"', '\"')
                print(new_tag)
                r_tags.hdel(f'tag_metadata:{tag}', 'first_seen')
                r_tags.hdel(f'tag_metadata:{tag}', 'last_seen')
                r_tags.srem(f'list_tags:{obj_type}', tag)
                r_tags.srem(f'list_tags:{obj_type}:', tag)
                r_tags.srem(f'list_tags', tag)
                raw = get_obj_by_tags(obj_type, [tag], nb_obj=500000, date_from=date_from, date_to=date_to)
                if raw.get('tagged_obj', []):
                    for obj_id in raw['tagged_obj']:
                        # print(obj_id)
                        delete_object_tag(tag, obj_type, obj_id)
                        add_object_tag(new_tag, obj_type, obj_id)
                else:
                    update_tag_global_by_obj_type(tag, obj_type)

# if __name__ == '__main__':
#     taxo = 'accessnow'
#     # taxo = TAXONOMIES.get(taxo)
#     res = is_taxonomy_tag_enabled(taxo, 'test')
#     print(res)
