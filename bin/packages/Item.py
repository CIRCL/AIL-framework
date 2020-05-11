#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import gzip
import redis

from io import BytesIO

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Date
import Tag
import Cryptocurrency
import Pgp

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import item_basic
import ConfigLoader
import Correlate_object
import Decoded
import Screenshot
import telegram

config_loader = ConfigLoader.ConfigLoader()
# get and sanityze PASTE DIRECTORY
PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'
PASTES_FOLDER = os.path.join(os.path.realpath(PASTES_FOLDER), '')

r_cache = config_loader.get_redis_conn("Redis_Cache")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
screenshot_directory = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "crawled_screenshot"))
config_loader = None

def exist_item(item_id):
    return item_basic.exist_item(item_id)

def get_basename(item_id):
    return os.path.basename(item_id)

def get_item_id(full_path):
    return full_path.replace(PASTES_FOLDER, '', 1)

def get_item_filepath(item_id):
    return item_basic.get_item_filepath(item_id)

def get_item_date(item_id, add_separator=False):
    l_directory = item_id.split('/')
    if add_separator:
        return '{}/{}/{}'.format(l_directory[-4], l_directory[-3], l_directory[-2])
    else:
        return '{}{}{}'.format(l_directory[-4], l_directory[-3], l_directory[-2])

def get_source(item_id):
    return item_id.split('/')[-5]

def get_item_basename(item_id):
    return os.path.basename(item_id)

def get_item_size(item_id):
    return round(os.path.getsize(os.path.join(PASTES_FOLDER, item_id))/1024.0, 2)

def get_lines_info(item_id, item_content=None):
    if not item_content:
        item_content = get_item_content(item_id)
    max_length = 0
    line_id = 0
    nb_line = 0
    for line in item_content.splitlines():
        length = len(line)
        if length > max_length:
            max_length = length
        nb_line += 1
    return {'nb': nb_line, 'max_length': max_length}


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
        except:
            item_content = ''
    return str(item_content)

# API
def get_item(request_dict):
    if not request_dict:
        return Response({'status': 'error', 'reason': 'Malformed JSON'}, 400)

    item_id = request_dict.get('id', None)
    if not item_id:
        return ( {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400 )
    if not exist_item(item_id):
        return ( {'status': 'error', 'reason': 'Item not found'}, 404 )

    dict_item = {}
    dict_item['id'] = item_id
    date = request_dict.get('date', True)
    if date:
        add_separator = False
        if request_dict.get('date_separator', False):
            add_separator = True
        dict_item['date'] = get_item_date(item_id, add_separator=add_separator)
    tags = request_dict.get('tags', True)
    if tags:
        dict_item['tags'] = Tag.get_obj_tag(item_id)

    size = request_dict.get('size', False)
    if size:
        dict_item['size'] = get_item_size(item_id)

    content = request_dict.get('content', False)
    if content:
        # UTF-8 outpout, # TODO: use base64
        dict_item['content'] = get_item_content(item_id)

    raw_content = request_dict.get('raw_content', False)
    if raw_content:
        dict_item['raw_content'] = get_raw_content(item_id)

    lines_info = request_dict.get('lines', False)
    if lines_info:
        dict_item['lines'] = get_lines_info(item_id, dict_item.get('content', 'None'))

    if request_dict.get('pgp'):
        dict_item['pgp'] = {}
        if request_dict['pgp'].get('key'):
            dict_item['pgp']['key'] = get_item_pgp_key(item_id)
        if request_dict['pgp'].get('mail'):
            dict_item['pgp']['mail'] = get_item_pgp_mail(item_id)
        if request_dict['pgp'].get('name'):
            dict_item['pgp']['name'] = get_item_pgp_name(item_id)

    if request_dict.get('cryptocurrency'):
        dict_item['cryptocurrency'] = {}
        if request_dict['cryptocurrency'].get('bitcoin'):
            dict_item['cryptocurrency']['bitcoin'] = get_item_bitcoin(item_id)

    return (dict_item, 200)


###
### correlation
###
def get_item_cryptocurrency(item_id, currencies_type=None, get_nb=False):
    '''
    Return all cryptocurrencies of a given item.

    :param item_id: item id
    :param currencies_type: list of cryptocurrencies type
    :type currencies_type: list, optional
    '''
    return Cryptocurrency.cryptocurrency.get_item_correlation_dict(item_id, correlation_type=currencies_type, get_nb=get_nb)

def get_item_pgp(item_id, currencies_type=None, get_nb=False):
    '''
    Return all pgp of a given item.

    :param item_id: item id
    :param currencies_type: list of cryptocurrencies type
    :type currencies_type: list, optional
    '''
    return Pgp.pgp.get_item_correlation_dict(item_id, correlation_type=currencies_type, get_nb=get_nb)

def get_item_username(item_id, currencies_type=None, get_nb=False):
    '''
    Return all pgp of a given item.

    :param item_id: item id
    :param currencies_type: list of cryptocurrencies type
    :type currencies_type: list, optional
    '''
    return telegram.correlation.get_item_correlation_dict(item_id, correlation_type=currencies_type, get_nb=get_nb)

def get_item_decoded(item_id):
    '''
    Return all pgp of a given item.

    :param item_id: item id
    :param currencies_type: list of cryptocurrencies type
    :type currencies_type: list, optional
    '''
    return Decoded.get_item_decoded(item_id)

def get_item_all_screenshot(item_id):
    '''
    Return all screenshot of a given item.

    :param item_id: item id
    '''
    return Screenshot.get_item_screenshot_list(item_id)

def get_item_all_correlation(item_id, correlation_names=[], get_nb=False):
    '''
    Retun all correlation of a given item id.

    :param item_id: item id
    :type domain: str

    :return: a dict of all correlation for a item id
    :rtype: dict
    '''
    if not correlation_names:
        correlation_names = Correlate_object.get_all_correlation_names()
    item_correl = {}
    for correlation_name in correlation_names:
        if correlation_name=='cryptocurrency':
            res = get_item_cryptocurrency(item_id, get_nb=get_nb)
        elif correlation_name=='pgp':
            res = get_item_pgp(item_id, get_nb=get_nb)
        elif correlation_name=='username':
            res = get_item_username(item_id, get_nb=get_nb)
        elif correlation_name=='decoded':
            res = get_item_decoded(item_id)
        elif correlation_name=='screenshot':
            res = get_item_all_screenshot(item_id)
        else:
            res = None
        # add correllation to dict
        if res:
            item_correl[correlation_name] = res
    return item_correl



## TODO: REFRACTOR
def _get_item_correlation(correlation_name, correlation_type, item_id):
    res = r_serv_metadata.smembers('item_{}_{}:{}'.format(correlation_name, correlation_type, item_id))
    if res:
        return list(res)
    else:
        return []

## TODO: REFRACTOR
def get_item_bitcoin(item_id):
    return _get_item_correlation('cryptocurrency', 'bitcoin', item_id)

## TODO: REFRACTOR
def get_item_pgp_key(item_id):
    return _get_item_correlation('pgpdump', 'key', item_id)

## TODO: REFRACTOR
def get_item_pgp_name(item_id):
    return _get_item_correlation('pgpdump', 'name', item_id)

## TODO: REFRACTOR
def get_item_pgp_mail(item_id):
    return _get_item_correlation('pgpdump', 'mail', item_id)

## TODO: REFRACTOR
def get_item_pgp_correlation(item_id):
    pass

###
### GET Internal Module DESC
###
def get_item_list_desc(list_item_id):
    desc_list = []
    for item_id in list_item_id:
        desc_list.append( {'id': item_id, 'date': get_item_date(item_id), 'tags': Tag.get_obj_tag(item_id)} )
    return desc_list

# # TODO: add an option to check the tag
def is_crawled(item_id):
    return item_id.startswith('crawled')

def is_onion(item_id):
    is_onion = False
    if len(is_onion) > 62:
        if is_crawled(item_id) and item_id[-42:-36] == '.onion':
            is_onion = True
    return is_onion

def is_item_in_domain(domain, item_id):
    is_in_domain = False
    domain_lenght = len(domain)
    if len(item_id) > (domain_lenght+48):
        if item_id[-36-domain_lenght:-36] == domain:
            is_in_domain = True
    return is_in_domain

def get_item_domain(item_id):
    return item_id[19:-36]

def get_domain(item_id):
    item_id = item_id.split('/')
    item_id = item_id[-1]
    return item_id[:-36]

def get_item_parent(item_id):
    return r_serv_metadata.hget('paste_metadata:{}'.format(item_id), 'father')

def get_item_children(item_id):
    return list(r_serv_metadata.smembers('paste_children:{}'.format(item_id)))

def add_item_parent(item_parent, item_id):
    return item_basic.add_item_parent(item_parent, item_id)

def get_item_link(item_id):
    return r_serv_metadata.hget('paste_metadata:{}'.format(item_id), 'real_link')

def get_item_screenshot(item_id):
    screenshot = r_serv_metadata.hget('paste_metadata:{}'.format(item_id), 'screenshot')
    if screenshot:
        return os.path.join(screenshot[0:2], screenshot[2:4], screenshot[4:6], screenshot[6:8], screenshot[8:10], screenshot[10:12], screenshot[12:])
    return ''

def get_item_har_name(item_id):
    os.path.join(screenshot_directory, item_id) + '.json'
    if os.path.isfile(har_path):
        return har_path
    else:
        return None

def get_item_har(har_path):
    pass

def get_item_filename(item_id):
    # Creating the full filepath
    filename = os.path.join(PASTES_FOLDER, item_id)
    filename = os.path.realpath(filename)

    # incorrect filename
    if not os.path.commonprefix([filename, PASTES_FOLDER]) == PASTES_FOLDER:
        return None
    else:
        return filename

def get_item_duplicate(item_id, r_list=True):
    res = r_serv_metadata.smembers('dup:{}'.format(item_id))
    if r_list:
        if res:
            return list(res)
        else:
            return []
    return res

def add_item_duplicate(item_id, l_dup):
    for item_dup in l_dup:
        r_serv_metadata.sadd('dup:{}'.format(item_dup), item_id)
        r_serv_metadata.sadd('dup:{}'.format(item_id), item_dup)

def delete_item_duplicate(item_id):
    item_dup = get_item_duplicate(item_id)
    for item_dup in get_item_duplicate(item_id):
        r_serv_metadata.srem('dup:{}'.format(item_dup), item_id)
    r_serv_metadata.delete('dup:{}'.format(item_id))

def get_raw_content(item_id):
    filepath = get_item_filepath(item_id)
    with open(filepath, 'rb') as f:
        file_content = BytesIO(f.read())
    return file_content

def save_raw_content(item_id, io_content):
    filepath = get_item_filename(item_id)
    if os.path.isfile(filepath):
        #print('File already exist')
        return False
    # create subdir
    dirname = os.path.dirname(filepath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    # # TODO: check if is IO file
    with open(filepath, 'wb') as f:
        f.write(io_content.getvalue())
    return True

# IDEA: send item to duplicate ?
def create_item(obj_id, obj_metadata, io_content):
    '''
    Create a new Item (Import or Test only).

    :param obj_id: item id
    :type obj_metadata: dict - 'first_seen', 'tags'

    :return: is item created
    :rtype: boolean
    '''
    # check if datetime match ??


    # # TODO: validate obj_id

    res = save_raw_content(obj_id, io_content)
    # item saved
    if res:
        # creata tags
        if 'tags' in obj_metadata:
            # # TODO: handle mixed tags: taxonomies and Galaxies
            Tag.api_add_obj_tags(tags=obj_metadata['tags'], object_id=obj_id, object_type="item")
        return True

    # Item not created
    return False

def delete_item(obj_id):
    # check if item exists
    if not exist_item(obj_id):
        return False
    else:
        Tag.delete_obj_tags(obj_id, 'item', Tag.get_obj_tag(obj_id))
        delete_item_duplicate(obj_id)
        # delete MISP event
        r_serv_metadata.delete('misp_events:{}'.format(obj_id))
        r_serv_metadata.delete('hive_cases:{}'.format(obj_id))

        os.remove(get_item_filename(obj_id))

        # get all correlation
        obj_correlations = get_item_all_correlation(obj_id)
        for correlation in obj_correlations:
            if correlation=='cryptocurrency' or correlation=='pgp':
                for obj2_subtype in obj_correlations[correlation]:
                    for obj2_id in obj_correlations[correlation][obj2_subtype]:
                        Correlate_object.delete_obj_relationship(correlation, obj2_id, 'item', obj_id,
                                                            obj1_subtype=obj2_subtype)
            else:
                for obj2_id in obj_correlations[correlation]:
                    Correlate_object.delete_obj_relationship(correlation, obj2_id, 'item', obj_id)
        return True

    ### REQUIRE MORE WORK
    # delete child/son !!!
    ### TODO in inport V2
    # delete from tracked items
    # delete from queue
    ###
    return False
