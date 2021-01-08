#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import base64
import os
import sys
import redis

from hashlib import sha256
from io import BytesIO

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item
import Date
import Tag

import Correlate_object
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
SCREENSHOT_FOLDER = config_loader.get_files_directory('screenshot')
config_loader = None

# get screenshot relative path
def get_screenshot_rel_path(sha256_string, add_extension=False):
    screenshot_path =  os.path.join(sha256_string[0:2], sha256_string[2:4], sha256_string[4:6], sha256_string[6:8], sha256_string[8:10], sha256_string[10:12], sha256_string[12:])
    if add_extension:
        screenshot_path = screenshot_path + '.png'
    return screenshot_path

def get_screenshot_filepath(sha256_string):
    filename = os.path.join(SCREENSHOT_FOLDER, get_screenshot_rel_path(sha256_string, add_extension=True))
    return os.path.realpath(filename)

def exist_screenshot(sha256_string):
    screenshot_path = get_screenshot_filepath(sha256_string)
    return os.path.isfile(screenshot_path)

def get_metadata(sha256_string):
    metadata_dict = {}
    metadata_dict['img'] = get_screenshot_rel_path(sha256_string)
    metadata_dict['tags'] = get_screenshot_tags(sha256_string)
    metadata_dict['is_tags_safe'] = Tag.is_tags_safe(metadata_dict['tags'])
    return metadata_dict

def get_screenshot_tags(sha256_string):
    return Tag.get_obj_tag(sha256_string)

def get_screenshot_items_list(sha256_string):
    res = r_serv_onion.smembers('screenshot:{}'.format(sha256_string))
    if res:
        return list(res)
    else:
        return []

def get_item_screenshot(item_id):
    return r_serv_metadata.hget('paste_metadata:{}'.format(item_id), 'screenshot')

def get_item_screenshot_list(item_id):
    '''
    Retun all decoded item of a given item id.

    :param item_id: item id
    '''
    screenshot = get_item_screenshot(item_id)
    if screenshot:
        return [screenshot]
    else:
        return []

def get_domain_screenshot(domain):
    '''
    Retun all screenshot of a given domain.

    :param domain: crawled domain
    '''
    res = r_serv_onion.smembers('domain_screenshot:{}'.format(domain))
    if res:
        return list(res)
    else:
        return []

def get_randon_domain_screenshot(domain, r_path=True):
    '''
    Retun all screenshot of a given domain.

    :param domain: crawled domain
    '''
    res = r_serv_onion.srandmember('domain_screenshot:{}'.format(domain))
    if res and r_path:
        return get_screenshot_rel_path(res)
    return res

def get_screenshot_domain(sha256_string):
    '''
    Retun all domain of a given screenshot.

    :param sha256_string: sha256_string
    '''
    res = r_serv_onion.smembers('screenshot_domain:{}'.format(sha256_string))
    if res:
        return list(res)
    else:
        return []

def get_screenshot_correlated_object(sha256_string, correlation_objects=[]):
    '''
    Retun all correlation of a given sha256.

    :param sha1_string: sha256
    :type sha1_string: str

    :return: a dict of all correlation for a given sha256
    :rtype: dict
    '''
    if not correlation_objects:
        correlation_objects = Correlate_object.get_all_correlation_objects()
    decoded_correlation = {}
    for correlation_object in correlation_objects:
        if correlation_object == 'paste':
            res = get_screenshot_items_list(sha256_string)
        elif correlation_object == 'domain':
            res = get_screenshot_domain(sha256_string)
        else:
            res = None
        if res:
            decoded_correlation[correlation_object] = res
    return decoded_correlation

def save_item_relationship(obj_id, item_id):
    r_serv_metadata.hset('paste_metadata:{}'.format(item_id), 'screenshot', obj_id)
    r_serv_onion.sadd('screenshot:{}'.format(obj_id), item_id)
    if Item.is_crawled(item_id):
        domain = Item.get_item_domain(item_id)
        save_domain_relationship(obj_id, domain)

def delete_item_relationship(obj_id, item_id):
    r_serv_metadata.hdel('paste_metadata:{}'.format(item_id), 'screenshot', obj_id)
    r_serv_onion.srem('screenshot:{}'.format(obj_id), item_id)

def save_domain_relationship(obj_id, domain):
    r_serv_onion.sadd('domain_screenshot:{}'.format(domain), obj_id)
    r_serv_onion.sadd('screenshot_domain:{}'.format(obj_id), domain)

def delete_domain_relationship(obj_id, domain):
    r_serv_onion.srem('domain_screenshot:{}'.format(domain), obj_id)
    r_serv_onion.sadd('screenshot_domain:{}'.format(obj_id), domain)

def save_obj_relationship(obj_id, obj2_type, obj2_id):
    if obj2_type == 'domain':
        save_domain_relationship(obj_id, obj2_id)
    elif obj2_type == 'item':
        save_item_relationship(obj_id, obj2_id)

def delete_obj_relationship(obj_id, obj2_type, obj2_id):
    if obj2_type == 'domain':
        delete_domain_relationship(obj_id, obj2_id)
    elif obj2_type == 'item':
        delete_item_relationship(obj_id, obj2_id)

def get_screenshot_file_content(sha256_string):
    filepath = get_screenshot_filepath(sha256_string)
    with open(filepath, 'rb') as f:
        file_content = BytesIO(f.read())
    return file_content

# if force save, ignore max_size
def save_crawled_screeshot(b64_screenshot, max_size, f_save=False):
    screenshot_size = (len(b64_screenshot)*3) /4
    if screenshot_size < max_size or f_save:
        image_content = base64.standard_b64decode(b64_screenshot.encode())
        sha256_string = sha256(image_content).hexdigest()
        filepath = get_screenshot_filepath(sha256_string)
        if os.path.isfile(filepath):
            #print('File already exist')
            return sha256_string
        # create dir
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filepath, 'wb') as f:
            f.write(image_content)
        return sha256_string
    return False

def save_screenshot_file(sha256_string, io_content):
    filepath = get_screenshot_filepath(sha256_string)
    if os.path.isfile(filepath):
        #print('File already exist')
        return False
    # create dir
    dirname = os.path.dirname(filepath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    # # TODO: check if is IO file
    with open(filepath, 'wb') as f:
        f.write(io_content.getvalue())
    return True

def delete_screenshot_file(obj_id):
    filepath = get_screenshot_filepath(obj_id)
    if not os.path.isfile(filepath):
        return False
    Tag.delete_obj_tags(obj_id, 'image', Tag.get_obj_tag(obj_id))
    os.remove(filepath)
    return True

def create_screenshot(obj_id, obj_meta, io_content):
    # # TODO: check if sha256
    res = save_screenshot_file(obj_id, io_content)
    if res:
        # creata tags
        if 'tags' in obj_meta:
            # # TODO: handle mixed tags: taxonomies and Galaxies
            Tag.api_add_obj_tags(tags=obj_meta['tags'], object_id=obj_id, object_type="image")
        return True

    return False

def delete_screenshot(obj_id):
    if not exist_screenshot(obj_id):
        return False

    res = delete_screenshot_file(obj_id)
    if not res:
        return False

    obj_correlations = get_screenshot_correlated_object(obj_id)
    if 'domain' in obj_correlations:
        for domain in obj_correlations['domain']:
            r_serv_onion.srem('domain_screenshot:{}'.format(domain), obj_id)
        r_serv_onion.delete('screenshot_domain:{}'.format(obj_id))

    if 'paste' in obj_correlations: # TODO: handle item
        for item_id in obj_correlations['paste']:
            r_serv_metadata.hdel('paste_metadata:{}'.format(item_id), 'screenshot')
        r_serv_onion.delete('screenshot:{}'.format(obj_id), item_id)

    return True
