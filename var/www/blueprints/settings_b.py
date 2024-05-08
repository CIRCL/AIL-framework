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

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_updates
from lib import ail_users
from packages import git_status

# ============ BLUEPRINT ============
settings_b = Blueprint('settings_b', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/settings'))

# ============ VARIABLES ============
# bootstrap_label = Flask_config.bootstrap_label

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
    acl_admin = current_user.is_in_role('admin')
    return render_template("settings_index.html", git_metadata=git_metadata,
                           ail_version=ail_version, acl_admin=acl_admin)

@settings_b.route("/settings/background_update/json", methods=['GET'])
@login_required
@login_read_only
def get_background_update_metadata_json():
    return jsonify(ail_updates.get_update_background_meta(options={}))

@settings_b.route("/settings/modules", methods=['GET'])
@login_required
@login_read_only
def settings_modules():
    acl_admin = current_user.is_in_role('admin')
    return render_template("settings/modules.html", acl_admin=acl_admin)

@settings_b.route("/settings/user/profile", methods=['GET'])
@login_required
@login_read_only
def user_profile():
    acl_admin = current_user.is_in_role('admin')

@settings_b.route("/settings/new_user_api_key", methods=['GET'])
@login_required
@login_admin
def new_token_user():
    user_id = request.args.get('user_id')
    admin_id = current_user.get_user_id()
    r = ail_users.api_create_user_api_key(user_id, admin_id)
    if r[1] != 200:
        return create_json_response(r[0], r[1])
    else:
        return redirect(url_for('settings_b.users_list'))

@settings_b.route("/settings/delete_user", methods=['GET'])
@login_required
@login_admin
def delete_user():
    user_id = request.args.get('user_id')
    admin_id = current_user.get_user_id()
    r = ail_users.api_delete_user(user_id, admin_id)
    if r[1] != 200:
        return create_json_response(r[0], r[1])
    else:
        return redirect(url_for('settings_b.users_list'))

@settings_b.route("/settings/users", methods=['GET'])
@login_required
@login_admin
def users_list():
    meta = ail_users.api_get_users_meta()
    new_user = {}
    return render_template("users_list.html", meta=meta, new_user=new_user, acl_admin=True)






#############################################
