#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the rest api
'''

import os
import re
import sys
import uuid
import json
import datetime

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects.Items import Item
from lib import Tag
from lib import Tracker

from packages import Term

from packages import Import_helper

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'import'))
import importer


from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, escape
from flask_login import login_required

from functools import wraps

# ============ VARIABLES ============
import Flask_config


app = Flask_config.app
baseUrl = Flask_config.baseUrl
r_cache = Flask_config.r_cache
r_serv_db = Flask_config.r_serv_db


restApi = Blueprint('restApi', __name__, template_folder='templates')

# ============ AUTH FUNCTIONS ============

def check_token_format(strg, search=re.compile(r'[^a-zA-Z0-9_-]').search):
    return not bool(search(strg))

def verify_token(token):
    if len(token) != 41:
        return False

    if not check_token_format(token):
        return False

    if r_serv_db.hexists('user:tokens', token):
        return True
    else:
        return False

def get_user_from_token(token):
    return r_serv_db.hget('user:tokens', token)

def verify_user_role(role, token):
    # User without API
    if role == 'user_no_api':
        return False

    user_id = get_user_from_token(token)
    if user_id:
        if is_in_role(user_id, role):
            return True
        else:
            return False
    else:
        return False

def is_in_role(user_id, role):
    if r_serv_db.sismember('user_role:{}'.format(role), user_id):
        return True
    else:
        return False

# ============ DECORATOR ============

def token_required(user_role):
    def actual_decorator(funct):
        @wraps(funct)
        def api_token(*args, **kwargs):
            data = authErrors(user_role)
            if data:
                return Response(json.dumps(data[0], indent=2, sort_keys=True), mimetype='application/json'), data[1]
            else:
                return funct(*args, **kwargs)
        return api_token
    return actual_decorator

def get_auth_from_header():
    token = request.headers.get('Authorization').replace(' ', '') # remove space
    return token

def authErrors(user_role):
    # Check auth
    if not request.headers.get('Authorization'):
        return ({'status': 'error', 'reason': 'Authentication needed'}, 401)
    token = get_auth_from_header()
    data = None
    # verify token format

    # brute force protection
    current_ip = request.remote_addr
    login_failed_ip = r_cache.get('failed_login_ip_api:{}'.format(current_ip))
    # brute force by ip
    if login_failed_ip:
        login_failed_ip = int(login_failed_ip)
        if login_failed_ip >= 5:
            return ({'status': 'error', 'reason': 'Max Connection Attempts reached, Please wait {}s'.format(r_cache.ttl('failed_login_ip_api:{}'.format(current_ip)))}, 401)

    try:
        authenticated = False
        if verify_token(token):
            authenticated = True

            # check user role
            if not verify_user_role(user_role, token):
                data = ({'status': 'error', 'reason': 'Access Forbidden'}, 403)

        if not authenticated:
            r_cache.incr('failed_login_ip_api:{}'.format(current_ip))
            r_cache.expire('failed_login_ip_api:{}'.format(current_ip), 300)
            data = ({'status': 'error', 'reason': 'Authentication failed'}, 401)
    except Exception as e:
        print(e)
        data = ({'status': 'error', 'reason': 'Malformed Authentication String'}, 400)
    if data:
        return data
    else:
        return None

# ============ API CORE =============

def create_json_response(data_dict, response_code):
    return Response(json.dumps(data_dict, indent=2, sort_keys=True), mimetype='application/json'), int(response_code)

def get_mandatory_fields(json_data, required_fields):
    for field in required_fields:
        if field not in json_data:
            return {'status': 'error', 'reason': 'mandatory field: {} not provided'.format(field)}, 400
    return None

# ============ FUNCTIONS ============

def is_valid_uuid_v4(header_uuid):
    try:
        header_uuid=header_uuid.replace('-', '')
        uuid_test = uuid.UUID(hex=header_uuid, version=4)
        return uuid_test.hex == header_uuid
    except:
        return False

def one():
    return 1

# ============= ROUTES ==============

# @restApi.route("/api", methods=['GET'])
# @login_required
# def api():
#     return 'api doc'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# POST
#
# {
#   "id": item_id,      mandatory
#   "content": true,
#   "tags": true,
#
#
# }
#
# response: {
#               "id": "item_id",
#               "tags": [],
#           }
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/get/item", methods=['POST'])
@token_required('read_only')
def get_item_id():
    data = request.get_json()
    res = Item.get_item(data)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/item/default", methods=['POST'])
@token_required('read_only')
def get_item_id_basic():

    data = request.get_json()
    item_id = data.get('id', None)
    req_data = {'id': item_id, 'date': True, 'content': True, 'tags': True}
    res = Item.get_item(req_data)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# GET
#
# {
#   "id": item_id,      mandatory
# }
#
# response: {
#               "id": "item_id",
#               "tags": [],
#           }
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/get/item/tag", methods=['POST'])
@token_required('read_only')
def get_item_tag():

    data = request.get_json()
    item_id = data.get('id', None)
    req_data = {'id': item_id, 'date': False, 'tags': True}
    res = Item.get_item(req_data)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# POST
#
# {
#   "id": item_id,      mandatory
#   "tags": [tags to add],
#   "galaxy": [galaxy to add],
# }
#
# response: {
#               "id": "item_id",
#               "tags": [tags added],
#           }
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/add/item/tag", methods=['POST'])
@token_required('analyst')
def add_item_tags():

    data = request.get_json()
    if not data:
        return Response(json.dumps({'status': 'error', 'reason': 'Malformed JSON'}, indent=2, sort_keys=True), mimetype='application/json'), 400

    object_id = data.get('id', None)
    tags = data.get('tags', [])
    galaxy = data.get('galaxy', [])

    # res = Tag.api_add_obj_tags(tags=tags, galaxy_tags=galaxy, object_id=object_id, object_type="item")
    res = {'error': 'disabled endpoint'}, 500
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# DELETE
#
# {
#   "id": item_id,      mandatory
#   "tags": [tags to delete],
# }
#
# response: {
#               "id": "item_id",
#               "tags": [tags deleted],
#           }
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/delete/item/tag", methods=['DELETE'])
@token_required('analyst')
def delete_item_tags():

    data = request.get_json()
    if not data:
        return Response(json.dumps({'status': 'error', 'reason': 'Malformed JSON'}, indent=2, sort_keys=True), mimetype='application/json'), 400

    object_id = data.get('id', None)
    tags = data.get('tags', [])

    res = Tag.api_delete_obj_tags(tags=tags, object_id=object_id, object_type="item")
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# GET
#
# {
#   "id": item_id,      mandatory
# }
#
# response: {
#               "id": "item_id",
#               "content": "item content"
#           }
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/get/item/content", methods=['POST'])
@token_required('read_only')
def get_item_content():
    data = request.get_json()
    item_id = data.get('id', None)
    req_data = {'id': item_id, 'date': False, 'content': True, 'tags': False}
    res = Item.get_item(req_data)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]


@restApi.route("api/v1/get/item/content/utf8/base64", methods=['POST'])
@token_required('read_only')
def get_item_content_encoded_text():
    data = request.get_json()
    item_id = data.get('id', None)
    req_data = {'id': item_id}
    res = Item.api_get_item_content_base64_utf8(req_data)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]


@restApi.route("api/v1/get/items/sources", methods=['GET'])
@token_required('read_only')
def get_item_sources():
    res = Item.api_get_items_sources()
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]



# @restApi.route("api/v1/get/item/source/check", methods=['POST'])
# @token_required('read_only')
# def get_check_item_source():
#     data = request.get_json()
#     source = data.get('source', None)
#     req_data = {'source': source}
#     res = Item.check_item_source(req_data)
#     return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # #        TAGS       # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

@restApi.route("api/v1/get/tag/metadata", methods=['POST'])
@token_required('read_only')
def get_tag_metadata():
    data = request.get_json()
    tag = data.get('tag', None)
    if not Tag.is_tag_in_all_tag(tag):
        return Response(json.dumps({'status': 'error', 'reason':'Tag not found'}, indent=2, sort_keys=True), mimetype='application/json'), 404
    metadata = Tag.get_tag_metadata(tag)
    return Response(json.dumps(metadata, indent=2, sort_keys=True), mimetype='application/json'), 200

@restApi.route("api/v1/get/tag/all", methods=['GET'])
@token_required('read_only')
def get_all_tags():
    res = {'tags': Tag.get_all_tags()}
    return Response(json.dumps(res, indent=2, sort_keys=True), mimetype='application/json'), 200

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # #        TRACKER       # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/add/tracker", methods=['POST'])
@token_required('analyst')
def add_tracker_term():
    data = request.get_json()
    user_token = get_auth_from_header()
    user_id = get_user_from_token(user_token)
    res = Tracker.api_add_tracker(data, user_id)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/delete/tracker", methods=['DELETE'])
@token_required('analyst')
def delete_tracker_term():
    data = request.get_json()
    user_token = get_auth_from_header()
    user_id = get_user_from_token(user_token)
    res = Term.parse_tracked_term_to_delete(data, user_id)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/tracker/item", methods=['POST'])
@token_required('read_only')
def get_tracker_term_item():
    data = request.get_json()
    user_token = get_auth_from_header()
    user_id = get_user_from_token(user_token)
    res = Term.parse_get_tracker_term_item(data, user_id)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]


@restApi.route("api/v1/get/tracker/yara/content", methods=['POST'])
@token_required('read_only')
def get_default_yara_rule_content():
    data = request.get_json()
    rule_name = data.get('rule_name', None)
    rule_name = escape(rule_name)
    req_data = {'rule_name': rule_name}
    res = Tracker.get_yara_rule_content_restapi(req_data)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/tracker/metadata", methods=['POST'])
@token_required('read_only')
def get_tracker_metadata_api():
    data = request.get_json()
    tracker_uuid = data.get('tracker_uuid', None)
    req_data = {'tracker_uuid': tracker_uuid}
    res = Tracker.get_tracker_metadata_api(req_data)
    return Response(json.dumps(res[0], indent=2, sort_keys=False), mimetype='application/json'), res[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # #        CRYPTOCURRENCY       # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/get/cryptocurrency/bitcoin/metadata", methods=['POST'])
@token_required('read_only')
def get_cryptocurrency_bitcoin_metadata():
    data = request.get_json()
    crypto_address = data.get('bitcoin', None)
    req_data = {'bitcoin': crypto_address, 'metadata': True}
    raise Exception('TO MIGRATE')
    res = 0
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/cryptocurrency/bitcoin/item", methods=['POST'])
@token_required('read_only')
def get_cryptocurrency_bitcoin_item():
    data = request.get_json()
    bitcoin_address = data.get('bitcoin', None)
    req_data = {'bitcoin': bitcoin_address, 'items': True}
    raise Exception('TO MIGRATE')
    res = 0
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # #       PGP       # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/get/pgp/key/metadata", methods=['POST'])
@token_required('read_only')
def get_pgp_key_metadata():
    data = request.get_json()
    pgp_field = data.get('key', None)
    req_data = {'key': pgp_field, 'metadata': True}
    raise Exception('TO MIGRATE')
    res = 0
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/pgp/mail/metadata", methods=['POST'])
@token_required('read_only')
def get_pgp_mail_metadata():
    data = request.get_json()
    pgp_field = data.get('mail', None)
    req_data = {'mail': pgp_field, 'metadata': True}
    raise Exception('TO MIGRATE')
    res = 0
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/pgp/name/metadata", methods=['POST'])
@token_required('read_only')
def get_pgp_name_metadata():
    data = request.get_json()
    pgp_field = data.get('name', None)
    req_data = {'name': pgp_field, 'metadata': True}
    raise Exception('TO MIGRATE')
    res = 0
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/pgp/key/item", methods=['POST'])
@token_required('read_only')
def get_pgp_key_item():
    data = request.get_json()
    pgp_field = data.get('key', None)
    req_data = {'key': pgp_field, 'items': True}
    res = 0
    raise Exception('TO MIGRATE')
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/pgp/mail/item", methods=['POST'])
@token_required('read_only')
def get_pgp_mail_item():
    data = request.get_json()
    pgp_mail = data.get('mail', None)
    req_data = {'mail': pgp_mail, 'items': True}
    raise Exception('TO MIGRATE')
    res = 0
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/pgp/name/item", methods=['POST'])
@token_required('read_only')
def get_pgp_name_item():
    data = request.get_json()
    pgp_name = data.get('name', None)
    req_data = {'name': pgp_name, 'items': True}
    raise Exception('TO MIGRATE')
    res = 0
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

'''



@restApi.route("api/v1/get/item/cryptocurrency/key", methods=['POST'])
@token_required('analyst')
def get_item_cryptocurrency_bitcoin():
    data = request.get_json()
    item_id = data.get('id', None)
    req_data = {'id': item_id, 'date': False, 'tags': False, 'pgp': {'key': True}}
    res = Item.get_item(req_data)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/item/pgp/mail", methods=['POST'])
@token_required('analyst')
def get_item_cryptocurrency_bitcoin():
    data = request.get_json()
    item_id = data.get('id', None)
    req_data = {'id': item_id, 'date': False, 'tags': False, 'pgp': {'mail': True}}
    res = Item.get_item(req_data)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

@restApi.route("api/v1/get/item/pgp/name", methods=['POST'])
@token_required('analyst')
def get_item_cryptocurrency_bitcoin():
    data = request.get_json()
    item_id = data.get('id', None)
    req_data = {'id': item_id, 'date': False, 'tags': False, 'pgp': {'name': True}}
    res = Item.get_item(req_data)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
'''

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # #        CRAWLER      # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/crawl/domain", methods=['POST'])
@token_required('analyst')
def crawl_domain():
    data = request.get_json()

    url = data.get('url', None)
    screenshot = data.get('screenshot', None)
    har = data.get('har', None)
    depth_limit = data.get('depth_limit', None)
    max_pages = data.get('max_pages', None)
    auto_crawler = data.get('auto_crawler', None)
    crawler_delta = data.get('crawler_delta', None)
    crawler_type = data.get('url', None)
    cookiejar_uuid = data.get('url', None)
    user_agent = data.get('url', None)

    res = crawlers.api_create_crawler_task(json_dict)
    res[0]['domain'] = domain
    return create_json_response(res[0], res[1])


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # #        DOMAIN       # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/get/domain/status/minimal", methods=['POST'])
@token_required('analyst')
def get_domain_status_minimal():
    data = request.get_json()
    domain = data.get('domain', None)
    # error handler
    # TODO TO MIGRATE
    raise Exception('TO MIGRATE')
    # res = Domain.api_verify_if_domain_exist(domain)
    if res:
        return create_json_response(res[0], res[1])
    # TODO TO MIGRATE
    raise Exception('TO MIGRATE')
    # res = Domain.api_get_domain_up_range(domain)
    res[0]['domain'] = domain
    return create_json_response(res[0], res[1])

@restApi.route("api/v1/get/crawled/domain/list", methods=['POST'])
@token_required('analyst')
def get_crawled_domain_list():
    data = request.get_json()
    res = get_mandatory_fields(data, ['date_from', 'date_to'])
    if res:
        return create_json_response(res[0], res[1])

    date_from = data.get('date_from', None)
    date_to = data.get('date_to', None)
    domain_type = data.get('domain_type', None)
    domain_status = 'UP'
    # TODO TO MIGRATE
    raise Exception('TO MIGRATE')
    # res = Domain.api_get_domains_by_status_daterange(date_from, date_to, domain_type)
    dict_res = res[0]
    dict_res['date_from'] = date_from
    dict_res['date_to'] = date_to
    dict_res['domain_status'] = domain_status
    dict_res['domain_type'] = domain_type
    return create_json_response(dict_res, res[1])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # #        IMPORT     # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# POST JSON FORMAT
#
# {
#   "type": "text",         (default value)
#   "tags": [],             (default value)
#   "default_tags": True,    (default value)
#   "galaxy" [],            (default value)
#   "text": "",             mandatory if type = text
# }
#
# response: {"uuid": "uuid"}
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/import/item", methods=['POST'])
@token_required('analyst')
def import_item():

    data = request.get_json()
    if not data:
        return Response(json.dumps({'status': 'error', 'reason': 'Malformed JSON'}, indent=2, sort_keys=True), mimetype='application/json'), 400

    # unpack json
    text_to_import = data.get('text', None)
    if not text_to_import:
        return Response(json.dumps({'status': 'error', 'reason': 'No text supplied'}, indent=2, sort_keys=True), mimetype='application/json'), 400

    tags = data.get('tags', [])
    if not type(tags) is list:
        tags = []
    galaxy = data.get('galaxy', [])
    if not type(galaxy) is list:
        galaxy = []

    if not Tag.is_valid_tags_taxonomies_galaxy(tags, galaxy):
        return Response(json.dumps({'status': 'error', 'reason': 'Tags or Galaxy not enabled'}, indent=2, sort_keys=True), mimetype='application/json'), 400

    default_tags = data.get('default_tags', True)
    if default_tags:
        tags.append('infoleak:submission="manual"')

    if sys.getsizeof(text_to_import) > 900000:
        return Response(json.dumps({'status': 'error', 'reason': 'Size exceeds default'}, indent=2, sort_keys=True), mimetype='application/json'), 413

    UUID = str(uuid.uuid4())
    Import_helper.create_import_queue(tags, galaxy, text_to_import, UUID)

    return Response(json.dumps({'uuid': UUID}, indent=2, sort_keys=True), mimetype='application/json')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# GET
#
# {
#   "uuid": "uuid",      mandatory
# }
#
# response: {
#               "status": "in queue"/"in progress"/"imported",
#               "items": [all item id]
#           }
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/get/import/item", methods=['POST'])
@token_required('analyst')
def import_item_uuid():
    data = request.get_json()
    UUID = data.get('uuid', None)

    # Verify uuid
    if not is_valid_uuid_v4(UUID):
        return Response(json.dumps({'status': 'error', 'reason': 'Invalid uuid'}), mimetype='application/json'), 400

    data = Import_helper.check_import_status(UUID)
    if data:
        return Response(json.dumps(data[0]), mimetype='application/json'), data[1]

    return Response(json.dumps({'status': 'error', 'reason': 'Invalid response'}), mimetype='application/json'), 400

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/import/json/item", methods=['POST'])
@token_required('user')
def import_json_item():

    data_json = request.get_json()
    res = importer.api_import_json_item(data_json)
    return Response(json.dumps(res[0]), mimetype='application/json'), res[1]


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # #        CORE       # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@restApi.route("api/v1/ping", methods=['GET'])
@token_required('read_only')
def v1_ping():
    return Response(json.dumps({'status': 'pong'}), mimetype='application/json'), 200

# ========= REGISTRATION =========
app.register_blueprint(restApi, url_prefix=baseUrl)
