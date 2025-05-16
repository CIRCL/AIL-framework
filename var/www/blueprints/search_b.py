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
# from lib import chats_viewer
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
    return render_template('search_dashboard.html', username_subtypes=ail_core.get_object_all_subtypes('username'))


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
        url_for('search_b.search_crawled', search=to_search, page=page,
                index=search_type))


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

    # if search_result:
    #     dict_page = paginate_iterator(ids, nb_obj=500, page=page)
    #     dict_objects = mails.get_metas(dict_page['list_elem'], options={'sparkline'})
    # else:
    #     dict_objects = {}
    #     dict_page = {}
    #
    # return render_template("search_mail_result.html", dict_objects=dict_objects, search_result=search_result,
    #                        dict_page=dict_page,
    #                        to_search=to_search, case_sensitive=case_sensitive, type_to_search=type_to_search)
