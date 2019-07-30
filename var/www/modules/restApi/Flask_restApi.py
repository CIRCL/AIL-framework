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
import redis
import datetime

import Import_helper
import Item
import Paste
import Tag

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response
from flask_login import login_required

from functools import wraps

# ============ VARIABLES ============
import Flask_config


app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_cache = Flask_config.r_cache
r_serv_db = Flask_config.r_serv_db
r_serv_onion = Flask_config.r_serv_onion
r_serv_metadata = Flask_config.r_serv_metadata

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

def verify_user_role(role, token):
    user_id = r_serv_db.hget('user:tokens', token)
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

    try:
        authenticated = False
        if verify_token(token):
            authenticated = True

            # check user role
            if not verify_user_role(user_role, token):
                data = ({'status': 'error', 'reason': 'Access Forbidden'}, 403)

        if not authenticated:
            data = ({'status': 'error', 'reason': 'Authentication failed'}, 401)
    except Exception as e:
        print(e)
        data = ({'status': 'error', 'reason': 'Malformed Authentication String'}, 400)
    if data:
        return data
    else:
        return None

# ============ API CORE =============



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

@restApi.route("api/items", methods=['GET', 'POST'])
@token_required('admin')
def items():
    item = request.args.get('id')

    return Response(json.dumps({'test': 2}), mimetype='application/json')

@restApi.route("api/get/item/info/<path:item_id>", methods=['GET'])
@token_required('admin')
def get_item_id(item_id):
    """
        **GET api/get/item/info/<item id>**

        **Get item**

        This function allows user to get a specific item information through their item_id.

        :param id: id of the item
        :type id: item id
        :return: item's information in json and http status code

        - Example::

            curl -k https://127.0.0.1:7000/api/get/item/info/submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json"

        - Expected Success Response::

            HTTP Status Code: 200

            {
              "content": "item content test",
              "date": "20190726",
              "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
              "tags":
                [
                  "misp-galaxy:backdoor=\"Rosenbridge\"",
                  "infoleak:automatic-detection=\"pgp-message\"",
                  "infoleak:automatic-detection=\"encrypted-private-key\"",
                  "infoleak:submission=\"manual\"",
                  "misp-galaxy:backdoor=\"SLUB\""
                ]
            }

        - Expected Fail Response::

            HTTP Status Code: 400

            {'status': 'error', 'reason': 'Item not found'}

    """
    try:
        item_object = Paste.Paste(item_id)
    except FileNotFoundError:
        return Response(json.dumps({'status': 'error', 'reason': 'Item not found'}, indent=2, sort_keys=True), mimetype='application/json'), 400

    data = item_object.get_item_dict()
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json')

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
@restApi.route("api/get/item/tag/<path:item_id>", methods=['GET'])
@token_required('admin')
def get_item_tag(item_id):
    """
        **GET api/get/item/tag/<item id>**

        **Get item tags**

        This function allows user to get all items tags form a specified item id.

        :param id: id of the item
        :type id: item id
        :return: item's tags list in json and http status code

        - Example::

            curl -k https://127.0.0.1:7000/api/get/item/tag/submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json"

        - Expected Success Response::

            HTTP Status Code: 200

            {
              "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
              "tags":
                [
                  "misp-galaxy:backdoor=\"Rosenbridge\"",
                  "infoleak:automatic-detection=\"pgp-message\"",
                  "infoleak:automatic-detection=\"encrypted-private-key\"",
                  "infoleak:submission=\"manual\"",
                  "misp-galaxy:backdoor=\"SLUB\""
                ]
            }

        - Expected Fail Response::

            HTTP Status Code: 400

            {'status': 'error', 'reason': 'Item not found'}

    """
    if not Item.exist_item(item_id):
        return Response(json.dumps({'status': 'error', 'reason': 'Item not found'}, indent=2, sort_keys=True), mimetype='application/json'), 400
    tags = Tag.get_item_tags(item_id)
    dict_tags = {}
    dict_tags['id'] = item_id
    dict_tags['tags'] = tags
    return Response(json.dumps(dict_tags, indent=2, sort_keys=True), mimetype='application/json')

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
@restApi.route("api/add/item/tag", methods=['POST'])
@token_required('admin')
def add_item_tags():
    """
        **POST api/add/item/tag**

        **add tags to an item**

        This function allows user to add tags and galaxy to an item.

        :param id: id of the item
        :type id: item id
        :param tags: list of tags (default=[])
        :type tags: list
        :param galaxy: list of galaxy (default=[])
        :type galaxy: list

        :return: item id and tags added in json and http status code

        - Example::

            curl -k https://127.0.0.1:7000/api/add/item/tag --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST

        - input.json Example::

            {
              "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
              "tags": [
                        "infoleak:analyst-detection=\"private-key\"",
                        "infoleak:analyst-detection=\"api-key\""
                      ],
              "galaxy": [
                          "misp-galaxy:stealer=\"Vidar\""
                        ]
            }

        - Expected Success Response::

            HTTP Status Code: 200

            {
              "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
              "tags": [
                "infoleak:analyst-detection=\"private-key\"",
                "infoleak:analyst-detection=\"api-key\"",
                "misp-galaxy:stealer=\"Vidar\""
              ]
            }

        - Expected Fail Response::

            HTTP Status Code: 400

            {'status': 'error', 'reason': 'Item id not found'}
            {'status': 'error', 'reason': 'Tags or Galaxy not specified'}
            {'status': 'error', 'reason': 'Tags or Galaxy not enabled'}

    """
    data = request.get_json()
    if not data:
        return Response(json.dumps({'status': 'error', 'reason': 'Malformed JSON'}, indent=2, sort_keys=True), mimetype='application/json'), 400

    item_id = data.get('id', None)
    tags = data.get('tags', [])
    galaxy = data.get('galaxy', [])

    res = Tag.add_items_tag(tags, galaxy, item_id)
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
@restApi.route("api/delete/item/tag", methods=['DELETE'])
@token_required('admin')
def delete_item_tags():
    """
        **DELET E api/delete/item/tag**

        **delete tags from an item**

        This function allows user to delete tags and galaxy from an item.

        :param id: id of the item
        :type id: item id
        :param tags: list of tags (default=[])
        :type tags: list

        :return: item id and tags deleted in json and http status code

        - Example::

            curl -k https://127.0.0.1:7000/api/delete/item/tag --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X DELET E

        - input.json Example::

            {
              "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
              "tags": [
                        "infoleak:analyst-detection=\"private-key\"",
                        "infoleak:analyst-detection=\"api-key\"",
                        "misp-galaxy:stealer=\"Vidar\""
                      ]
            }

        - Expected Success Response::

            HTTP Status Code: 200

            {
              "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz",
              "tags": [
                "infoleak:analyst-detection=\"private-key\"",
                "infoleak:analyst-detection=\"api-key\"",
                 "misp-galaxy:stealer=\"Vidar\""
              ]
            }

        - Expected Fail Response::

            HTTP Status Code: 400

            {'status': 'error', 'reason': 'Item id not found'}
            {'status': 'error', 'reason': 'No Tag(s) specified}
            {'status': 'error', 'reason': 'Malformed JSON'}

    """
    data = request.get_json()
    if not data:
        return Response(json.dumps({'status': 'error', 'reason': 'Malformed JSON'}, indent=2, sort_keys=True), mimetype='application/json'), 400

    item_id = data.get('id', None)
    tags = data.get('tags', [])

    res = Tag.remove_item_tags(tags, item_id)
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
@restApi.route("api/get/item/content/<path:item_id>", methods=['GET'])
@token_required('admin')
def get_item_content(item_id):
    """
        **GET api/get/item/content/<item id>**

        **Get item content**

        This function allows user to get a specific item content.

        :param id: id of the item
        :type id: item id
        :return: item's content in json and http status code

        - Example::

            curl -k https://127.0.0.1:7000/api/get/item/content/submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json"

        - Expected Success Response::

            HTTP Status Code: 200

            {
              "content": "item content test",
              "id": "submitted/2019/07/26/3efb8a79-08e9-4776-94ab-615eb370b6d4.gz"
            }

        - Expected Fail Response::

            HTTP Status Code: 400

            {'status': 'error', 'reason': 'Item not found'}

    """
    try:
        item_object = Paste.Paste(item_id)
    except FileNotFoundError:
        return Response(json.dumps({'status': 'error', 'reason': 'Item not found'}, indent=2, sort_keys=True), mimetype='application/json'), 400
    item_object = Paste.Paste(item_id)
    dict_content = {}
    dict_content['id'] = item_id
    dict_content['content'] = item_object.get_p_content()
    return Response(json.dumps(dict_content, indent=2, sort_keys=True), mimetype='application/json')

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
@restApi.route("api/import/item", methods=['POST'])
@token_required('admin')
def import_item():
    """
        **POST api/import/item**

        **Import new item**

        This function allows user to import new items. asynchronous function.

        :param text: text to import
        :type text: str
        :param type: import type (default='text')
        :type type: "text"
        :param tags: list of tags (default=[])
        :type tags: list
        :param galaxy: list of galaxy (default=[])
        :type galaxy: list
        :param default_tags: add default tag (default=True)
        :type default_tags: boolean

        :return: imported uuid in json and http status code

        - Example::

            curl -k https://127.0.0.1:7000/api/import/item --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json" --data @input.json -X POST

        - input.json Example::

            {
              "type": "text",
              "tags": [
                        "infoleak:analyst-detection=\"private-key\""
                      ],
              "text": "text to import"
            }

        - Expected Success Response::

            HTTP Status Code: 200

            {
              "uuid": "0c3d7b34-936e-4f01-9cdf-2070184b6016"
            }

        - Expected Fail Response::

            HTTP Status Code: 400

            {'status': 'error', 'reason': 'Malformed JSON'}
            {'status': 'error', 'reason': 'No text supplied'}
            {'status': 'error', 'reason': 'Tags or Galaxy not enabled'}
            {'status': 'error', 'reason': 'Size exceeds default'}

    """
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
        return Response(json.dumps({'status': 'error', 'reason': 'Size exceeds default'}, indent=2, sort_keys=True), mimetype='application/json'), 400

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
@restApi.route("api/import/item/<UUID>", methods=['GET'])
@token_required('admin')
def import_item_uuid(UUID):
    """
        **GET api/import/item/<uuid4>**

        **Get import status and all items imported by uuid**

        This return the import status and a list of imported items.
        The full list of imported items is not complete until 'status'='imported'.

        :param uuid: import uuid
        :type uuid: uuid4
        :return: json: import status + imported items list

        - Example::

            curl -k https://127.0.0.1:7000/api/import/item/b20a69f1-99ad-4cb3-b212-7ce24b763b50 --header "Authorization: iHc1_ChZxj1aXmiFiF1mkxxQkzawwriEaZpPqyTQj " -H "Content-Type: application/json"

        - Expected Success Response::

            HTTP Status Code: 200

            {
              "items": [
                         "submitted/2019/07/26/b20a69f1-99ad-4cb3-b212-7ce24b763b50.gz"
                       ],
              "status": "in queue"/"in progress"/"imported"
            }

        - Expected Fail Response::

            HTTP Status Code: 400

            {'status': 'error', 'reason': 'Invalid uuid'}
            {'status': 'error', 'reason': 'Unknow uuid'}

    """

    # Verify uuid
    if not is_valid_uuid_v4(UUID):
        return Response(json.dumps({'status': 'error', 'reason': 'Invalid uuid'}), mimetype='application/json'), 400

    data = Import_helper.check_import_status(UUID)
    if data:
        return Response(json.dumps(data[0]), mimetype='application/json'), data[1]

    return Response(json.dumps({'status': 'error', 'reason': 'Invalid response'}), mimetype='application/json'), 400

# ========= REGISTRATION =========
app.register_blueprint(restApi, url_prefix=baseUrl)
