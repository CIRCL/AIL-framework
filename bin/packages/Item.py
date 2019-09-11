#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import gzip
import redis

sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'modules'))
import Flask_config
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Date
import Tag

PASTES_FOLDER = Flask_config.PASTES_FOLDER
r_cache = Flask_config.r_cache
r_serv_metadata = Flask_config.r_serv_metadata

def exist_item(item_id):
    if os.path.isfile(os.path.join(PASTES_FOLDER, item_id)):
        return True
    else:
        return False

def get_item_date(item_id):
    l_directory = item_id.split('/')
    return '{}{}{}'.format(l_directory[-4], l_directory[-3], l_directory[-2])

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
        dict_item['date'] = get_item_date(item_id)
    tags = request_dict.get('tags', True)
    if tags:
        dict_item['tags'] = Tag.get_item_tags(item_id)

    size = request_dict.get('size', False)
    if size:
        dict_item['size'] = get_item_size(item_id)

    content = request_dict.get('content', False)
    if content:
        # UTF-8 outpout, # TODO: use base64
        dict_item['content'] = get_item_content(item_id)

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

def _get_item_correlation(correlation_name, correlation_type, item_id):
    print('item_{}_{}:{}'.format(correlation_name, correlation_type, item_id))
    res = r_serv_metadata.smembers('item_{}_{}:{}'.format(correlation_name, correlation_type, item_id))
    if res:
        return list(res)
    else:
        return []

def get_item_bitcoin(item_id):
    return _get_item_correlation('cryptocurrency', 'bitcoin', item_id)

def get_item_pgp_key(item_id):
    return _get_item_correlation('pgpdump', 'key', item_id)

def get_item_pgp_name(item_id):
    return _get_item_correlation('pgpdump', 'name', item_id)

def get_item_pgp_mail(item_id):
    return _get_item_correlation('pgpdump', 'mail', item_id)


###
### GET Internal Module DESC
###
def get_item_list_desc(list_item_id):
    desc_list = []
    for item_id in list_item_id:
        desc_list.append( {'id': item_id, 'date': get_item_date(item_id), 'tags': Tag.get_item_tags(item_id)} )
    return desc_list
