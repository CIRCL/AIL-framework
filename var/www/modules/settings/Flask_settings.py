#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the settings modules page
'''
from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for
from flask_login import login_required, current_user

from Role_Manager import login_admin, login_analyst, login_user, login_read_only
from Role_Manager import create_user_db, edit_user_db, delete_user_db, check_password_strength, generate_new_token, gen_password

import json
import datetime

import git_status
import d4

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl
r_serv_db = Flask_config.r_serv_db
REPO_ORIGIN = Flask_config.REPO_ORIGIN
dict_update_description = Flask_config.dict_update_description
email_regex = Flask_config.email_regex

settings = Blueprint('settings', __name__, template_folder='templates')



# ============ FUNCTIONS ============
def one():
    return 1

def check_email(email):
    result = email_regex.match(email)
    if result:
        return True
    else:
        return False

def get_git_metadata():
    dict_git = {}
    dict_git['current_branch'] = git_status.get_current_branch()
    dict_git['is_clone'] = git_status.is_not_fork(REPO_ORIGIN)
    dict_git['is_working_directory_clean'] = git_status.is_working_directory_clean()
    dict_git['current_commit'] = git_status.get_last_commit_id_from_local()
    dict_git['last_remote_commit'] = git_status.get_last_commit_id_from_remote()
    dict_git['last_local_tag'] = git_status.get_last_tag_from_local()
    dict_git['last_remote_tag'] = git_status.get_last_tag_from_remote()

    if dict_git['current_commit'] != dict_git['last_remote_commit']:
        dict_git['new_git_update_available'] = True
    else:
        dict_git['new_git_update_available'] = False

    if dict_git['last_local_tag'] != dict_git['last_remote_tag']:
        dict_git['new_git_version_available'] = True
    else:
        dict_git['new_git_version_available'] = False

    return dict_git

def get_update_metadata():
    dict_update = {}
    dict_update['current_version'] = r_serv_db.get('ail:version')
    dict_update['current_background_update'] = r_serv_db.get('ail:current_background_update')
    dict_update['update_in_progress'] = r_serv_db.get('ail:update_in_progress')
    dict_update['update_error'] = r_serv_db.get('ail:update_error')

    if dict_update['update_in_progress']:
        dict_update['update_progression'] = r_serv_db.scard('ail:update_{}'.format(dict_update['update_in_progress']))
        dict_update['update_nb'] = dict_update_description[dict_update['update_in_progress']]['nb_background_update']
        dict_update['update_stat'] = int(dict_update['update_progression']*100/dict_update['update_nb'])
        dict_update['current_background_script'] = r_serv_db.get('ail:current_background_script')
        dict_update['current_background_script_stat'] = r_serv_db.get('ail:current_background_script_stat')

    return dict_update

def get_user_metadata(user_id):
    user_metadata = {}
    user_metadata['email'] = user_id
    user_metadata['role'] = r_serv_db.hget('user_metadata:{}'.format(user_id), 'role')
    user_metadata['api_key'] = r_serv_db.hget('user_metadata:{}'.format(user_id), 'token')
    return user_metadata

def get_users_metadata(list_users):
    users = []
    for user in list_users:
        users.append(get_user_metadata(user))
    return users

def get_all_users():
    return r_serv_db.hkeys('user:all')

def get_all_roles():
    return r_serv_db.zrange('ail:all_role', 0, -1)

# ============= ROUTES ==============

@settings.route("/settings/", methods=['GET'])
@login_required
@login_read_only
def settings_page():
    git_metadata = get_git_metadata()
    current_version = r_serv_db.get('ail:version')
    update_metadata = get_update_metadata()

    admin_level = current_user.is_in_role('admin')

    return render_template("settings_index.html", git_metadata=git_metadata,
                            admin_level=admin_level,
                            current_version=current_version)

@settings.route("/settings/edit_profile", methods=['GET'])
@login_required
@login_read_only
def edit_profile():
    user_metadata = get_user_metadata(current_user.get_id())
    admin_level = current_user.is_in_role('admin')
    return render_template("edit_profile.html", user_metadata=user_metadata,
                            admin_level=admin_level)

@settings.route("/settings/new_token", methods=['GET'])
@login_required
@login_user
def new_token():
    generate_new_token(current_user.get_id())
    return redirect(url_for('settings.edit_profile'))

@settings.route("/settings/new_token_user", methods=['POST'])
@login_required
@login_admin
def new_token_user():
    user_id = request.form.get('user_id')
    if r_serv_db.exists('user_metadata:{}'.format(user_id)):
        generate_new_token(user_id)
    return redirect(url_for('settings.users_list'))

@settings.route("/settings/create_user", methods=['GET'])
@login_required
@login_admin
def create_user():
    user_id = request.args.get('user_id')
    error = request.args.get('error')
    error_mail = request.args.get('error_mail')
    role = None
    if r_serv_db.exists('user_metadata:{}'.format(user_id)):
        role = r_serv_db.hget('user_metadata:{}'.format(user_id), 'role')
    else:
        user_id = None
    all_roles = get_all_roles()
    return render_template("create_user.html", all_roles=all_roles, user_id=user_id, user_role=role,
                                        error=error, error_mail=error_mail,
                                        admin_level=True)

@settings.route("/settings/create_user_post", methods=['POST'])
@login_required
@login_admin
def create_user_post():
    email = request.form.get('username')
    role = request.form.get('user_role')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    all_roles = get_all_roles()

    if email and len(email)< 300 and check_email(email) and role:
        if role in all_roles:
            # password set
            if password1 and password2:
                if password1==password2:
                    if check_password_strength(password1):
                        password = password1
                    else:
                        return render_template("create_user.html", all_roles=all_roles, error="Incorrect Password", admin_level=True)
                else:
                    return render_template("create_user.html", all_roles=all_roles, error="Passwords don't match", admin_level=True)
            # generate password
            else:
                password = gen_password()

            if current_user.is_in_role('admin'):
                # edit user
                if r_serv_db.exists('user_metadata:{}'.format(email)):
                    if password1 and password2:
                        edit_user_db(email, password=password, role=role)
                        return redirect(url_for('settings.users_list', new_user=email, new_user_password=password, new_user_edited=True))
                    else:
                        edit_user_db(email, role=role)
                        return redirect(url_for('settings.users_list', new_user=email, new_user_password='Password not changed', new_user_edited=True))
                # create user
                else:
                    create_user_db(email, password, default=True, role=role)
                    return redirect(url_for('settings.users_list', new_user=email, new_user_password=password, new_user_edited=False))

        else:
            return render_template("create_user.html", all_roles=all_roles, admin_level=True)
    else:
        return render_template("create_user.html", all_roles=all_roles, error_mail=True, admin_level=True)

@settings.route("/settings/users_list", methods=['GET'])
@login_required
@login_admin
def users_list():
    all_users = get_users_metadata(get_all_users())
    new_user = request.args.get('new_user')
    new_user_dict = {}
    if new_user:
        new_user_dict['email'] = new_user
        new_user_dict['edited'] = request.args.get('new_user_edited')
        new_user_dict['password'] = request.args.get('new_user_password')
    return render_template("users_list.html", all_users=all_users, new_user=new_user_dict, admin_level=True)

@settings.route("/settings/edit_user", methods=['POST'])
@login_required
@login_admin
def edit_user():
    user_id = request.form.get('user_id')
    return redirect(url_for('settings.create_user', user_id=user_id))

@settings.route("/settings/delete_user", methods=['POST'])
@login_required
@login_admin
def delete_user():
    user_id = request.form.get('user_id')
    delete_user_db(user_id)
    return redirect(url_for('settings.users_list'))


@settings.route("/settings/get_background_update_stats_json", methods=['GET'])
@login_required
@login_read_only
def get_background_update_stats_json():
    # handle :end, error
    update_stats = {}
    current_update = r_serv_db.get('ail:current_background_update')
    update_in_progress = r_serv_db.get('ail:update_in_progress')


    if current_update:
        update_stats['update_version']= current_update
        update_stats['background_name']= r_serv_db.get('ail:current_background_script')
        update_stats['background_stats']= r_serv_db.get('ail:current_background_script_stat')
        if update_stats['background_stats'] is None:
            update_stats['background_stats'] = 0
        else:
            update_stats['background_stats'] = int(update_stats['background_stats'])

        update_progression = r_serv_db.scard('ail:update_{}'.format(current_update))
        update_nb_scripts = dict_update_description[current_update]['nb_background_update']
        update_stats['update_stat'] = int(update_progression*100/update_nb_scripts)
        update_stats['update_stat_label'] = '{}/{}'.format(update_progression, update_nb_scripts)

        if not update_in_progress:
            update_stats['error'] = True
            error_message = r_serv_db.get('ail:update_error')
            if error_message:
                update_stats['error_message'] = error_message
            else:
                update_stats['error_message'] = 'Please relaunch the bin/update-background.py script'
        else:
            if update_stats['background_name'] is None:
                update_stats['error'] = True
                update_stats['error_message'] = 'Please launch the bin/update-background.py script'
            else:
                update_stats['error'] = False

        return jsonify(update_stats)

    else:
        return jsonify({})

@settings.route("/settings/passivedns", methods=['GET'])
@login_required
@login_read_only
def passive_dns():
    passivedns_enabled = d4.is_passive_dns_enabled()
    return render_template("passive_dns.html", passivedns_enabled=passivedns_enabled)

@settings.route("/settings/passivedns/change_state", methods=['GET'])
@login_required
@login_admin
def passive_dns_change_state():
    new_state = request.args.get('state') == 'enable'
    passivedns_enabled = d4.change_passive_dns_state(new_state)
    return redirect(url_for('settings.passive_dns'))

# ========= REGISTRATION =========
app.register_blueprint(settings, url_prefix=baseUrl)
