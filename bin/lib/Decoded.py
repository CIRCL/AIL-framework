#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import magic
import sys
import redis

from io import BytesIO

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item
import Date
import Tag

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))


import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
HASH_DIR = config_loader.get_config_str('Directories', 'hash')
config_loader = None

# # TODO: move me in another file
def get_all_correlation_objects():
    '''
    Return a list of all correllated objects
    '''
    return ['domain', 'paste']

def get_decoded_item_type(sha1_string):
    '''
    Retun the estimed type of a given decoded item.

    :param sha1_string: sha1_string
    '''
    return r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'estimated_type')

def get_file_mimetype(bytes_content):
    return magic.from_buffer(bytes_content, mime=True)

def nb_decoded_seen_in_item(sha1_string):
    nb = r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'nb_seen_in_all_pastes')
    if nb is None:
        return 0
    else:
        return int(nb)

def nb_decoded_item_size(sha1_string):
    nb = r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'size')
    if nb is None:
        return 0
    else:
        return int(nb)

def get_decoded_relative_path(sha1_string, mimetype=None):
    if not mimetype:
        mimetype = get_decoded_item_type(sha1_string)
    return os.path.join(HASH_DIR, mimetype, sha1_string[0:2], sha1_string)

def get_decoded_filepath(sha1_string, mimetype=None):
    return os.path.join(os.environ['AIL_HOME'], get_decoded_relative_path(sha1_string, mimetype=mimetype))

def exist_decoded(sha1_string):
    return r_serv_metadata.exists('metadata_hash:{}'.format(sha1_string))

def get_decoded_metadata(sha1_string, nb_seen=False, size=False, file_type=False, tag=False):
    metadata_dict = {}
    metadata_dict['first_seen'] = r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'first_seen')
    metadata_dict['last_seen'] = r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'last_seen')
    if nb_seen:
        metadata_dict['nb_seen'] = nb_decoded_seen_in_item(sha1_string)
    if size:
        metadata_dict['size'] = nb_decoded_item_size(sha1_string)
    if file_type:
        metadata_dict['file_type'] = get_decoded_item_type(sha1_string)
    if tag:
        metadata_dict['tags'] = get_decoded_tag(sha1_string)
    return metadata_dict

def get_decoded_tag(sha1_string):
    return Tag.get_obj_tag(sha1_string)

def get_list_nb_previous_hash(sha1_string, num_day):
    nb_previous_hash = []
    for date_day in Date.get_previous_date_list(num_day):
        nb_previous_hash.append(get_nb_hash_seen_by_date(sha1_string, date_day))
    return nb_previous_hash

def get_nb_hash_seen_by_date(sha1_string, date_day):
    nb = r_serv_metadata.zscore('hash_date:{}'.format(date_day), sha1_string)
    if nb is None:
        return 0
    else:
        return int(nb)

def get_decoded_vt_report(sha1_string):
    vt_dict = {}
    res = r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'vt_link')
    if res:
        vt_dict["link"] = res
    res = r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'vt_report')
    if res:
        vt_dict["report"] = res
    return vt_dict


def get_decoded_items_list(sha1_string):
    return r_serv_metadata.zrange('nb_seen_hash:{}'.format(sha1_string), 0, -1)

def get_item_decoded(item_id):
    '''
    Retun all decoded item of a given item id.

    :param item_id: item id
    '''
    res = r_serv_metadata.smembers('hash_paste:{}'.format(item_id))
    if res:
        return list(res)
    else:
        return []

def get_domain_decoded_item(domain):
    '''
    Retun all decoded item of a given domain.

    :param domain: crawled domain
    '''
    res = r_serv_metadata.smembers('hash_domain:{}'.format(domain))
    if res:
        return list(res)
    else:
        return []

def get_decoded_domain_item(sha1_string):
    '''
    Retun all domain of a given decoded item.

    :param sha1_string: sha1_string
    '''
    res = r_serv_metadata.smembers('domain_hash:{}'.format(sha1_string))
    if res:
        return list(res)
    else:
        return []

def get_decoded_correlated_object(sha1_string, correlation_objects=[]):
    '''
    Retun all correlation of a given sha1.

    :param sha1_string: sha1
    :type sha1_string: str

    :return: a dict of all correlation for a given sha1
    :rtype: dict
    '''
    if correlation_objects is None:
        correlation_objects = get_all_correlation_objects()
    decoded_correlation = {}
    for correlation_object in correlation_objects:
        if correlation_object == 'paste':
            res = get_decoded_items_list(sha1_string)
        elif correlation_object == 'domain':
            res = get_decoded_domain_item(sha1_string)
        else:
            res = None
        if res:
            decoded_correlation[correlation_object] = res
    return decoded_correlation

def save_domain_decoded(domain, sha1_string):
    r_serv_metadata.sadd('hash_domain:{}'.format(domain), sha1_string) # domain - hash map
    r_serv_metadata.sadd('domain_hash:{}'.format(sha1_string), domain) # hash - domain ma


def get_decoded_file_content(sha1_string, mimetype=None):
    filepath = get_decoded_filepath(sha1_string, mimetype=mimetype)
    with open(filepath, 'rb') as f:
        file_content = BytesIO(f.read())
    return file_content

# # TODO: check file format
def save_decoded_file_content(sha1_string, io_content, date_range, mimetype=None):
    if not mimetype:
        if exist_decoded(sha1_string):
            mimetype = get_decoded_item_type(sha1_string)
        else:
            mimetype = get_file_mimetype(io_content.getvalue())

    

    filepath = get_decoded_filepath(sha1_string, mimetype=mimetype)
    if os.path.isfile(filepath):
        print('File already exist')
        return False

    # create dir
    dirname = os.path.dirname(filepath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(filepath, 'wb') as f:
        f.write(io_content.getvalue())

    # create hash metadata
    r_serv_metadata.hset('metadata_hash:{}'.format(sha1_string), 'size', os.path.getsize(filepath))

    r_serv_metadata.hset('metadata_hash:{}'.format(sha1_string), 'first_seen', date_range['date_from'])
    r_serv_metadata.hset('metadata_hash:{}'.format(sha1_string), 'last_seen', date_range['date_to'])

    return True

def delete_decoded_file(obj_id, io_content):
    # check if item exists
    if not exist_decoded(obj_id):
        return False
    else:
        Tag.delete_obj_tags(obj_id, 'decoded', Tag.get_obj_tag(obj_id))
        os.remove(get_decoded_filepath(sha1_string))
        r_serv_metadata.delete('metadata_hash:{}'.format(obj_id))
        return True

def create_decoded(obj_id, obj_meta, io_content):
    first_seen = obj_meta.get('first_seen', None)
    last_seen = obj_meta.get('last_seen', None)
    date_range = Date.sanitise_date_range(first_seen, last_seen, separator='', date_type='datetime')

    res = save_decoded_file_content(obj_id, io_content, date_range, mimetype=None)
    if res and 'tags' in obj_meta:
        Tag.api_add_obj_tags(tags=obj_metadata['tags'], object_id=obj_id, object_type="decoded")
