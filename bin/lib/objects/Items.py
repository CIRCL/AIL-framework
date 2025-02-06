#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import base64
import gzip
import magic
import os
import re
import sys
import html2text

from io import BytesIO
from uuid import uuid4

from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ail_core import get_ail_uuid, rreplace
from lib.objects.abstract_object import AbstractObject
from lib.ConfigLoader import ConfigLoader
from lib import item_basic
from lib.Language import LanguagesDetector
from lib.data_retention_engine import update_obj_date, get_obj_date_first
from packages import Date


from flask import url_for

config_loader = ConfigLoader()
# # TODO:  get and sanitize ITEMS DIRECTORY
ITEMS_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'
ITEMS_FOLDER = os.path.join(os.path.realpath(ITEMS_FOLDER), '')

r_cache = config_loader.get_redis_conn("Redis_Cache")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
screenshot_directory = config_loader.get_files_directory('screenshot')
har_directory = config_loader.get_files_directory('har')
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


class Item(AbstractObject):
    """
    AIL Item Object. (strings)
    """

    def __init__(self, id):
        super(Item, self).__init__('item', id)

    def exists(self):
        return item_basic.exist_item(self.id)

    def get_date(self, separator=False):
        """
        Returns Item date
        """
        return item_basic.get_item_date(self.id, add_separator=separator)

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
        return {'style': '', 'icon': '', 'color': color, 'radius': 5}

    def get_source(self):
        """
        Returns Item source/feeder name
        """
        # return self.id.split('/')[-5]
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

    def get_content(self, r_type='str'):
        """
        Returns Item content
        """
        if r_type == 'str':
            return item_basic.get_item_content(self.id)
        elif r_type == 'bytes':
            return item_basic.get_item_content_binary(self.id)

    def get_raw_content(self, decompress=False):
        filepath = self.get_filename()
        if decompress:
            raw_content = BytesIO(self.get_content(r_type='bytes'))
        else:
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

    def get_size(self, r_str=False):
        size = os.path.getsize(self.get_filename())/1024.0
        if r_str:
            size = round(size, 2)
        return size

    def get_ail_2_ail_payload(self):
        payload = {'raw': self.get_gzip_content(b64=True)}
        return payload

    def get_parent(self):
        return item_basic.get_item_parent(self.id)

    def set_parent(self, parent_id):
        r_object.sadd(f'child:item::{parent_id}', self.id)
        r_object.hset(f'meta:item::{self.id}', 'parent', parent_id)

    def add_children(self, child_id):
        r_object.sadd(f'child:item::{self.id}', child_id)
        r_object.hset(f'meta:item::{child_id}', 'parent', self.id)

    def get_file_name(self):
        filename = self.get_correlation('file-name').get('file-name')
        if filename:
            return filename.pop()[1:]

    def get_message(self):
        filename = self.get_correlation('message').get('message')
        if filename:
            return filename.pop()[1:]

####################################################################################
####################################################################################

    # TODO ADD function to check if ITEM (content + file) already exists

    def sanitize_id(self):
        if ITEMS_FOLDER in self.id:
            self.id = self.id.replace(ITEMS_FOLDER, '', 1)

        # limit filename length
        basename = self.get_basename()
        if len(basename) > 255:
            new_basename = f'{basename[:215]}{str(uuid4())}.gz'
            self.id = rreplace(self.id, basename, new_basename, 1)
        return self.id

    # # TODO: sanitize_id
    # # TODO: check if already exists ?
    # # TODO: check if duplicate
    def _save_on_disk(self, content, content_type='bytes', b64=False, compressed=False):
        if not content_type == 'bytes':
            content = content.encode()
        if b64:
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

    # # TODO:
    # correlations
    # content
    # tags
    # origin
    # duplicate -> all item iterations ???
    # father
    #
    def create(self, content, content_type='bytes', b64=False, compressed=False):
        self._save_on_disk(content, content_type=content_type, b64=b64, compressed=compressed)

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    # TODO: DELETE ITEM CORRELATION + TAGS + METADATA + ...
    def delete(self):
        self._delete()
        try:
            os.remove(self.get_filename())
            return True
        except FileNotFoundError:
            return False

####################################################################################
####################################################################################

    def get_misp_object(self):
        obj = MISPObject('ail-leak', standalone=True)
        obj_date = self.get_date()
        if obj_date:
            obj.first_seen = obj_date
        else:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={obj_date}')

        obj_attrs = [obj.add_attribute('first-seen', value=obj_date),
                     obj.add_attribute('raw-data', value=self.id, data=self.get_raw_content()),
                     obj.add_attribute('sensor', value=get_ail_uuid())]
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def is_crawled(self):
        return self.id.startswith('crawled')

    # if is_crawled
    def get_domain(self):
        return self.id[19:-36]

    def get_screenshot(self):
        s = self.get_correlation('screenshot')
        if s.get('screenshot'):
            s = s['screenshot'].pop()[1:]
            return os.path.join(s[0:2], s[2:4], s[4:6], s[6:8], s[8:10], s[10:12], s[12:])

    def get_har(self):
        har_path = os.path.join(har_directory, self.id) + '.json'
        if os.path.isfile(har_path):
            return har_path
        else:
            return None

    def get_url(self):
        return r_object.hget(f'meta:item::{self.id}', 'url')

    def set_crawled(self, url, parent_id):
        r_object.hset(f'meta:item::{self.id}', 'url', url)
        self.set_parent(parent_id)

    # options: set of optional meta fields
    def get_meta(self, options=None):
        """
        :type options: set
        """
        if options is None:
            options = set()
        meta = self.get_default_meta(tags=True)
        meta['date'] = self.get_date(separator=True)
        meta['source'] = self.get_source()
        # optional meta fields
        if 'content' in options:
            meta['content'] = self.get_content()
        if 'crawler' in options:
            if self.is_crawled():
                tags = meta.get('tags')
                meta['crawler'] = self.get_meta_crawler(tags=tags)
        if 'duplicates' in options:
            meta['duplicates'] = self.get_duplicates()
        if 'file_name' in options:
            meta['file_name'] = self.get_file_name()
        if 'lines' in options:
            content = meta.get('content')
            meta['lines'] = self.get_meta_lines(content=content)
        if 'parent' in options:
            meta['parent'] = self.get_parent()
        if 'size' in options:
            meta['size'] = self.get_size(r_str=True)
        if 'mimetype' in options:
            content = meta.get('content')
            meta['mimetype'] = self.get_mimetype(content=content)
        if 'investigations' in options:
            meta['investigations'] = self.get_investigations()
        if 'link' in options:
            meta['link'] = self.get_link(flask_context=True)
        if 'last_full_date' in options:
            meta['last_full_date'] = f"{meta['date'][0:4]}-{meta['date'][5:7]}-{meta['date'][8:10]}"

        # meta['encoding'] = None
        return meta

    def get_meta_crawler(self, tags=None):
        """
        :type tags: list
        """
        crawler = {}
        if self.is_crawled():
            crawler['domain'] = self.get_domain()
            crawler['har'] = self.get_har()
            crawler['screenshot'] = self.get_screenshot()
            crawler['url'] = self.get_url()

            domain_tags = self.get_obj_tags('domain', '', crawler['domain'], r_list=True)
            if tags is None:
                tags = self.get_tags()
            crawler['is_tags_safe'] = self.is_tags_safe(tags) and self.is_tags_safe(domain_tags)
        return crawler

    def get_meta_lines(self, content=None):
        if not content:
            content = self.get_content()
        max_length = 0
        nb_line = 0
        for line in content.splitlines():
            length = len(line)
            if length > max_length:
                max_length = length
            nb_line += 1
        return {'nb': nb_line, 'max_length': max_length}

    # TODO RENAME ME
    def get_languages(self, min_len=600, num_langs=3, min_proportion=0.2, min_probability=0.7, force_gcld3=False):
        ld = LanguagesDetector(nb_langs=num_langs, min_proportion=min_proportion, min_probability=min_probability, min_len=min_len)
        return ld.detect(self.get_content(), force_gcld3=force_gcld3)

    def get_mimetype(self, content=None):
        if not content:
            content = self.get_content()
        return magic.from_buffer(content, mime=True)

    ############################################################################
    ############################################################################

def _get_dir_source_name(directory, source_name=None, l_sources_name=None, filter_dir=False):
    """
    :type l_sources_name: set
    """
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
                # try:
                int(src_name)
                to_add = os.path.join(source_name)
                # filter sources, remove first directory
                if filter_dir:
                    to_add = to_add.replace('archive/', '').replace('alerts/', '')
                l_sources_name.add(to_add)
                return l_sources_name
                # except:
                #    pass
            if source_name:
                src_name = os.path.join(source_name, src_name)
            l_sources_name = _get_dir_source_name(directory, source_name=src_name, l_sources_name=l_sources_name, filter_dir=filter_dir)
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

def _manual_set_items_date_first_last():
    first = 9999
    last = 0
    sources = get_items_sources()
    for source in sources:
        dir_source = os.path.join(os.environ['AIL_HOME'], ITEMS_FOLDER, source)
        for dir_name in os.listdir(dir_source):
            if os.path.isdir(os.path.join(dir_source, dir_name)):
                date = int(dir_name)
                if date < first:
                    first = date
                if date > last:
                    last = date
    if first != 9999:
        update_obj_date(first, 'item')
    if last != 0:
        update_obj_date(last, 'item')

################################################################################
################################################################################
################################################################################

def get_nb_items_objects(filters={}):
    nb = 0
    date_from = filters.get('date_from')
    date_to = filters.get('date_to')
    if 'sources' in filters:
        sources = filters['sources']
    else:
        sources = get_all_sources()
    sources = sorted(sources)

    # date
    if date_from and date_to:
        daterange = Date.get_daterange(date_from, date_to)
    elif date_from:
        daterange = Date.get_daterange(date_from, Date.get_today_date_str())
    elif date_to:
        date_from = get_obj_date_first('item')
        daterange = Date.get_daterange(date_from, date_to)
    else:
        date_from = get_obj_date_first('item')
        daterange = Date.get_daterange(date_from, Date.get_today_date_str())

    for source in sources:
        for date in daterange:
            date = f'{date[0:4]}/{date[4:6]}/{date[6:8]}'
            full_dir = os.path.join(ITEMS_FOLDER, source, date)
            if not os.path.isdir(full_dir):
                continue
            nb += len(os.listdir(full_dir))
    return nb

def get_all_items_objects(filters={}):
    date_from = filters.get('date_from')
    date_to = filters.get('date_to')
    if 'sources' in filters:
        sources = filters['sources']
    else:
        sources = get_all_sources()
    sources = sorted(sources)
    if filters.get('start'):
        if filters['start']['type'] == 'item':
            start_id = filters['start']['id']
            item = Item(start_id)
            if not item.exists():
                start_id = None
                start_date = None
            # remove sources
            start_source = item.get_source()
            i = 0
            while start_source and len(sources) > i:
                if sources[i] == start_source:
                    sources = sources[i:]
                    start_source = None
                i += 1
            start_date = item.get_date()
        else:
            start_id = None
            start_date = None
    else:
        start_id = None
        start_date = None

    # date
    if date_from and date_to:
        daterange = Date.get_daterange(date_from, date_to)
    elif date_from:
        daterange = Date.get_daterange(date_from, Date.get_today_date_str())
    elif date_to:
        date_from = get_obj_date_first('item')
        daterange = Date.get_daterange(date_from, date_to)
    else:
        date_from = get_obj_date_first('item')
        if date_from:
            daterange = Date.get_daterange(date_from, Date.get_today_date_str())
        else:
            daterange = []
    if start_date:
        if int(start_date) > int(date_from):
            i = 0
            while start_date and len(daterange) > i:
                if daterange[i] == start_date:
                    daterange = daterange[i:]
                    start_date = None
                i += 1

    for source in sources:
        for date in daterange:
            date = f'{date[0:4]}/{date[4:6]}/{date[6:8]}'
            full_dir = os.path.join(ITEMS_FOLDER, source, date)
            s_dir = os.path.join(source, date)
            if not os.path.isdir(full_dir):
                continue

            # TODO replace by os.scandir() ????
            all_items = sorted([os.path.join(s_dir, f)
                                for f in os.listdir(full_dir)
                                if os.path.isfile(os.path.join(full_dir, f))])
            # start obj id
            if start_id:
                i = 0
                while start_id and len(all_items) > i:
                    if all_items[i] == start_id:
                        if i == len(all_items):
                            all_items = []
                        else:
                            all_items = all_items[i+1:]
                        start_id = None
                    i += 1
            for obj_id in all_items:
                if obj_id:
                    yield Item(obj_id)

################################################################################
################################################################################
################################################################################

#### API ####

def api_get_item(data):
    item_id = data.get('id', None)
    if not item_id:
        return {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400
    item = Item(item_id)
    if not item.exists():
        return {'status': 'error', 'reason': 'Item not found'}, 404

    options = set()
    if data.get('content'):
        options.add('content')
    if data.get('crawler'):
        options.add('crawler')
    if data.get('duplicates'):
        options.add('duplicates')
    if data.get('lines'):
        options.add('lines')
    if data.get('mimetype'):
        options.add('mimetype')
    if data.get('parent'):
        options.add('parent')
    if data.get('size'):
        options.add('size')

    # TODO correlation

    return item.get_meta(options=options), 200


# -- API -- #

################################################################################
################################################################################
################################################################################

            # TODO

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

def get_item_content(item_id):
    return item_basic.get_item_content(item_id)


# API
# def get_item(request_dict):
#     if not request_dict:
#         return {'status': 'error', 'reason': 'Malformed JSON'}, 400
#
#     item_id = request_dict.get('id', None)
#     if not item_id:
#         return {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400
#     if not exist_item(item_id):
#         return {'status': 'error', 'reason': 'Item not found'}, 404
#
#     dict_item = {}
#     dict_item['id'] = item_id
#     date = request_dict.get('date', True)
#     if date:
#         add_separator = False
#         if request_dict.get('date_separator', False):
#             add_separator = True
#         dict_item['date'] = get_item_date(item_id, add_separator=add_separator)
#     tags = request_dict.get('tags', True)
#     if tags:
#         dict_item['tags'] = Tag.get_object_tags('item', item_id)
#
#     size = request_dict.get('size', False)
#     if size:
#         dict_item['size'] = get_item_size(item_id)
#
#     content = request_dict.get('content', False)
#     if content:
#         # UTF-8 outpout, # TODO: use base64
#         dict_item['content'] = get_item_content(item_id)
#
#     raw_content = request_dict.get('raw_content', False)
#     if raw_content:
#         dict_item['raw_content'] = get_raw_content(item_id)
#
#     lines_info = request_dict.get('lines', False)
#     if lines_info:
#         dict_item['lines'] = get_lines_info(item_id, dict_item.get('content', 'None'))
#
#     if request_dict.get('pgp'):
#         dict_item['pgp'] = {}
#         if request_dict['pgp'].get('key'):
#             dict_item['pgp']['key'] = get_item_pgp_key(item_id)
#         if request_dict['pgp'].get('mail'):
#             dict_item['pgp']['mail'] = get_item_pgp_mail(item_id)
#         if request_dict['pgp'].get('name'):
#             dict_item['pgp']['name'] = get_item_pgp_name(item_id)
#
#     if request_dict.get('cryptocurrency'):
#         dict_item['cryptocurrency'] = {}
#         if request_dict['cryptocurrency'].get('bitcoin'):
#             dict_item['cryptocurrency']['bitcoin'] = get_item_bitcoin(item_id)
#
#     return dict_item, 200



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
        item = Item(item_id)
        desc_list.append( {'id': item_id, 'date': get_item_date(item_id), 'tags': item.get_tags(r_list=True)})
    return desc_list

def is_crawled(item_id):
    return item_basic.is_crawled(item_id)

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

# TODO MOVE ME
def get_item_har_name(item_id):
    har_path = os.path.join(har_directory, item_id) + '.json'
    if os.path.isfile(har_path):
        return har_path
    else:
        return None

def get_item_filename(item_id):
    # Creating the full filepath
    filename = os.path.join(ITEMS_FOLDER, item_id)
    filename = os.path.realpath(filename)

    # incorrect filename
    if not os.path.commonprefix([filename, ITEMS_FOLDER]) == ITEMS_FOLDER:
        return None
    else:
        return filename

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
            item = Item(obj_id)
            # # TODO: handle mixed tags: taxonomies and Galaxies
            # for tag in obj_metadata['tags']:
            #     item.add_tag(tag)
        return True

    # Item not created
    return False

    # # check if item exists
    # if not exist_item(obj_id):
    #     return False
    # else:
    #     delete_item_duplicate(obj_id)
    #     # delete MISP event
    #     r_s_metadata.delete('misp_events:{}'.format(obj_id))
    #     r_s_metadata.delete('hive_cases:{}'.format(obj_id))
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


# if __name__ == '__main__':
#     content = 'test file content'
#     duplicates = {'tests/2020/01/02/test.gz': [{'algo':'ssdeep', 'similarity':75}, {'algo':'tlsh', 'similarity':45}]}
#
    # item = Item('tests/2020/01/02/test_save.gz')
#     item.create(content, _save=False)
#     filters = {'date_from': '20230101', 'date_to': '20230501', 'sources': ['crawled', 'submitted'], 'start': ':submitted/2023/04/28/submitted_2b3dd861-a75d-48e4-8cec-6108d41450da.gz'}
#     gen = get_all_items_objects(filters=filters)
#     for obj_id in gen:
#         print(obj_id.id)
