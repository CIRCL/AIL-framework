#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import gzip
import redis

import Flask_config
import Date
import Tag

PASTES_FOLDER = Flask_config.PASTES_FOLDER
r_cache = Flask_config.r_cache

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
        print("ERROR in: " + item_id)
        print(e)
        item_content = None
    if item_content is None:
        try:
            with gzip.open(item_full_path, 'r') as f:
                item_content = f.read()
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

    return (dict_item, 200)
