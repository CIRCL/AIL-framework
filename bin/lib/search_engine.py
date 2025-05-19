#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

import meilisearch

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects import Domains
from lib.objects import Items
from lib.objects import Messages
from lib import chats_viewer

config_loader = ConfigLoader()
IS_MEILISEARCH_ENABLED = config_loader.get_config_boolean('Indexer', 'meilisearch')
M_URL = config_loader.get_config_str('Indexer', 'meilisearch_url')
M_KEY = config_loader.get_config_str('Indexer', 'meilisearch_key')
config_loader = None

def is_meilisearch_enabled():
    return IS_MEILISEARCH_ENABLED


class MeiliSearch:
    def __init__(self):
        self.client = meilisearch.Client(M_URL, M_KEY)

    def search(self, indexes, query, nb=20, page=1):  # TODO filters, multisearch
        if len(indexes) == 1:
            return self.client.index(indexes[0]).search(query, {'attributesToSearchOn': ['content'], 'limit': nb, 'page': page,
                                                           'attributesToCrop': ['content'],
                                                           'attributesToHighlight': ['content'],
                                                           'highlightPreTag': '🔎⏩',
                                                           'highlightPostTag': '⏪🔍',
                                                           'cropLength': 100,
                                                           'showMatchesPosition': False
                                                           })
        else:
            end_query = []
            for index in indexes:
                end_query.append({'indexUid': index,
                              'q': query,
                              'attributesToSearchOn': ['content'],
                              'attributesToCrop': ['content'],
                              'attributesToHighlight': ['content'],
                              'highlightPreTag': '🔎⏩',
                              'highlightPostTag': '⏪🔍',
                              'cropLength': 100,
                              'showMatchesPosition': False
                              })
            return self.client.multi_search(end_query, {'limit': nb, 'offset': (page - 1) * nb})

    def get_indexes(self):
        return self.client.get_indexes()

    def _create_indexes(self):
        for index in ['cdiscord', 'ctelegram', 'cmatrix', 'tor', 'web']:  # TODO dynamic load of chat uuid ?
            self.client.create_index(index, {'primaryKey': 'uuid'})

    def add(self, index, document):
        self.client.index(index).add_documents([document], primary_key='uuid')

    def remove(self, index, doc_id):
        self.client.index(index).delete_document(doc_id)

    def _delete(self, index):
        self.client.index(index).delete_all_documents()

    def _delete_all(self):
        indexes = self.client.get_indexes()
        print(indexes)
        for index in indexes["results"]:
            index.delete()


if IS_MEILISEARCH_ENABLED:
    Engine = MeiliSearch()
else:
    Engine = None
##

def index_all():
    # Engine._delete_all()
    # Engine._delete('tor')
    # Engine._delete('web')
    Engine._create_indexes()
    index_crawled()
    index_chats_messages()

def _index_crawled_domain(dom_id):
    domain = Domains.Domain(dom_id)
    for item_id in domain.get_crawled_items_by_epoch():
        item = Items.Item(item_id)
        if not item.exists():
            continue
        if item.is_onion():
            index = 'tor'
        else:
            index = 'web'
        document = item.get_search_document()
        Engine.add(index, document)

def index_crawled():
    for dom_id in Domains.get_domains_up_by_type('onion'):
        _index_crawled_domain(dom_id)
    for dom_id in Domains.get_domains_up_by_type('web'):
        _index_crawled_domain(dom_id)

def index_message(message):
    index = f'c{message.get_protocol()}'
    document = message.get_search_document()
    if document:
        Engine.add(index, document)


# TODO index chat with description
# TODO index user-account description
def index_chats_messages():
    for message in chats_viewer.get_messages_iterator():
        index_message(message)


# def search(index, query, page=1, nb=20):
#     return Engine.search(index, query, page=page, nb=nb)

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
    last = first+ nb_per_page
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
    pages = total/nb_per_page
    if pages.is_integer():
        pagination['nb_pages'] = int(pages)
    else:
        pagination['nb_pages'] = int(pages) + 1
    pagination['nb_first'], pagination['nb_last'] = _get_pagination_nb_first_last(pagination, nb_per_page)
    return pagination

def api_search_crawled(data):
    index = data.get("index")
    to_search = data.get("search")
    page = sanityze_page(data.get("page"))
    nb_per_page = 20

    if not index or index not in ['tor', 'web', 'all']:
        return {"status": "error", "reason": "Invalid search index"}, 400
    if not to_search:
        return {"status": "error", "reason": "Invalid search query"}, 400

    # TODO SEARCH TITLE

    if index == 'all':
        indexes = ['tor', 'web']
    else:
        indexes = [index]

    result = Engine.search(indexes, to_search, page=page, nb=nb_per_page)
    objs = []
    pagination = {}
    # if isinstance(result['results'], dict):
    if result.get("hits"):
        pagination = extract_pagination_from_result(result, nb_per_page, page)
        for res in result['hits']:
            item = Items.Item(res['id'].split(':', 2)[2])
            meta = item.get_meta(options={'url'})
            meta['result'] = res['_formatted']['content']
            objs.append(meta)
    # else:
    #     total = 0
    #     for index in result['results']:
    #         total += index['totalHits']
    #         for res in index['hits']:
    #             item = Items.Item(res['id'].split(':', 2)[2])
    #             meta = item.get_meta(options={'url'})
    #             meta['result'] = res['_formatted']['content']
    #             objs.append(meta)
    #     pagination = create_pagination_multiple_indexes(total, nb_per_page, page)
    return (objs, pagination), 200

def api_search_chats(data):
    index = data.get("index")
    to_search = data.get("search")
    page = sanityze_page(data.get("page"))
    nb_per_page = 20

    protocols = chats_viewer.get_chat_protocols()

    if index != 'all':
        if not index or index not in protocols:
            return {"status": "error", "reason": "Invalid search index"}, 400
        if not to_search:
            return {"status": "error", "reason": "Invalid search query"}, 400

    # TODO SEARCH CHATS + USERS DESCRIPTION + MESSAGES FORWARD

    indexes = []
    if index == 'all':
        for protocol in protocols:
            indexes.append(f'c{protocol}')
    else:
        indexes.append(f'c{index}')


    result = Engine.search(indexes, to_search, page=page, nb=nb_per_page)
    objs = []
    pagination = {}
    # if isinstance(result['results'], dict):
    if result.get("hits"):
        pagination = extract_pagination_from_result(result, nb_per_page, page)
        for res in result['hits']:
            message = Messages.Message(res['id'].split(':', 2)[2])
            meta = message.get_meta(options={'barcodes', 'files', 'files-names', 'forwarded_from', 'full_date', 'icon', 'images', 'language', 'link', 'parent', 'parent_meta', 'protocol', 'qrcodes', 'reactions', 'user-account'})
            meta['protocol'] = chats_viewer.get_chat_protocol_meta(meta['protocol'])
            if meta.get('reply_to'):
                print(meta['reply_to'])
            meta['result'] = res['_formatted']['content']
            objs.append(meta)
    return (objs, pagination), 200

### Filter
# use filters ???
# onion
# chat -> mention, forward, chat type ???

### SEARCH
# Limitation: The maximum number of terms taken into account for each search query is 10.
# If a search query includes more than 10 words, all words after the 10th will be ignored.
#
# multisearch -> search on multiple indexes ???
# single search for one index
#
# client.index('index').search('test)

### INDEX
# .index(index_name).update_documents([doc])  # partial update -> keep old filed
# .index(index_name).add_documents() -> delete old fields
# .index("misp-galaxy").update_filterable_attributes( ... )
# .swap_indexes -> update index without interruption

### delete
# client.index('movies').delete_all_documents()
# .index('movies').delete_document(25684)


if __name__ == '__main__':
    index_all()
    # print(search('ctelegram', 'test'))
