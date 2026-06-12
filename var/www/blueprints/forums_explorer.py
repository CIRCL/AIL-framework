#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: Forum explorer endpoints.
"""

import os
import sys
import json

from flask import render_template, request, Blueprint, Response, abort
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import forums_viewer

# ============ BLUEPRINT ============
forums_explorer = Blueprint('forums_explorer', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/forums_explorer'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============

@forums_explorer.route("/chats/explorer/forums", methods=['GET'])
@login_required
@login_read_only
def forum_explorer_forums():
    forum_id = request.args.get('id')
    if forum_id:
        meta = forums_viewer.api_get_forum(forum_id)
        if meta[1] != 200:
            return create_json_response(meta[0], meta[1])
        # TODO CREATE OTHER TEMPLATE with NEW ENDPOINT
        return render_template('forums_explorer_forum.html', meta=meta[0], bootstrap_label=bootstrap_label)

    forums = forums_viewer.get_forums()
    return render_template('forums_explorer_index.html', forums=forums, bootstrap_label=bootstrap_label)


@forums_explorer.route("/chats/explorer/forum/subforum", methods=['GET'])
@login_required
@login_read_only
def forum_explorer_subforum():
    subtype = request.args.get('subtype')
    subforum_id = request.args.get('id')
    meta = forums_viewer.api_get_subforum(subtype, subforum_id)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    return render_template('forums_explorer_subforum.html', meta=meta[0], bootstrap_label=bootstrap_label)


@forums_explorer.route("/chats/explorer/forums/thread", methods=['GET'])
@login_required
@login_read_only
def forum_explorer_thread():
    subtype = request.args.get('subtype')
    thread_id = request.args.get('id')
    page = request.args.get('page')
    nb = request.args.get('nb')
    meta = forums_viewer.api_get_forum_thread(subtype, thread_id, page=page, nb=nb)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    return render_template('forums_explorer_thread.html', meta=meta[0], bootstrap_label=bootstrap_label)
