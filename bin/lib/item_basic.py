#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import gzip

import magic

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Tag

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
# get and sanityze PASTE DIRECTORY
PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'
PASTES_FOLDER = os.path.join(os.path.realpath(PASTES_FOLDER), '')

r_cache = config_loader.get_redis_conn("Redis_Cache")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

def exist_item(item_id):
    filename = get_item_filepath(item_id)
    if os.path.isfile(filename):
        return True
    else:
        return False

def get_item_filepath(item_id):
    filename = os.path.join(PASTES_FOLDER, item_id)
    return os.path.realpath(filename)

def get_item_date(item_id, add_separator=False):
    l_directory = item_id.split('/')
    if add_separator:
        return '{}/{}/{}'.format(l_directory[-4], l_directory[-3], l_directory[-2])
    else:
        return '{}{}{}'.format(l_directory[-4], l_directory[-3], l_directory[-2])

def get_basename(item_id):
    return os.path.basename(item_id)

def get_source(item_id):
    l_source = item_id.split('/')[:-4]
    return os.path.join(*l_source)

# # TODO: add an option to check the tag
def is_crawled(item_id):
    return item_id.startswith('crawled')

def get_item_domain(item_id):
    return item_id[19:-36]

def get_item_content_binary(item_id):
    item_full_path = os.path.join(PASTES_FOLDER, item_id)
    try:
        with gzip.open(item_full_path, 'rb') as f:
            item_content = f.read()
    except Exception as e:
        print(e)
        item_content = ''
    return item_content

def get_item_content(item_id):
    item_full_path = os.path.join(PASTES_FOLDER, item_id)
    try:
        item_content = r_cache.get(item_full_path)
    except UnicodeDecodeError:
        item_content = None
    except Exception as e:
        item_content = None
    if item_content is None:
        try:
            with gzip.open(item_full_path, 'r') as f:
                item_content = f.read().decode()
                r_cache.set(item_full_path, item_content)
                r_cache.expire(item_full_path, 300)
        except Exception as e:
            print(e)
            item_content = ''
    return str(item_content)

def get_item_mimetype(item_id):
    return magic.from_buffer(get_item_content(item_id), mime=True)

#### TREE CHILD/FATHER ####
def is_father(item_id):
    return r_serv_metadata.exists('paste_children:{}'.format(item_id))

def is_children(item_id):
    return r_serv_metadata.hexists('paste_metadata:{}'.format(item_id), 'father')

def is_root_node(item_id):
    if is_father(item_id) and not is_children(item_id):
        return True
    else:
        return False

def is_node(item_id):
    if is_father(item_id) or is_children(item_id):
        return True
    else:
        return False

def is_leaf(item_id):
    if not is_father(item_id) and is_children(item_id):
        return True
    else:
        return False

def is_domain_root(item_id):
    if not is_crawled(item_id):
        return False
    else:
        domain = get_item_domain(item_id)
        item_father = get_item_parent(item_id)
        if not is_crawled(item_father):
            return True
        else:
            # same domain
            if get_item_domain(item_father) == domain:
                return False
            else:
                return True

def get_item_url(item_id):
    return r_serv_metadata.hget(f'paste_metadata:{item_id}', 'real_link')

def get_nb_children(item_id):
    return r_serv_metadata.scard('paste_children:{}'.format(item_id))


def get_item_parent(item_id):
    return r_serv_metadata.hget('paste_metadata:{}'.format(item_id), 'father')

def get_item_children(item_id):
    return list(r_serv_metadata.smembers('paste_children:{}'.format(item_id)))

# # TODO:  handle domain last origin in domain lib
def _delete_node(item_id):
    # only if item isn't deleted
    #if is_crawled(item_id):
    #    r_serv_metadata.hrem('paste_metadata:{}'.format(item_id), 'real_link')
    for children_id in get_item_children(item_id):
        r_serv_metadata.hdel('paste_metadata:{}'.format(children_id), 'father')
    r_serv_metadata.delete('paste_children:{}'.format(item_id))

    # delete regular
        # simple if leaf

    # delete item node

def get_all_domain_node_by_item_id(item_id, l_nodes=[]):
    domain = get_item_domain(item_id)
    for child_id in get_item_children(item_id):
        if get_item_domain(child_id) == domain:
            l_nodes.append(child_id)
            l_nodes = get_all_domain_node_by_item_id(child_id, l_nodes)
    return l_nodes

##--  --##


def add_item_parent_by_parent_id(parent_type, parent_id, item_id):
    parent_item_id = get_obj_id_item_id(parent_type, parent_id)
    if parent_item_id:
        add_item_parent(parent_item_id, item_id)

def add_item_parent(parent_item_id, item_id):
    r_serv_metadata.hset('paste_metadata:{}'.format(item_id), 'father', parent_item_id)
    r_serv_metadata.sadd('paste_children:{}'.format(parent_item_id), item_id)
    return True

# TODO:
# FIXME:
#### UNKNOW SECTION ####

def get_obj_id_item_id(parent_type, parent_id):
    all_parents_type = ['twitter_id', 'jabber_id', 'telegram_id']
    if parent_type in all_parents_type:
        return r_serv_metadata.hget('map:{}:item_id'.format(parent_type), parent_id)
    else:
        return None

def add_map_obj_id_item_id(obj_id, item_id, obj_type):
    if obj_type == 'twitter_id':
        r_serv_metadata.hset('map:twitter_id:item_id', obj_id, item_id)
    if obj_type == 'jabber_id':
        r_serv_metadata.hset('map:jabber_id:item_id', obj_id, item_id)
    if obj_type == 'telegram_id':
        r_serv_metadata.hset('map:telegram_id:item_id', obj_id, item_id)

# delete twitter id

##--  --##

## COMMON ##
def _get_dir_source_name(directory, source_name=None, l_sources_name=set(), filter_dir=False):
    if not l_sources_name:
        l_sources_name = set()
    if source_name:
        l_dir = os.listdir(os.path.join(directory, source_name))
    else:
        l_dir = os.listdir(directory)
    # empty directory
    if not l_dir:
        return l_sources_name.add(source_name)
    else:
        for src_name in l_dir:
            if len(src_name) == 4:
                #try:
                int(src_name)
                to_add = os.path.join(source_name)
                # filter sources, remove first directory
                if filter_dir:
                    to_add = to_add.replace('archive/', '').replace('alerts/', '')
                l_sources_name.add(to_add)
                return l_sources_name
                #except:
                #    pass
            if source_name:
                src_name = os.path.join(source_name, src_name)
            l_sources_name = _get_dir_source_name(directory, source_name=src_name, l_sources_name=l_sources_name, filter_dir=filter_dir)
    return l_sources_name


def get_all_items_sources(filter_dir=False, r_list=False):
    res = _get_dir_source_name(PASTES_FOLDER, filter_dir=filter_dir)
    if res:
        if r_list:
            res = list(res)
        return res
    else:
        return []

def verify_sources_list(sources):
    all_sources = get_all_items_sources()
    for source in sources:
        if source not in all_sources:
            return {'status': 'error', 'reason': 'Invalid source', 'value': source}, 400
    return None

def get_all_items_metadata_dict(list_id):
    list_meta = []
    for item_id in list_id:
        list_meta.append( {'id': item_id, 'date': get_item_date(item_id), 'tags': Tag.get_obj_tag(item_id)} )
    return list_meta

##--  --##


if __name__ == '__main__':
    get_all_items_sources()
