#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: ail_investigations
'''

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only

# sys.path.append('modules')
# import Flask_config

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_updates
from packages import git_status

# ============ BLUEPRINT ============
settings_b = Blueprint('settings_b', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/settings'))

# ============ VARIABLES ============
#bootstrap_label = Flask_config.bootstrap_label

# ============ FUNCTIONS ============
def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============

@settings_b.route("/settings", methods=['GET'])
@login_required
@login_read_only
def settings_page():
    git_metadata = git_status.get_git_metadata()
    ail_version = ail_updates.get_ail_version()
    #admin_level = current_user.is_in_role('admin')
    return render_template("settings_index.html", git_metadata=git_metadata,
                            ail_version=ail_version)

@settings_b.route("/settings/background_update/json", methods=['GET'])
@login_required
@login_read_only
def get_background_update_metadata_json():
    return jsonify(ail_updates.get_update_background_metadata())











#############################################
