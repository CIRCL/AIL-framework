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
from lib import d4
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
    user_id = current_user.get_user_id()
    acl_admin = current_user.is_in_role('admin')
    r = ail_users.api_get_user_profile(user_id)
    if r[1] != 200:
        return create_json_response(r[0], r[1])
    meta = r[0]
    return render_template("user_profile.html", meta=meta, acl_admin=acl_admin)

@settings_b.route("/settings/user/api_key/new", methods=['GET'])
@login_required
@login_read_only
def new_token_user_self():
    user_id = current_user.get_user_id()
    r = ail_users.api_create_user_api_key_self(user_id)
    if r[1] != 200:
        return create_json_response(r[0], r[1])
    else:
        return redirect(url_for('settings_b.user_profile'))

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

@settings_b.route("/settings/create_user", methods=['GET'])
@login_required
@login_admin
def create_user():
    user_id = request.args.get('user_id')
    error = request.args.get('error')
    error_mail = request.args.get('error_mail')
    meta = {}
    if user_id:
        r = ail_users.api_get_user_profile(user_id)
        if r[1] != 200:
            return create_json_response(r[0], r[1])
        meta = r[0]
    all_roles = ail_users.get_all_roles()
    return render_template("create_user.html", all_roles=all_roles, meta=meta,
                           error=error, error_mail=error_mail,
                           acl_admin=True)

@settings_b.route("/settings/edit_user", methods=['GET'])
@login_required
@login_admin
def edit_user():
    user_id = request.args.get('user_id')
    return redirect(url_for('settings_b.create_user', user_id=user_id))


@settings_b.route("/settings/create_user_post", methods=['POST'])
@login_required
@login_admin
def create_user_post():
    # Admin ID
    admin_id = current_user.get_user_id()

    email = request.form.get('username')
    role = request.form.get('user_role')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    all_roles = ail_users.get_all_roles()

    if email and len(email) < 300 and ail_users.check_email(email) and role:
        if role in all_roles:
            # password set
            if password1 and password2:
                if password1 == password2:
                    if ail_users.check_password_strength(password1):
                        password = password1
                    else:
                        return render_template("create_user.html", all_roles=all_roles, error="Incorrect Password", acl_admin=True)
                else:
                    return render_template("create_user.html", all_roles=all_roles, error="Passwords don't match", acl_admin=True)
            # generate password
            else:
                password = ail_users.gen_password()

            if current_user.is_in_role('admin'):
                str_password = password
                if ail_users.exists_user(email):
                    if not password1 and not password2:
                        password = None
                        str_password = 'Password not changed'
                ail_users.create_user(email, password=password, role=role)
                new_user = {'email': email, 'password': str_password}
                return render_template("create_user.html", new_user=new_user, meta={}, all_roles=all_roles, acl_admin=True)

        else:
            return render_template("create_user.html", all_roles=all_roles, acl_admin=True)
    else:
        return render_template("create_user.html", all_roles=all_roles, error_mail=True, acl_admin=True)



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
    return render_template("users_list.html", meta=meta, acl_admin=True)

#############################################

@settings_b.route("/settings/passivedns", methods=['GET'])
@login_required
@login_read_only
def passive_dns():
    passivedns_enabled = d4.is_passive_dns_enabled()
    return render_template("passive_dns.html", passivedns_enabled=passivedns_enabled)


@settings_b.route("/settings/passivedns/change_state", methods=['GET'])
@login_required
@login_admin
def passive_dns_change_state():
    new_state = request.args.get('state') == 'enable'
    passivedns_enabled = d4.change_passive_dns_state(new_state)
    return redirect(url_for('settings_b.passive_dns'))

# @settings.route("/settings/ail", methods=['GET'])
# @login_required
# @login_admin
# def ail_configs():
#     return render_template("ail_configs.html", passivedns_enabled=None)

