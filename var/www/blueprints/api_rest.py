#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
"""

import os
import sys
import json

from functools import wraps
from flask import request, Blueprint, Response

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_api
from lib import ail_core
from lib import ail_updates
from lib import ail_logger
from lib import crawlers
from lib import chats_viewer

from lib import Investigations
from lib import Tag

from lib.objects import ail_objects
from lib.objects import Domains
from lib.objects import Titles

from importer.FeederImporter import api_add_json_feeder_to_queue


# LOGS
# access_logger = ail_logger.get_access_config()


# ============ BLUEPRINT ============
api_rest = Blueprint('api_rest', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates'))


# ============ AUTH FUNCTIONS ============

def get_auth_from_header():
    token = request.headers.get('Authorization').replace(' ', '')  # remove space
    return token


def token_required(user_role):
    def actual_decorator(funct):
        @wraps(funct)
        def api_token(*args, **kwargs):
            # Check AUTH Header
            if not request.headers.get('Authorization'):
                return create_json_response({'status': 'error', 'reason': 'Authentication needed'}, 401)

            # Check Role
            if not user_role:
                return create_json_response({'status': 'error', 'reason': 'Invalid Role'}, 401)

            token = get_auth_from_header()
            ip_source = request.access_route[0]
            data, status_code = ail_api.authenticate_user(token, ip_address=ip_source)
            if status_code != 200:
                return create_json_response(data, status_code)
            elif data:
                # check user role
                if not ail_api.is_user_in_role(user_role, token):
                    return create_json_response({'status': 'error', 'reason': 'Access Forbidden'}, 403)
                else:
                    # User Authenticated + In Role
                    # print(funct.__name__)
                    return funct(*args, **kwargs)
            else:
                return create_json_response({'status': 'error', 'reason': 'Internal'}, 400)

        return api_token
    return actual_decorator


# ============ FUNCTIONS ============

def create_json_response(data, status_code):
    return Response(json.dumps(data) + "\n", mimetype='application/json'), status_code

# ============= ROUTES ==============

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # #        CORE       # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

@api_rest.route("api/v1/ping", methods=['GET'])
@token_required('user')
def v1_ping():
    return create_json_response({'status': 'pong'}, 200)

@api_rest.route("api/v1/uuid", methods=['GET'])
@token_required('user')
def v1_uuid():
    ail_uid = ail_core.get_ail_uuid()
    return create_json_response({'uuid': ail_uid}, 200)

@api_rest.route("api/v1/version", methods=['GET'])
@token_required('user')
def v1_version():
    version = ail_updates.get_ail_version()
    return create_json_response({'version': version}, 200)

@api_rest.route("api/v1/pyail/version", methods=['GET'])
@token_required('user')
def v1_pyail_version():
    ail_version = 'v1.0.0'
    return create_json_response({'version': ail_version}, 200)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # #      CRAWLERS       # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # TODO: ADD RESULT JSON Response
@api_rest.route("api/v1/add/crawler/task", methods=['POST'])  # TODO V2 Migration
@token_required('user')
def add_crawler_task():
    data = request.get_json()
    user_token = get_auth_from_header()
    user_org, user_id, _ = ail_api.get_basic_user_meta(user_token)
    res = crawlers.api_add_crawler_task(data, user_org, user_id=user_id)
    if res:
        return create_json_response(res[0], res[1])

    dict_res = {'url': data['url']}
    return create_json_response(dict_res, 200)


@api_rest.route("api/v1/add/crawler/capture", methods=['POST'])  # TODO V2 Migration
@token_required('user')
def add_crawler_capture():
    data = request.get_json()
    user_token = get_auth_from_header()
    user_id = ail_api.get_user_from_token(user_token)
    res = crawlers.api_add_crawler_capture(data, user_id)
    if res:
        return create_json_response(res[0], res[1])

    dict_res = {'url': data['url']}
    return create_json_response(dict_res, 200)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # #       IMPORTERS       # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@api_rest.route("api/v1/import/json/item", methods=['POST'])  # TODO V2 Migration
@token_required('user')
def import_json_item():
    data_json = request.get_json()
    res = api_add_json_feeder_to_queue(data_json)
    return Response(json.dumps(res[0]), mimetype='application/json'), res[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # #      OBJECTS      # # # # # # # # # # # # # # # # # # # TODO LIST OBJ TYPES + SUBTYPES
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
@api_rest.route("api/v1/object", methods=['GET'])  # TODO options
@token_required('user')
def v1_object():
    obj_gid = request.args.get('gid')
    if obj_gid:
        r = ail_objects.api_get_object_global_id(obj_gid)
    else:
        obj_type = request.args.get('type')
        obj_subtype = request.args.get('subtype')
        obj_id = request.args.get('id')
        r = ail_objects.api_get_object(obj_type, obj_subtype, obj_id)
    return create_json_response(r[0], r[1])


@api_rest.route("api/v1/obj/gid/<path:object_global_id>", methods=['GET'])  # TODO REMOVE ME ????
@token_required('user')
def v1_object_global_id(object_global_id):
    r = ail_objects.api_get_object_global_id(object_global_id)
    return create_json_response(r[0], r[1])

# @api_rest.route("api/v1/object/<object_type>/<object_subtype>/<path:object_id>", methods=['GET'])
@api_rest.route("api/v1/obj/<object_type>/<path:object_id>", methods=['GET'])  # TODO REMOVE ME ????
@token_required('user')
def v1_object_type_id(object_type, object_id):
    r = ail_objects.api_get_object_type_id(object_type, object_id)
    return create_json_response(r[0], r[1])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # #      CHATS      # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

@api_rest.route("api/v1/chat/messages", methods=['GET'])
@token_required('user')
def objects_chat_messages():
    obj_subtype = request.args.get('subtype')
    obj_id = request.args.get('id')
    r = chats_viewer.api_chat_messages(obj_subtype, obj_id)
    return create_json_response(r[0], r[1])

@api_rest.route("api/v1/chat-subchannel/messages", methods=['GET'])
@token_required('user')
def objects_chat_subchannel_messages():
    obj_subtype = request.args.get('subtype')
    obj_id = request.args.get('id')
    r = chats_viewer.api_subchannel_messages(obj_subtype, obj_id)
    return create_json_response(r[0], r[1])

@api_rest.route("api/v1/chat-thread/messages", methods=['GET'])
@token_required('user')
def objects_chat_thread_messages():
    obj_subtype = request.args.get('subtype')
    obj_id = request.args.get('id')
    r = chats_viewer.api_thread_messages(obj_subtype, obj_id)
    return create_json_response(r[0], r[1])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # #      DOMAINS      # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

@api_rest.route("api/v1/lookup/onion/<domain>", methods=['GET'])
@token_required('user')
def api_lookup_onion(domain):
    return create_json_response(crawlers.api_get_onion_lookup(domain), 200)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # #      TITLES       # # # # # # # # # # # # # # # # # # # TODO TO REVIEW
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

@api_rest.route("api/v1/titles/download", methods=['GET'])  # TODO RENAME ->api/v1/titles/domains
@token_required('user')
def objects_titles_download():
    return create_json_response(Titles.Titles().get_contents_ids(), 200)


# TODO
@api_rest.route("api/v1/titles/download/unsafe", methods=['GET'])  # TODO RENAME ->api/v1/titles/domains/unsafe
@token_required('user')
def objects_titles_download_unsafe():
    all_titles = {}
    unsafe_tags = Tag.unsafe_tags
    for tag in unsafe_tags:
        domains = Tag.get_tag_objects(tag, 'domain')
        for domain_id in domains:
            domain = Domains.Domain(domain_id)
            domain_titles = domain.get_correlation('title').get('title', [])
            for dt in domain_titles:
                title = Titles.Title(dt[1:])
                title_content = title.get_content()
                if title_content and title_content != 'None':
                    if title_content not in all_titles:
                        all_titles[title_content] = []
                    all_titles[title_content].append(domain.get_id())
    return Response(json.dumps(all_titles), mimetype='application/json'), 200

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # #      INVESTIGATIONS     # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

@api_rest.route("api/v1/investigation/<investigation_uuid>", methods=['GET'])  # TODO options
@token_required('user')
def v1_investigation(investigation_uuid):
    user_token = get_auth_from_header()
    user_org, user_id, user_role = ail_api.get_basic_user_meta(user_token)
    r = Investigations.api_get_investigation(user_org, user_id, user_role, investigation_uuid)
    return create_json_response(r[0], r[1])

# TODO CATCH REDIRECT
