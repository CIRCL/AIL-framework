#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
"""

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_read_only, login_user_no_api

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib import search_engine
from lib import chats_viewer
# from lib import Language
# from lib import Tag
# from lib import module_extractor
# from lib.objects import ail_objects

# ============ BLUEPRINT ============
search_b = Blueprint('search_b', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/search'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ FUNCTIONS ============

# ============= ROUTES ==============

# @chats_explorer.route("/chats/explorer", methods=['GET'])
# @login_required
# @login_read_only
# def chats_explorer_dashboard():
#     return

@search_b.route("search", methods=['GET'])
@login_required
@login_read_only
def search_dashboard():
    protocols = chats_viewer.get_chat_protocols_meta()
    return render_template('search_dashboard.html', protocols=protocols,
                           username_subtypes=ail_core.get_object_all_subtypes('username'))


@search_b.route("/search/crawled/post", methods=['POST'])
@login_required
@login_read_only
def search_crawled_post():
    to_search = request.form.get('to_search')
    search_type = request.form.get('search_type_crawled')
    page = request.form.get('page', 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    return redirect(
        url_for('search_b.search_crawled', search=to_search, page=page, index=search_type))


@search_b.route("/search/crawled", methods=['GET'])
@login_required
@login_read_only
def search_crawled():
    search = request.args.get('search')
    index = request.args.get('index', 'tor')
    page = request.args.get('page', 1)

    r = search_engine.api_search_crawled({'index': index, 'search': search, 'page': page})
    if r[1] != 200:
        return create_json_response(r[0], r[1])

    result, pagination = r[0]

    # TODO icon eye + correlation

    return render_template("search_crawled.html", to_search=search, search_index=index,
                           bootstrap_label=bootstrap_label,
                           result=result, pagination=pagination)

@search_b.route("/search/chats/post", methods=['POST'])
@login_required
@login_read_only
def search_chats_post():
    to_search = request.form.get('to_search')
    search_type = request.form.get('search_type_chats')
    page = request.form.get('page', 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    return redirect(
        url_for('search_b.search_chats', search=to_search, page=page, index=search_type))


@search_b.route("/search/chats", methods=['GET'])
@login_required
@login_read_only
def search_chats():
    search = request.args.get('search')
    index = request.args.get('index', 'telegram')
    page = request.args.get('page', 1)

    r = search_engine.api_search_chats({'index': index, 'search': search, 'page': page})
    if r[1] != 200:
        return create_json_response(r[0], r[1])

    result, pagination = r[0]

    protocols = chats_viewer.get_chat_protocols_meta()
    return render_template("search_chats.html", protocols=protocols,
                           to_search=search, search_index=index,
                           bootstrap_label=bootstrap_label,
                           result=result, pagination=pagination)
