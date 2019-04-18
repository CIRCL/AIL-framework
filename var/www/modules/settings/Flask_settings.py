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
dict_update_description = Flask_config.dict_update_description

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
# ============= ROUTES ==============

@settings.route("/settings/", methods=['GET'])
def settings_page():
    git_metadata = get_git_metadata()
    current_version = r_serv_db.get('ail:version')
    update_metadata = get_update_metadata()


    return render_template("settings_index.html", git_metadata=git_metadata,
                            current_version=current_version)


@settings.route("/settings/get_background_update_stats_json", methods=['GET'])
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

# ========= REGISTRATION =========
app.register_blueprint(settings, url_prefix=baseUrl)
