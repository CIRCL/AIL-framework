#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
# get and sanityze PASTE DIRECTORY
PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'
PASTES_FOLDER = os.path.join(os.path.realpath(PASTES_FOLDER), '')

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

def get_source(item_id):
    return item_id.split('/')[-5]

# # TODO: add an option to check the tag
def is_crawled(item_id):
    return item_id.startswith('crawled')

def get_item_domain(item_id):
    return item_id[19:-36]

def add_item_parent_by_parent_id(parent_type, parent_id, item_id):
    parent_item_id = get_obj_id_item_id(parent_type, parent_id)
    if parent_item_id:
        add_item_parent(parent_item_id, item_id)

def add_item_parent(parent_item_id, item_id):
    r_serv_metadata.hset('paste_metadata:{}'.format(item_id), 'father', parent_item_id)
    r_serv_metadata.sadd('paste_children:{}'.format(parent_item_id), item_id)
    return True

def add_map_obj_id_item_id(obj_id, item_id, obj_type):
    if obj_type == 'twitter_id':
        r_serv_metadata.hset('map:twitter_id:item_id', obj_id, item_id)

def get_obj_id_item_id(parent_type, parent_id):
    all_parents_type = ['twitter_id']
    if parent_type in all_parents_type:
        return r_serv_metadata.hget('map:twitter_id:item_id', parent_id)
    else:
        return None
