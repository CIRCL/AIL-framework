#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import logging.config
import sys
import time
import uuid

import meilisearch
from hashlib import sha256

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_logger
from lib.ConfigLoader import ConfigLoader
from lib.objects import Domains
from lib.objects import FilesNames
from lib.objects import Images
from lib.objects import Items
from lib.objects import Messages
from lib.objects import Screenshots
from lib.objects import Titles
from lib.objects import UsersAccount
from lib import chats_viewer
from packages import Date

logging.config.dictConfig(ail_logger.get_config(name='ail'))
logger = logging.getLogger()

config_loader = ConfigLoader()
IS_MEILISEARCH_ENABLED = config_loader.get_config_boolean('Indexer', 'meilisearch')
M_URL = config_loader.get_config_str('Indexer', 'meilisearch_url')
M_KEY = config_loader.get_config_str('Indexer', 'meilisearch_key')
r_search = config_loader.get_db_conn("Kvrocks_Searchs")
config_loader = None


def get_obj_uuid5(obj_gid):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, obj_gid))


def is_meilisearch_enabled():
    return IS_MEILISEARCH_ENABLED


MESSAGES_INDEXES = {'cdiscord', 'ctelegram', 'cmatrix'}  # TODO dynamic load of chat name -> load all chat protocol
DATERANGE_INDEXES = {'filename', 'title'}


def load_indexes_names():
    names = {'desc-dom', 'desc-img', 'desc-screen', 'filename', 'title'}
    for domain_types in Domains.get_all_domains_types():
        names.add(domain_types)
    for chat_name in MESSAGES_INDEXES:
        names.add(chat_name)
    return sorted(names)


INDEX_NAMES = load_indexes_names()


def get_indexes_names():
    return INDEX_NAMES


def index_all():
    # Engine._delete_all()
    # Engine._delete('onion')
    # delete_crawled_content_domains_items()
    Engine.create_indexes()
    # Engine._create_index('onion')
    # Engine.setup_indexes_searchable_filterable_sortable()
    index_crawled()
    index_chats()
    index_user_accounts()
    index_messages()
    index_images_descriptions()
    index_screenshots_descriptions()
    index_domains_descriptions()
    index_titles()
    index_file_names()


class MeiliSearch:
    def __init__(self):
        self.client = meilisearch.Client(M_URL, M_KEY)

    def init(self):
        if not self.get_indexes():
            self.create_indexes()

    def search(self, indexes, query, nb=20, page=1, timestamp_from=None, timestamp_to=None, sort='recent'):
        # TODO investigate attributesToRetrieve speed
        end_query = []
        for index in indexes:
            q = {'indexUid': index,
                 'q': query,
                 'attributesToSearchOn': ['content'],
                 'attributesToCrop': ['content'],
                 'attributesToHighlight': ['content'],
                 'highlightPreTag': '🔎⏩',
                 'highlightPostTag': '⏪🔍',
                 'cropLength': 100,
                 'showMatchesPosition': False,
                 }
            if sort == 'recent':
                q['sort'] = ['last:desc']
            if timestamp_from and timestamp_to:
                if index in DATERANGE_INDEXES:
                    q['filter'] = f'first >= {timestamp_from} AND last <= {timestamp_to}'
                else:
                    q['filter'] = f'last >= {timestamp_from} AND last <= {timestamp_to}'
            elif timestamp_from:
                if index in DATERANGE_INDEXES:
                    q['filter'] = f'first >= {timestamp_from}'
                else:
                    q['filter'] = f'last >= {timestamp_from}'
            elif timestamp_to:
                q['filter'] = f'last <= {timestamp_to}'
            end_query.append(q)
        return self.client.multi_search(end_query, {'limit': nb, 'offset': (page - 1) * nb})

    def get_indexes(self):
        names = []
        for index in self.client.get_indexes().get('results', []):
            names.append(index.uid)
        return names

    def _create_index(self, index_name):
        self.client.create_index(index_name, {'primaryKey': 'uuid'})
        self.setup_index_searchable_filterable_sortable(index_name)

    def create_indexes(self):
        for index_name in get_indexes_names():
            self._create_index(index_name)

    def setup_index_searchable_filterable_sortable(self, index_name):
        # restrict searchable attributes
        self.client.index(index_name).update_searchable_attributes(['content'])
        filterable_attributes = ['last']
        if index_name not in MESSAGES_INDEXES:
            filterable_attributes.append('first')
        # filter by daterange
        self.client.index(index_name).update_filterable_attributes(filterable_attributes)
        # sort by date
        self.client.index(index_name).update_sortable_attributes(filterable_attributes)
        # result rank
        # Default:
        #     "words",      -> nb match terms
        #     "typo",       -> nb match typo
        #     "proximity",  -> short distance between terms
        #     "attribute",  -> most important attributes
        #     "sort",
        #     "exactness"
        self.client.index(index_name).update_ranking_rules(
            ['sort', 'words', 'typo', 'proximity', 'attribute', 'exactness'])

    def setup_indexes_searchable_filterable_sortable(self):
        for index_name in get_indexes_names():
            self.setup_index_searchable_filterable_sortable(index_name)

    # replacing existing documents
    def add(self, index, document):
        self.client.index(index).add_documents([document], primary_key='uuid')

    def update(self, index, document):
        self.client.index(index).update_documents([document], primary_key='uuid')

    def remove(self, index, doc_id):
        self.client.index(index).delete_document(doc_id)

    def _delete(self, index):
        # self.client.index(index).delete_all_documents()
        self.client.delete_index(index)

    def _delete_all(self):
        indexes = self.client.get_indexes()
        for index in indexes["results"]:
            index.delete()
        delete_crawled_content_domains_items()

    def get_stats(self):
        return self.client.get_all_stats()

    def index_obj(self, index, obj, timestamp):
        document = obj.get_search_document(timestamp)
        if document:
            self.update(index, document)

    ## INDEX ##
    def index_crawled_item(self, domain, item, timestamp):
        content = item.get_html2text_content()
        cid = sha256(content.encode()).hexdigest()
        index = domain.get_domain_type()
        # update
        if r_search.exists(f'crawled:{index}:{cid}'):
            document = {'uuid': cid, 'last': timestamp}
            self.update(index, document)
        # new content
        else:
            r_search.sadd(f'crawled:{index}:contents', cid)
            document = {'uuid': cid, 'content': content, 'last': timestamp}
            self.add(index, document)
        r_search.hset(f'crawled:{index}:{cid}', domain.id, item.id)

    def index_chat_message(self, message):
        index = f'c{message.get_protocol()}'
        timestamp = message.get_timestamp()
        chat_instance = message.get_chat_instance()
        chat = chats_viewer.get_obj_chat('chat', chat_instance, message.get_chat_id())
        user_account = message.get_user_account()
        self.index_obj(index, chat, timestamp)
        self.index_obj(index, user_account, timestamp)
        self.index_obj(index, message, timestamp)


if IS_MEILISEARCH_ENABLED:
    Engine = MeiliSearch()
else:
    Engine = None

#### INDEXER ####

## DOMAIN ##

def index_crawled_item(item):
    domain = Domains.Domain(item.get_domain())
    timestamp = domain.get_item_timestamp(item.id)
    if timestamp:
        Engine.index_crawled_item(domain, item, timestamp)
    # else: # TODO LOG


def _index_crawled_domain(dom_id):
    domain = Domains.Domain(dom_id)
    for timestamp in domain.get_timestamps_up():
        for item_id in domain.get_crawled_items_by_epoch(epoch=timestamp):
            item = Items.Item(item_id)
            if not item.exists():
                continue
            Engine.index_crawled_item(domain, item, timestamp)


def index_crawled():
    # multi process
    if not r_search.exists('to_index:crawled'):
        for domain_type in Domains.get_all_domains_types():
            for dom_id in Domains.get_domains_up_by_type(domain_type):
                r_search.sadd('to_index:crawled', dom_id)
    while True:
        dom_id = r_search.spop('to_index:crawled')
        if not dom_id:
            break
        _index_crawled_domain(dom_id)


## MESSAGE ##

def index_chats():
    for obj in chats_viewer.get_chats_iterator():
        index = f'c{obj.get_protocol()}'
        document = obj.get_search_document()
        if document:
            Engine.update(index, document)

def index_messages():
    for message in chats_viewer.get_messages_iterator():
        index = f'c{message.get_protocol()}'
        document = message.get_search_document()
        if document:
            Engine.update(index, document)

def index_user_accounts():
    for obj in UsersAccount.UserAccounts().get_iterator():
        index = f'c{obj.get_protocol()}'
        document = obj.get_search_document()
        if document:
            Engine.update(index, document)

## DESCRIPTION ##

def index_image_description(image):
    index = f'desc-img'
    document = image.get_search_document()
    if document:
        Engine.add(index, document)

def index_images_descriptions():
    for image in Images.get_all_images_objects():
        index_image_description(image)


def index_screenshot_description(screenshot):
    index = f'desc-screen'
    document = screenshot.get_search_document()
    if document:
        Engine.add(index, document)

def index_screenshots_descriptions():
    for screenshot in Screenshots.get_screenshots_obj_iterator():
        index_screenshot_description(screenshot)


def index_domain_description(domain_id):
    index = f'desc-dom'
    domain = Domains.Domain(domain_id)
    document = domain.get_search_description_document()
    if document:
        Engine.add(index, document)

def index_domains_descriptions():
    for dom_id in Domains.get_domains_up_by_type('onion'):
        index_domain_description(dom_id)
    for dom_id in Domains.get_domains_up_by_type('web'):
        index_domain_description(dom_id)


## TITLE ##  # TODO update only

def index_title(title_id):
    index = 'title'
    obj = Titles.Title(title_id)
    document = obj.get_search_document()
    if document:
        Engine.update(index, document)


def index_titles():
    index = 'title'
    for obj in Titles.Titles().get_iterator():
        document = obj.get_search_document()
        if document:
            Engine.update(index, document)


## FILENAME ##  # TODO update only

def index_file_name(obj_id):
    index = 'filename'
    obj = FilesNames.FileName(obj_id)
    document = obj.get_search_document()
    if document:
        Engine.update(index, document)


def index_file_names():
    index = 'filename'
    for obj in FilesNames.FilesNames().get_iterator():
        document = obj.get_search_document()
        if document:
            Engine.update(index, document)

## --INDEXER-- ##


def remove_document(index_name, obj_gid):
    Engine.remove(index_name, get_obj_uuid5(obj_gid))


def delete_index(index_name):
    Engine._delete(index_name)
    Engine.client.create_index(index_name, {'primaryKey': 'uuid'})

def log(user_id, index, to_search):
    logger.warning(f'{user_id} search: {index} - {to_search}')


#### PAGINATION ####

def sanityze_page(page):
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1
    return page

def _get_pagination_nb_first_last(pagination, nb_per_page):
    first = (pagination['page'] - 1) * nb_per_page
    last = first + nb_per_page
    if last > pagination['total']:
        last = pagination['total']
    if first == 0:
        first = 1
    return first, last

def extract_pagination_from_result(result, nb_per_page, page):
    if 'page' in result:
        pagination = {'page': result['page'], 'total': result['totalHits'], 'nb_pages': result['totalPages']}
    else:
        pagination = create_pagination_multiple_indexes(result['estimatedTotalHits'], nb_per_page, page)
    pagination['nb_first'], pagination['nb_last'] = _get_pagination_nb_first_last(pagination, nb_per_page)
    return pagination

def create_pagination_multiple_indexes(total, nb_per_page, page):
    pagination = {'page': page, 'total': total}
    pages = total / nb_per_page
    if pages.is_integer():
        pagination['nb_pages'] = int(pages)
    else:
        pagination['nb_pages'] = int(pages) + 1
    pagination['nb_first'], pagination['nb_last'] = _get_pagination_nb_first_last(pagination, nb_per_page)
    return pagination


## --PAGINATION-- ##

#### CRAWLED CONTENT ####

def get_crawled_content_domains_items(index, h):
    return r_search.hgetall(f'crawled:{index}:{h}')


def delete_crawled_content_domains_items():
    for index in Domains.get_all_domains_types():
        while True:
            c_id = r_search.spop(f'crawled:{index}:contents')
            if not c_id:
                break
            r_search.delete(f'crawled:{index}:{c_id}')
    r_search.delete('to_index:crawled')


#### API ####

def api_check_indexes(indexes):
    for index in indexes:
        if index not in INDEX_NAMES:
            return {"status": "error", "reason": f"Unknow index: {index}"}, 404
    return None, 200


def api_search(data):
    indexes = data.get("indexes")
    to_search = data.get("search")
    page = sanityze_page(data.get("page"))
    nb_per_page = 20
    user_id = data.get("user_id")
    log(user_id, str(indexes), to_search)

    r = api_check_indexes(indexes)
    if r[1] != 200:
        return r

    sort = data.get("sort", "recent")
    if sort != "best" and sort != "recent":
        return {"status": "error", "reason": "Invalid sort"}, 400

    timestamp_from = data.get("from")
    timestamp_to = data.get("to")

    if timestamp_from:
        try:
            timestamp_from = Date.convert_str_date_to_epoch(timestamp_from)
        except:
            return {"status": "error", "reason": "Invalid date from"}, 400
    if timestamp_to:
        try:
            timestamp_to = Date.convert_str_date_to_epoch(timestamp_to)
        except:
            return {"status": "error", "reason": "Invalid date from"}, 400

    result = Engine.search(indexes, to_search, page=page, nb=nb_per_page, timestamp_from=timestamp_from, sort=sort,
                           timestamp_to=timestamp_to)
    objs = []
    pagination = {}
    if result.get("hits"):
        pagination = extract_pagination_from_result(result, nb_per_page, page)
        for res in result['hits']:
            # crawled items
            if not res.get('id'):
                index = res['_federation']['indexUid']
                #
                domains_items = get_crawled_content_domains_items(index, res['uuid'])
                obj = Items.Item(domains_items[next(iter(domains_items))])
                meta = obj.get_meta(options={'url', 'crawler'})
                meta['domains_items'] = domains_items
            else:
                obj_type, subtype, obj_id = res['id'].split(':', 2)
                if obj_type == 'item':
                    obj = Items.Item(obj_id)
                    meta = obj.get_meta(options={'url'})
                elif obj_type == 'message':
                    message = Messages.Message(obj_id)
                    meta = message.get_meta(
                        options={'barcodes', 'files', 'files-names', 'forwarded_from', 'full_date', 'icon', 'images',
                                 'language', 'link', 'parent', 'parent_meta', 'protocol', 'qrcodes', 'reactions',
                                 'user-account'})
                    meta['protocol'] = chats_viewer.get_chat_protocol_meta(meta['protocol'])
                    # if meta.get('reply_to'):
                    #     print(meta['reply_to'])
                elif obj_type == 'chat':
                    obj = chats_viewer.get_obj_chat('chat', subtype, obj_id)
                    meta = obj.get_meta(options={'link', 'icon', 'info', 'nb_participants', 'protocol', 'tags_safe', 'username', 'usernames'})
                elif obj_type == 'user-account':
                    obj = UsersAccount.UserAccount(obj_id, subtype)
                    meta = obj.get_meta(options={'link', 'icon', 'info', 'nb_chats', 'protocol', 'tags_safe', 'username', 'usernames'})
                elif obj_type == 'image':
                    obj = Images.Image(obj_id)
                    meta = obj.get_meta(options={'link', 'tags_safe'})
                elif obj_type == 'screenshot':
                    obj = Screenshots.Screenshot(obj_id)
                    meta = obj.get_meta(options={'link', 'tags_safe'})
                elif obj_type == 'domain':
                    obj = Domains.Domain(obj_id)
                    meta = obj.get_meta(options={'link', 'tags_safe'})
                elif obj_type == 'file-name':
                    obj = FilesNames.FileName(obj_id)
                    meta = obj.get_meta(options={'link'})
                elif obj_type == 'title':
                    obj = Titles.Title(obj_id)
                    meta = obj.get_meta(options={'link'})
                else:
                    print('ERROR UNKNOWN OBJ RESULT', res)
                    continue  # TODO ERROR

            meta['result'] = res['_formatted']['content']
            objs.append(meta)
    return (objs, pagination), 200

## --API-- ##

### SEARCH
# Limitation: The maximum number of terms taken into account for each search query is 10.
# If a search query includes more than 10 words, all words after the 10th will be ignored.

### INDEX
# .index(index_name).update_documents([doc])  # partial update -> keep old filed
# .index(index_name).add_documents() -> delete old fields
# .swap_indexes -> update index without interruption

### delete
# client.index('movies').delete_all_documents()
# .index('movies').delete_document(25684)


if __name__ == '__main__':
    index_all()
    # delete_crawled_content_domains_items()
    # Engine.setup_indexes_searchable_filterable_sortable()
    # import json
    # print(json.dumps(Engine.get_stats(), indent=2))
    # data = {'indexes': ['filename', 'title'], 'user_id': 'admin@admin.test', 'search': 'stick'}
    # r = api_search(data)
    # print(r)
