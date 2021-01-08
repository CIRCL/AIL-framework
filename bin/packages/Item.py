#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import redis
import cld3
import html2text

from io import BytesIO

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Date
import Tag
import Cryptocurrency
import Pgp

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import item_basic
import domain_basic
import ConfigLoader
import Correlate_object
import Decoded
import Screenshot
import Username

from item_basic import *

config_loader = ConfigLoader.ConfigLoader()
# get and sanityze PASTE DIRECTORY
PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'
PASTES_FOLDER = os.path.join(os.path.realpath(PASTES_FOLDER), '')

r_cache = config_loader.get_redis_conn("Redis_Cache")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
screenshot_directory = config_loader.get_files_directory('screenshot')
har_directory = config_loader.get_files_directory('har')

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
    return item_basic.get_item_date(item_id, add_separator=add_separator)

def get_source(item_id):
    return item_basic.get_source(item_id)

def get_item_basename(item_id):
    return os.path.basename(item_id)

def get_item_size(item_id):
    return round(os.path.getsize(os.path.join(PASTES_FOLDER, item_id))/1024.0, 2)

def get_item_encoding(item_id):
    return None

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


def get_item_metadata(item_id, item_content=None):
    ## TODO: FIXME ##performance
    # encoding
    # language
    # lines info

    item_metadata = {}
    item_metadata['date'] = get_item_date(item_id, add_separator=True)
    item_metadata['source'] = get_source(item_id)
    item_metadata['size'] = get_item_size(item_id)
    item_metadata['encoding'] = get_item_encoding(item_id)
    item_metadata['lines'] = get_lines_info(item_id, item_content=item_content)

    return item_metadata

def get_item_parent(item_id):
    return item_basic.get_item_parent(item_id)

def add_item_parent(item_parent, item_id):
    return item_basic.add_item_parent(item_parent, item_id)

def get_item_content(item_id):
    return item_basic.get_item_content(item_id)

def get_item_content_html2text(item_id, item_content=None, ignore_links=False):
    if not item_content:
        item_content = get_item_content(item_id)
    h = html2text.HTML2Text()
    h.ignore_links = ignore_links
    h.ignore_images = ignore_links
    return h.handle(item_content)

def remove_all_urls_from_content(item_id, item_content=None):
    if not item_content:
        item_content = get_item_content(item_id)
    regex = r'\b(?:http://|https://)?(?:[a-zA-Z\d-]{,63}(?:\.[a-zA-Z\d-]{,63})+)(?:\:[0-9]+)*(?:/(?:$|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*\b'
    url_regex = re.compile(regex)
    urls = url_regex.findall(item_content)
    urls = sorted(urls, key=len, reverse=True)
    for url in urls:
        item_content = item_content.replace(url, '')

    regex_pgp_public_blocs = r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]+?-----END PGP PUBLIC KEY BLOCK-----'
    regex_pgp_signature = r'-----BEGIN PGP SIGNATURE-----[\s\S]+?-----END PGP SIGNATURE-----'
    regex_pgp_message = r'-----BEGIN PGP MESSAGE-----[\s\S]+?-----END PGP MESSAGE-----'
    re.compile(regex_pgp_public_blocs)
    re.compile(regex_pgp_signature)
    re.compile(regex_pgp_message)

    res = re.findall(regex_pgp_public_blocs, item_content)
    for it in res:
        item_content = item_content.replace(it, '')
    res = re.findall(regex_pgp_signature, item_content)
    for it in res:
        item_content = item_content.replace(it, '')
    res = re.findall(regex_pgp_message, item_content)
    for it in res:
        item_content = item_content.replace(it, '')

    return item_content

def get_item_languages(item_id, min_len=600, num_langs=3, min_proportion=0.2, min_probability=0.7):
    all_languages = []

    ## CLEAN CONTENT ##
    content = get_item_content_html2text(item_id, ignore_links=True)
    content = remove_all_urls_from_content(item_id, item_content=content)

    # REMOVE USELESS SPACE
    content = ' '.join(content.split())
    #- CLEAN CONTENT -#

    #print(content)
    #print(len(content))
    if len(content) >= min_len:
        for lang in cld3.get_frequent_languages(content, num_langs=num_langs):
            if lang.proportion >= min_proportion and lang.probability >= min_probability and lang.is_reliable:
                all_languages.append(lang)
    return all_languages

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

def get_item_username(item_id, sub_type=None, get_nb=False):
    '''
    Return all pgp of a given item.

    :param item_id: item id
    :param sub_type: list of username type
    :type sub_type: list, optional
    '''
    return Username.correlation.get_item_correlation_dict(item_id, correlation_type=sub_type, get_nb=get_nb)

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

def is_crawled(item_id):
    return item_basic.is_crawled(item_id)

def get_crawler_matadata(item_id, ltags=None):
    dict_crawler = {}
    if is_crawled(item_id):
        dict_crawler['domain'] = get_item_domain(item_id)
        if not ltags:
            ltags = Tag.get_obj_tag(item_id)
        dict_crawler['is_tags_safe'] = Tag.is_tags_safe(ltags)
        dict_crawler['url'] = get_item_link(item_id)
        dict_crawler['screenshot'] = get_item_screenshot(item_id)
        dict_crawler['har'] = get_item_har_name(item_id)
    return dict_crawler

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
    return item_basic.get_item_domain(item_id)

def get_domain(item_id):
    item_id = item_id.split('/')
    item_id = item_id[-1]
    return item_id[:-36]

def get_item_domain_with_port(item_id):
    return r_serv_metadata.hget('paste_metadata:{}'.format(item_id), 'domain')

def get_item_link(item_id):
    return r_serv_metadata.hget('paste_metadata:{}'.format(item_id), 'real_link')

def get_item_screenshot(item_id):
    screenshot = r_serv_metadata.hget('paste_metadata:{}'.format(item_id), 'screenshot')
    if screenshot:
        return os.path.join(screenshot[0:2], screenshot[2:4], screenshot[4:6], screenshot[6:8], screenshot[8:10], screenshot[10:12], screenshot[12:])
    return ''

def get_item_har_name(item_id):
    har_path = os.path.join(har_directory, item_id) + '.json'
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

def get_item_nb_duplicates(item_id):
    return r_serv_metadata.scard('dup:{}'.format(item_id))

def get_item_duplicates_dict(item_id):
    dict_duplicates = {}
    for duplicate in get_item_duplicate(item_id):
        duplicate = duplicate[1:-1].replace('\'', '').replace(' ', '').split(',')
        duplicate_id = duplicate[1]
        if not duplicate_id in dict_duplicates:
            dict_duplicates[duplicate_id] = {'date': get_item_date(duplicate_id, add_separator=True), 'algo': {}}
        algo = duplicate[0]
        if algo == 'tlsh':
            similarity = 100 - int(duplicate[2])
        else:
            similarity = int(duplicate[2])
        dict_duplicates[duplicate_id]['algo'][algo] = similarity
    return dict_duplicates

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

        # delete father/child
        delete_node(obj_id)

        # delete item metadata
        r_serv_metadata.delete('paste_metadata:{}'.format(obj_id))

        return True

    ### TODO in inport V2
    # delete from tracked items
    # delete from queue
    ###
    return False

#### ####
def delete_node(item_id):
    if is_node(item_id):
        if is_crawled(item_id):
            delete_domain_node(item_id)
        item_basic._delete_node(item_id)

def delete_domain_node(item_id):
    if is_domain_root(item_id):
        # remove from domain history
        domain, port = get_item_domain_with_port(item_id).split(':')
        domain_basic.delete_domain_item_core(item_id, domain, port)
    for child_id in get_all_domain_node_by_item_id(item_id):
        delete_item(child_id)

# if __name__ == '__main__':
#     import Domain
#     domain = Domain.Domain('domain.onion')
#     for domain_history in domain.get_domain_history():
#         domain_item = domain.get_domain_items_crawled(epoch=domain_history[1]) # item_tag
#         if "items" in domain_item:
#             for item_dict in domain_item['items']:
#                 item_id = item_dict['id']
#                 print(item_id)
#                 for lang in get_item_languages(item_id, min_proportion=0.2, min_probability=0.8):
#                     print(lang)
#                 print()
#     print(get_item_languages(item_id, min_proportion=0.2, min_probability=0.6)) # 0.7 ?
