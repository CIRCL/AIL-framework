#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the settings modules page
'''
from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for

import json
import datetime

import git_status

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_serv_db = Flask_config.r_serv_db
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal
REPO_ORIGIN = Flask_config.REPO_ORIGIN

settings = Blueprint('settings', __name__, template_folder='templates')



# ============ FUNCTIONS ============
def one():
    return 1

#def get_v1.5_update_tags_backgroud_status():
#    return '38%'

def get_git_metadata():
    dict_git = {}
    dict_git['current_branch'] = git_status.get_current_branch()
    dict_git['is_clone'] = git_status.is_not_fork(REPO_ORIGIN)
    dict_git['is_working_directory_clean'] = git_status.is_working_directory_clean()
    dict_git['current_commit'] = git_status.get_last_commit_id_from_local()
    dict_git['last_remote_commit'] = git_status.get_last_commit_id_from_remote()
    dict_git['last_local_tag'] = git_status.get_last_tag_from_local()
    dict_git['last_remote_tag'] = git_status.get_last_tag_from_remote()

    # # DEBUG:
    dict_git['last_local_tag'] = 'v1.3'
    dict_git['last_remote_commit'] = '234328439828943843839'

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

    dict_update['update_in_progress']='v1.5'

    return dict_update
# ============= ROUTES ==============

@settings.route("/settings/", methods=['GET'])
def settings_page():
    git_metadata = get_git_metadata()
    update_metadata = get_update_metadata()


    return render_template("settings_index.html", git_metadata=git_metadata,
                            update_metadata=update_metadata)

# ========= REGISTRATION =========
app.register_blueprint(settings, url_prefix=baseUrl)
