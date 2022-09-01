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

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import Tag

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

def get_all_decoder():
    return ['base64', 'binary', 'hexadecimal']

# TODO: # REVIEW: default => base64
def sanitize_decoder_name(decoder_name):
    if decoder_name in get_all_decoder():
        return decoder_name
    else:
        return 'base64'

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

def get_decoded_first_seen(sha1_string, r_int=False):
    res = r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'first_seen')
    if res:
        res = res.replace('/', '')
    if r_int:
        if res:
            return int(res)
        else:
            return 99999999
    return res

def get_decoded_last_seen(sha1_string, r_int=False):
    res = r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'last_seen')
    if res:
        res = res.replace('/', '')
    if r_int:
        if res:
            return int(res)
        else:
            return 0
    return res

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
    return Tag.get_object_tags('decoded', sha1_string)

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
    if not correlation_objects:
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

# # TODO: add delete
#         delete stats
def create_decoder_matadata(sha1_string, item_id, decoder_type):
    estimated_type = get_decoded_item_type(sha1_string)
    if not estimated_type:
        print('error, unknow sha1_string')
    decoder_type = sanitize_decoder_name(decoder_type)
    item_date = Item.get_item_date(item_id)

    r_serv_metadata.incrby('{}_decoded:{}'.format(decoder_type, item_date), 1)
    r_serv_metadata.zincrby('{}_date:{}'.format(decoder_type, item_date), sha1_string, 1)

    # first time we see this hash encoding on this item
    if r_serv_metadata.zscore('{}_hash:{}'.format(decoder_type, sha1_string), item_id) is None:

        # create hash metadata
        r_serv_metadata.sadd('hash_{}_all_type'.format(decoder_type), estimated_type)

        # first time we see this hash encoding today
        if r_serv_metadata.zscore('{}_date:{}'.format(decoder_type, item_date), sha1_string) is None:
            r_serv_metadata.zincrby('{}_type:{}'.format(decoder_type, estimated_type), item_date, 1) # # TODO: # DUP1

    r_serv_metadata.hincrby('metadata_hash:{}'.format(sha1_string), '{}_decoder'.format(decoder_type), 1)
    r_serv_metadata.zincrby('{}_type:{}'.format(decoder_type, estimated_type), item_date, 1) # # TODO: # DUP1

    r_serv_metadata.zincrby('{}_hash:{}'.format(decoder_type, sha1_string), item_id, 1) # number of b64 on this paste

# # # TODO: check if item and decoded exist
def save_item_relationship(sha1_string, item_id):
    estimated_type = get_decoded_item_type(sha1_string)
    if not estimated_type:
        print('error, unknow sha1_string')

    item_date = Item.get_item_date(item_id)

    r_serv_metadata.zincrby('hash_date:{}'.format(item_date), sha1_string, 1)

    update_decoded_daterange(sha1_string, item_date)

    # first time we see this hash (all encoding) on this item
    if r_serv_metadata.zscore('nb_seen_hash:{}'.format(sha1_string), item_id) is None:
        r_serv_metadata.hincrby('metadata_hash:{}'.format(sha1_string), 'nb_seen_in_all_pastes', 1) #### MOVE IT ????

    # # FIXME:
    r_serv_metadata.zincrby('nb_seen_hash:{}'.format(sha1_string), item_id, 1)# hash - paste map
    r_serv_metadata.sadd('hash_paste:{}'.format(item_id), sha1_string) # item - hash map

    # domain
    if Item.is_crawled(item_id):
        domain = Item.get_item_domain(item_id)
        save_domain_relationship(domain, sha1_string)

def delete_item_relationship(sha1_string, item_id):
    item_date = Item.get_item_date(item_id)

    #update_decoded_daterange(sha1_string, item_date) 3 # TODO:
    r_serv_metadata.srem('hash_paste:{}'.format(item_id), sha1_string) # item - hash map

    res = r_serv_metadata.zincrby('hash_date:{}'.format(item_date), sha1_string, -1)
    if int(res) < 1:
        r_serv_metadata.zrem('hash_date:{}'.format(item_date), sha1_string)

    res = r_serv_metadata.hget('metadata_hash:{}'.format(sha1_string), 'nb_seen_in_all_pastes')
    if int(res) > 0:
        r_serv_metadata.hincrby('metadata_hash:{}'.format(sha1_string), 'nb_seen_in_all_pastes', -1)

    res = r_serv_metadata.zincrby('nb_seen_hash:{}'.format(sha1_string), item_id, 1)# hash - paste map
    if int(res) < 1:
         r_serv_metadata.zrem('nb_seen_hash:{}'.format(sha1_string), item_id)

def save_domain_relationship(domain, sha1_string):
    r_serv_metadata.sadd('hash_domain:{}'.format(domain), sha1_string) # domain - hash map
    r_serv_metadata.sadd('domain_hash:{}'.format(sha1_string), domain) # hash - domain map

def delete_domain_relationship(domain, sha1_string):
    r_serv_metadata.srem('hash_domain:{}'.format(domain), sha1_string) # domain - hash map
    r_serv_metadata.srem('domain_hash:{}'.format(sha1_string), domain) # hash - domain map

def update_decoded_daterange(obj_id, new_date):
    new_date = int(new_date)
    new_date_str = str(new_date)
    new_date_str = '{}/{}/{}'.format(new_date_str[0:4], new_date_str[4:6], new_date_str[6:8])
    # obj_id don't exit
    if not r_serv_metadata.hexists('metadata_hash:{}'.format(obj_id), 'first_seen'):
        r_serv_metadata.hset('metadata_hash:{}'.format(obj_id), 'first_seen', new_date_str)
        r_serv_metadata.hset('metadata_hash:{}'.format(obj_id), 'last_seen', new_date_str)
    else:
        first_seen = get_decoded_first_seen(obj_id, r_int=True)
        last_seen = get_decoded_last_seen(obj_id, r_int=True)
        if new_date < first_seen:
            r_serv_metadata.hset('metadata_hash:{}'.format(obj_id), 'first_seen', new_date_str)
        if new_date > last_seen:
            r_serv_metadata.hset('metadata_hash:{}'.format(obj_id), 'last_seen', new_date_str)

def save_obj_relationship(obj_id, referenced_obj_type, referenced_obj_id):
    if referenced_obj_type == 'domain':
        save_domain_relationship(referenced_obj_id, obj_id)
    elif referenced_obj_type == 'item':
        save_item_relationship(obj_id, referenced_obj_id)

def delete_obj_relationship(obj_id, referenced_obj_type, referenced_obj_id):
    if referenced_obj_type == 'domain':
        delete_domain_relationship(referenced_obj_id, obj_id)
    elif referenced_obj_type == 'item':
        delete_item_relationship(obj_id, referenced_obj_id)

def get_decoded_file_content(sha1_string, mimetype=None):
    filepath = get_decoded_filepath(sha1_string, mimetype=mimetype)
    with open(filepath, 'rb') as f:
        file_content = BytesIO(f.read())
    return file_content

# # TODO: check file format
def save_decoded_file_content(sha1_string, file_content, date_from, date_to=None, mimetype=None):
    if not mimetype:
        if exist_decoded(sha1_string):
            mimetype = get_decoded_item_type(sha1_string)
        else:
            mimetype = get_file_mimetype(file_content)

    filepath = get_decoded_filepath(sha1_string, mimetype=mimetype)
    if os.path.isfile(filepath):
        #print('File already exist')
        return False

    # create dir
    dirname = os.path.dirname(filepath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(filepath, 'wb') as f:
        f.write(file_content)

    # create hash metadata
    r_serv_metadata.hset('metadata_hash:{}'.format(sha1_string), 'size', os.path.getsize(filepath))
    r_serv_metadata.hset('metadata_hash:{}'.format(sha1_string), 'estimated_type', mimetype)
    r_serv_metadata.sadd('hash_all_type', mimetype)

    update_decoded_daterange(sha1_string, date_from)
    if date_from != date_to and date_to:
        update_decoded_daterange(sha1_string, date_to)

    return True

def delete_decoded_file(obj_id):
    filepath = get_decoded_filepath(obj_id)
    if not os.path.isfile(filepath):
        return False

    Tag.delete_obj_tags(obj_id, 'decoded', Tag.get_obj_tag(obj_id)) #############
    os.remove(filepath)
    return True

def create_decoded(obj_id, obj_meta, io_content):
    first_seen = obj_meta.get('first_seen', None)
    last_seen = obj_meta.get('last_seen', None)
    date_range = Date.sanitise_date_range(first_seen, last_seen, separator='', date_type='datetime')
    decoded_file_content = io_content.getvalue()

    res = save_decoded_file_content(obj_id, decoded_file_content, date_range['date_from'], date_to=date_range['date_to'], mimetype=None)
    if res and 'tags' in obj_meta:
        Tag.api_add_obj_tags(tags=obj_meta['tags'], object_id=obj_id, object_type="decoded")

def delete_decoded(obj_id):
    if not exist_decoded(obj_id):
        return False

    res = delete_decoded_file(obj_id)
    if not res:
        return False

    obj_correlations = get_decoded_correlated_object(obj_id)
    if 'domain' in obj_correlations:
        for domain in obj_correlations['domain']:
            r_serv_metadata.srem('hash_domain:{}'.format(domain), obj_id)
        r_serv_metadata.delete('domain_hash:{}'.format(obj_id), domain)

    if 'paste' in obj_correlations: # TODO: handle item
        for item_id in obj_correlations['paste']:
            item_date = Item.get_item_date(item_id)

            r_serv_metadata.zrem('hash_date:{}'.format(item_date), obj_id)
            r_serv_metadata.srem('hash_paste:{}'.format(item_id), obj_id)
            for decoder_name in get_all_decoder():

                r_serv_metadata.incrby('{}_decoded:{}'.format(decoder_name, item_date), -1)
                r_serv_metadata.zrem('{}_date:{}'.format(decoder_name, item_date), obj_id)

        for decoder_name in get_all_decoder():
            r_serv_metadata.delete('{}_hash:{}'.format(decoder_name, obj_id))

        r_serv_metadata.delete('nb_seen_hash:{}'.format(obj_id))


    ####### # TODO: DUP1
    #r_serv_metadata.zincrby('{}_type:{}'.format(decoder_type, estimated_type), item_date, 1)
    #######

    ###
    #r_serv_metadata.sadd('hash_{}_all_type'.format(decoder_type), estimated_type)
    #r_serv_metadata.sadd('hash_all_type', estimated_type)
    ###

    r_serv_metadata.delete('metadata_hash:{}'.format(obj_id))
