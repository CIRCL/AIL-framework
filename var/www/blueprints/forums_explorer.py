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
from lib import forums_viewer
from lib import Language
from lib import Tag
from lib import module_extractor
from lib import ail_users
from lib.objects import ail_objects
from lib import images_engine

# ============ BLUEPRINT ============
forums_explorer = Blueprint('forums_explorer', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/forums_explorer'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ FUNCTIONS ============

# ============= ROUTES ==============

@forums_explorer.route("chats/explorer/forums", methods=['GET'])
@login_required
@login_read_only
def forum_explorer_forums():
    forums = forums_viewer.api_get_forums_meta()
    return render_template('explorer_forums.html', forums=forums)


