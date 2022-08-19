#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import base64
import gzip
import os
import re
import sys
import redis
import cld3
import html2text

from io import BytesIO

from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from export.Export import get_ail_uuid # # TODO: REPLACE
from lib.objects.abstract_object import AbstractObject
from lib.ConfigLoader import ConfigLoader
from lib import item_basic

from packages import Tag


from flask import url_for

config_loader = ConfigLoader()
# # TODO:  get and sanityze ITEMS DIRECTORY
ITEMS_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'
ITEMS_FOLDER = os.path.join(os.path.realpath(ITEMS_FOLDER), '')

r_cache = config_loader.get_redis_conn("Redis_Cache")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
screenshot_directory = config_loader.get_files_directory('screenshot')
har_directory = config_loader.get_files_directory('har')
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


################################################################################
################################################################################
################################################################################

class Item(AbstractObject):
    """
    AIL Item Object. (strings)
    """

    def __init__(self, id):
        super(Item, self).__init__('item', id)

    def get_date(self, separator=False):
        """
        Returns Item date
        """
        return item_basic.get_item_date(self.id, add_separator=separator)

    def get_source(self):
        """
        Returns Item source/feeder name
        """
        #return self.id.split('/')[-5]
        l_source = self.id.split('/')[:-4]
        return os.path.join(*l_source)

    def get_basename(self):
        return os.path.basename(self.id)

    def get_filename(self):
        # Creating the full filepath
        filename = os.path.join(ITEMS_FOLDER, self.id)
        filename = os.path.realpath(filename)

        # incorrect filename
        if not os.path.commonprefix([filename, ITEMS_FOLDER]) == ITEMS_FOLDER:
            return None
        else:
            return filename

    def get_content(self, binary=False):
        """
        Returns Item content
        """
        if binary:
            return item_basic.get_item_content_binary(self.id)
        else:
            return item_basic.get_item_content(self.id)

    def get_raw_content(self):
        filepath = self.get_filename()
        with open(filepath, 'rb') as f:
            raw_content = BytesIO(f.read())
        return raw_content

    def get_gzip_content(self, b64=False):
        with open(self.get_filename(), 'rb') as f:
            content = f.read()
        if b64:
            content = base64.b64encode(content)
        return content.decode()

    def get_html2text_content(self, content=None, ignore_links=False):
        if not content:
            content = self.get_content()
        h = html2text.HTML2Text()
        h.ignore_links = ignore_links
        h.ignore_images = ignore_links
        return h.handle(content)

    def get_size(self, str=False):
        size = os.path.getsize(self.get_filename())/1024.0
        if str:
            size = round(size, 2)
        return size

    def get_ail_2_ail_payload(self):
        payload = {'raw': self.get_gzip_content(b64=True)}
        return payload

    def set_father(self, father_id): # UPDATE KEYS ?????????????????????????????
        r_serv_metadata.sadd(f'paste_children:{father_id}', self.id)
        r_serv_metadata.hset(f'paste_metadata:{self.id}', 'father', father_id)

        #f'obj:children:{obj_type}:{subtype}:{id}, {obj_type}:{subtype}:{id}
        #f'obj:metadata:{obj_type}:{subtype}:{id}', 'father', fathe
        #  => ON Object LEVEL ?????????




    def sanitize_id(self):
        pass

    # # TODO: sanitize_id
    # # TODO: check if already exists ?
    # # TODO: check if duplicate
    def save_on_disk(self, content, binary=True, compressed=False, base64=False):
        if not binary:
            content = content.encode()
        if base64:
            content = base64.standard_b64decode(content)
        if not compressed:
            content = gzip.compress(content)

        # # TODO: # FIXME: raise Exception id filename is None ######
        filename = self.get_filename()
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'wb') as f:
            f.write(content)


    # # TODO: correlations
    #
    # content
    # tags
    # origin
    # duplicate -> all item iterations ???
    #
    def create(self, content, tags, father=None, duplicates=[], _save=True):
        if _save:
            self.save_on_disk(content, binary=True, compressed=False, base64=False)

        # # TODO:
        # for tag in tags:
        #     self.add_tag(tag)

        if father:
            pass

        for obj_id in duplicates:
            for dup in duplicates[obj_id]:
                self.add_duplicate(obj_id, dup['algo'], dup['similarity'])






    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    # TODO: DELETE ITEM CORRELATION + TAGS + METADATA + ...
    def delete(self):
        self._delete()
        try:
            os.remove(self.get_filename())
            return True
        except FileNotFoundError:
            return False

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_item.showItem', id=self.id)
        else:
            url = f'{baseurl}/object/item?id={self.id}'
        return url

    def get_svg_icon(self):
        if is_crawled(self.id):
            color = 'red'
        else:
            color = '#332288'
        return {'style': '', 'icon': '', 'color': color, 'radius':5}

    def get_misp_object(self):
        obj_date = self.get_date()
        obj = MISPObject('ail-leak', standalone=True)
        obj.first_seen = obj_date

        obj_attrs = []
        obj_attrs.append( obj.add_attribute('first-seen', value=obj_date) )
        obj_attrs.append( obj.add_attribute('raw-data', value=self.id, data=self.get_raw_content()) )
        obj_attrs.append( obj.add_attribute('sensor', value=get_ail_uuid()) )
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def exist_correlation(self):
        pass

    def is_crawled(self):
        return self.id.startswith('crawled')

    # if is_crawled
    def get_domain(self):
        return self.id[19:-36]

    def get_screenshot(self):
        s = r_serv_metadata.hget(f'paste_metadata:{self.id}', 'screenshot')
        if s:
            return os.path.join(s[0:2], s[2:4], s[4:6], s[6:8], s[8:10], s[10:12], s[12:])

    def get_har(self):
        har_path = os.path.join(har_directory, self.id) + '.json'
        if os.path.isfile(har_path):
            return har_path
        else:
            return None

    def get_url(self):
        return r_serv_metadata.hget(f'paste_metadata:{self.id}', 'real_link')

    # options: set of optional meta fields
    def get_meta(self, options=set()):
        meta = {}
        meta['id'] = self.id
        meta['date'] = self.get_date(separator=True) ############################ # TODO:
        meta['source'] = self.get_source()
        meta['tags'] = self.get_tags()
        # optional meta fields
        if 'content' in options:
            meta['content'] = self.get_content()
        if 'crawler' in options:
            if self.is_crawled():
                tags = meta.get('tags')
                meta['crawler'] = self.get_meta_crawler(tags=tags)
        if 'duplicates' in options:
            meta['duplicates'] = self.get_duplicates()
        if 'lines' in options:
            content = meta.get('content')
            meta['lines'] = self.get_meta_lines(content=content)
        if 'size' in options:
            meta['size'] = self.get_size(str=True)

        # # TODO: ADD GET FATHER

        # meta['encoding'] = None
        return meta

    def get_meta_crawler(self, tags=[]):
        crawler = {}
        if self.is_crawled():
            crawler['domain'] = self.get_domain()
            crawler['har'] = self.get_har()
            crawler['screenshot'] = self.get_screenshot()
            crawler['url'] = self.get_url()
            if not tags:
                tags = self.get_tags()
            crawler['is_tags_safe'] = Tag.is_tags_safe(tags)
        return crawler

    def get_meta_lines(self, content=None):
        if not content:
            content = self.get_content()
        max_length = 0
        line_id = 0
        nb_line = 0
        for line in content.splitlines():
            length = len(line)
            if length > max_length:
                max_length = length
            nb_line += 1
        return {'nb': nb_line, 'max_length': max_length}

    ############################################################################
    ############################################################################

def _get_dir_source_name(dir, source_name=None, l_sources_name=set(), filter_dir=False):
    if not l_sources_name:
        l_sources_name = set()
    if source_name:
        l_dir = os.listdir(os.path.join(dir, source_name))
    else:
        l_dir = os.listdir(dir)
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
            l_sources_name = _get_dir_source_name(dir, source_name=src_name, l_sources_name=l_sources_name, filter_dir=filter_dir)
    return l_sources_name

def get_items_sources(filter_dir=False, r_list=False):
    res = _get_dir_source_name(ITEMS_FOLDER, filter_dir=filter_dir)
    if res:
        if r_list:
            res = list(res)
        return res
    else:
        return []

def get_items_by_source(source):
    l_items = []
    dir_item = os.path.join(os.environ['AIL_HOME'], ITEMS_FOLDER, source)
    for root, dirs, files in os.walk(dir_item):
        for file in files:
            item_id = os.path.join(root, file).replace(ITEMS_FOLDER, '', 1)
            l_items.append(item_id)
    return l_items

################################################################################
################################################################################
################################################################################

def exist_item(item_id):
    return item_basic.exist_item(item_id)

def get_basename(item_id):
    return os.path.basename(item_id)

def get_item_id(full_path):
    return full_path.replace(ITEMS_FOLDER, '', 1)

def get_item_filepath(item_id):
    return item_basic.get_item_filepath(item_id)

def get_item_date(item_id, add_separator=False):
    return item_basic.get_item_date(item_id, add_separator=add_separator)

def get_source(item_id):
    return item_basic.get_source(item_id)

def get_all_sources():
    return item_basic.get_all_items_sources(r_list=True)

def get_item_basename(item_id):
    return os.path.basename(item_id)

def get_item_size(item_id):
    return round(os.path.getsize(os.path.join(ITEMS_FOLDER, item_id))/1024.0, 2)

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
    item_metadata = {'date': get_item_date(item_id, add_separator=True),
                     'source': get_source(item_id),
                     'size': get_item_size(item_id),
                     'encoding': get_item_encoding(item_id),
                     'lines': get_lines_info(item_id, item_content=item_content)
                     }
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
        return {'status': 'error', 'reason': 'Malformed JSON'}, 400

    item_id = request_dict.get('id', None)
    if not item_id:
        return {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400
    if not exist_item(item_id):
        return {'status': 'error', 'reason': 'Item not found'}, 404

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

    return dict_item, 200



def api_get_item_content_base64_utf8(request_dict):
    item_id = request_dict.get('id', None)
    if not request_dict:
        return {'status': 'error', 'reason': 'Malformed JSON'}, 400
    if not item_id:
        return {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400
    if not exist_item(item_id):
        return {'status': 'error', 'reason': 'Item not found'}, 404

    item_content = get_item_content(item_id)
    item_content = base64.b64encode((item_content.encode('utf-8'))).decode('UTF-8')
    return {'status': 'success', 'content': item_content}, 200


def api_get_items_sources():
    item_content = {'sources': get_all_sources()}
    return item_content, 200

# def check_item_source(request_dict):
#     source = request_dict.get('source', None)
#     if not request_dict:
#         return {'status': 'error', 'reason': 'Malformed JSON'}, 400
#     if not source:
#         return {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400
#
#     all_sources = item_basic.get_all_items_sources()
#
#     if source not in all_sources:
#         return {'status': 'error', 'reason': 'Invalid source', 'provide': source}, 400
#     return {'status': 'success', 'reason': 'Valid source', 'provide': source}, 200


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

def get_crawler_matadata(item_id, tags=None):
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
    filename = os.path.join(ITEMS_FOLDER, item_id)
    filename = os.path.realpath(filename)

    # incorrect filename
    if not os.path.commonprefix([filename, ITEMS_FOLDER]) == ITEMS_FOLDER:
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

# # TODO:
def delete_item(obj_id):
    pass

    # # check if item exists
    # if not exist_item(obj_id):
    #     return False
    # else:
    #     delete_item_duplicate(obj_id)
    #     # delete MISP event
    #     r_serv_metadata.delete('misp_events:{}'.format(obj_id))
    #     r_serv_metadata.delete('hive_cases:{}'.format(obj_id))
    #
    #     os.remove(get_item_filename(obj_id))
    #
    #     # get all correlation
    #     obj_correlations = get_item_all_correlation(obj_id)
    #     for correlation in obj_correlations:
    #         if correlation=='cryptocurrency' or correlation=='pgp':
    #             for obj2_subtype in obj_correlations[correlation]:
    #                 for obj2_id in obj_correlations[correlation][obj2_subtype]:
    #                     Correlate_object.delete_obj_relationship(correlation, obj2_id, 'item', obj_id,
    #                                                         obj1_subtype=obj2_subtype)
    #         else:
    #             for obj2_id in obj_correlations[correlation]:
    #                 Correlate_object.delete_obj_relationship(correlation, obj2_id, 'item', obj_id)
    #
    #     # delete father/child
    #     delete_node(obj_id)
    #
    #     # delete item metadata
    #     r_serv_metadata.delete('paste_metadata:{}'.format(obj_id))
    #
    #     return True
    #
    # ### TODO in inport V2
    # # delete from tracked items
    #
    # # # # TODO: # FIXME: LATER
    # # delete from queue
    # ###
    # return False

#### ####
# def delete_node(item_id):
#     if is_node(item_id):
#         if is_crawled(item_id):
#             delete_domain_node(item_id)
#         item_basic._delete_node(item_id)
#
# def delete_domain_node(item_id):
#     if is_domain_root(item_id):
#         # remove from domain history
#         domain, port = get_item_domain_with_port(item_id).split(':')
#         domain_basic.delete_domain_item_core(item_id, domain, port)
#     for child_id in get_all_domain_node_by_item_id(item_id):
#         delete_item(child_id)


if __name__ == '__main__':
    content = 'test file content'
    duplicates = {'tests/2020/01/02/test.gz': [{'algo':'ssdeep', 'similarity':75}, {'algo':'tlsh', 'similarity':45}]}

    item = Item('tests/2020/01/02/test_save.gz')
    item.create(content, _save=False)
