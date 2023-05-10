#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
"""

import os
import sys
import json

from flask import render_template, jsonify, request, Blueprint, redirect, url_for, Response, escape
from flask_login import login_required, current_user, login_user, logout_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib.objects import ail_objects
from lib import item_basic
from lib import Tracker
from lib import Tag


bootstrap_label = Flask_config.bootstrap_label

# ============ BLUEPRINT ============
hunters = Blueprint('hunters', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/hunter'))

# ============ VARIABLES ============


# ============ FUNCTIONS ============
def api_validator(api_response):
    if api_response:
        return Response(json.dumps(api_response[0], indent=2, sort_keys=True), mimetype='application/json'), api_response[1]

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============

##################
#    TRACKERS    #
##################

@hunters.route('/trackers', methods=['GET'])
@login_required
@login_read_only
def trackers_dashboard():
    user_id = current_user.get_id()  # TODO
    trackers = Tracker.get_trackers_dashboard()
    stats = Tracker.get_trackers_stats(user_id)
    return render_template("trackers_dashboard.html", trackers=trackers, stats=stats, bootstrap_label=bootstrap_label)

@hunters.route("/trackers/all")
@login_required
@login_read_only
def tracked_menu():
    user_id = current_user.get_id()
    user_trackers = Tracker.get_user_trackers_meta(user_id)
    global_trackers = Tracker.get_global_trackers_meta()
    return render_template("trackersManagement.html", user_trackers=user_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label)

@hunters.route("/trackers/word")
@login_required
@login_read_only
def tracked_menu_word():
    tracker_type = 'word'
    user_id = current_user.get_id()
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type='word')
    global_trackers = Tracker.get_global_trackers_meta(tracker_type='word')
    return render_template("trackersManagement.html", user_trackers=user_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/trackers/set")
@login_required
@login_read_only
def tracked_menu_set():
    tracker_type = 'set'
    user_id = current_user.get_id()
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type=tracker_type)
    global_trackers = Tracker.get_global_trackers_meta(tracker_type=tracker_type)
    return render_template("trackersManagement.html", user_trackers=user_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/trackers/regex")
@login_required
@login_read_only
def tracked_menu_regex():
    tracker_type = 'regex'
    user_id = current_user.get_id()
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type=tracker_type)
    global_trackers = Tracker.get_global_trackers_meta(tracker_type=tracker_type)
    return render_template("trackersManagement.html", user_trackers=user_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/trackers/yara")
@login_required
@login_read_only
def tracked_menu_yara():
    tracker_type = 'yara'
    user_id = current_user.get_id()
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type=tracker_type)
    global_trackers = Tracker.get_global_trackers_meta(tracker_type=tracker_type)
    return render_template("trackersManagement.html", user_trackers=user_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/trackers/typosquatting")
@login_required
@login_read_only
def tracked_menu_typosquatting():
    tracker_type = 'typosquatting'
    user_id = current_user.get_id()
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type=tracker_type)
    global_trackers = Tracker.get_global_trackers_meta(tracker_type=tracker_type)
    return render_template("trackersManagement.html", user_trackers=user_trackers, global_trackers=global_trackers,
                           bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/tracker/add", methods=['GET', 'POST'])
@login_required
@login_analyst
def add_tracked_menu():
    if request.method == 'POST':
        to_track = request.form.get("tracker")
        tracker_uuid = request.form.get("tracker_uuid")
        tracker_type = request.form.get("tracker_type")
        nb_words = request.form.get("nb_word", 1)
        description = request.form.get("description", '')
        webhook = request.form.get("webhook", '')
        level = request.form.get("level", 0)
        mails = request.form.get("mails", [])

        # TAGS
        tags = request.form.get("tags", [])
        taxonomies_tags = request.form.get('taxonomies_tags')
        if taxonomies_tags:
            try:
                taxonomies_tags = json.loads(taxonomies_tags)
            except:
                taxonomies_tags = []
        else:
            taxonomies_tags = []
        galaxies_tags = request.form.get('galaxies_tags')
        if galaxies_tags:
            try:
                galaxies_tags = json.loads(galaxies_tags)
            except:
                galaxies_tags = []
        else:
            galaxies_tags = []
        # custom tags
        if tags:
            tags = tags.split()
        else:
            tags = []
        tags = tags + taxonomies_tags + galaxies_tags

        # YARA #
        if tracker_type == 'yara':
            yara_default_rule = request.form.get("yara_default_rule")
            yara_custom_rule = request.form.get("yara_custom_rule")
            if yara_custom_rule:
                to_track = yara_custom_rule
                tracker_type = 'yara_custom'
            else:
                to_track = yara_default_rule
                tracker_type = 'yara_default'

        if level == 'on':
            level = 1
        else:
            level = 0
        if mails:
            mails = mails.split()
        else:
            tags = []
            
        # FILTERS
        filters = {}
        for obj_type in Tracker.get_objects_tracked():
            new_filter = request.form.get(f'{obj_type}_obj')
            if new_filter == 'on':
                filters[obj_type] = {}
                # Mimetypes
                mimetypes = request.form.get(f'mimetypes_{obj_type}', [])
                if mimetypes:
                    mimetypes = json.loads(mimetypes)
                    filters[obj_type]['mimetypes'] = mimetypes
                # Sources
                sources = request.form.get(f'sources_{obj_type}', [])
                if sources:
                    sources = json.loads(sources)
                    filters[obj_type]['sources'] = sources
                # Subtypes
                for obj_subtype in ail_core.get_object_all_subtypes(obj_type):
                    subtype = request.form.get(f'filter_{obj_type}_{obj_subtype}')
                    if subtype == 'on':
                        if 'subtypes' not in filters[obj_type]:
                            filters[obj_type]['subtypes'] = []
                        filters[obj_type]['subtypes'].append(obj_subtype)

        input_dict = {"tracked": to_track, "type": tracker_type,
                      "tags": tags, "mails": mails, "filters": filters,
                      "level": level, "description": description, "webhook": webhook}
        if tracker_type == 'set':
            try:
                input_dict['nb_words'] = int(nb_words)
            except TypeError:
                input_dict['nb_words'] = 1

        user_id = current_user.get_id()
        res = Tracker.api_add_tracker(input_dict, user_id)
        if res[1] == 200:
            return redirect(url_for('hunters.trackers_dashboard'))
        else:
            return create_json_response(res[0], res[1])
    else:
        return render_template("tracker_add.html",
                                all_sources=item_basic.get_all_items_sources(r_list=True),
                                tags_selector_data=Tag.get_tags_selector_data(),
                                all_yara_files=Tracker.get_all_default_yara_files())

@hunters.route('/tracker/delete', methods=['GET'])
@login_required
@login_analyst
def tracker_delete():
    user_id = current_user.get_id()
    tracker_uuid = request.args.get('uuid')
    res = Tracker.api_delete_tracker({'uuid': tracker_uuid}, user_id)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    else:
        return redirect(url_for('hunter.tracked_menu'))


####################
#    RETRO HUNT    #
####################

@hunters.route('/retro_hunt/tasks', methods=['GET'])
@login_required
@login_read_only
def retro_hunt_all_tasks():
    retro_hunts = Tracker.get_retro_hunt_metas()
    return render_template("retro_hunt_tasks.html", retro_hunts=retro_hunts, bootstrap_label=bootstrap_label)

@hunters.route('/retro_hunt/task/show', methods=['GET'])
@login_required
@login_read_only
def retro_hunt_show_task():
    task_uuid = request.args.get('uuid', None)
    objs = request.args.get('objs', False)

    date_from_item = request.args.get('date_from')
    date_to_item = request.args.get('date_to')
    if date_from_item:
        date_from_item = date_from_item.replace('-', '')
    if date_to_item:
        date_to_item = date_to_item.replace('-', '')

    res = Tracker.api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return create_json_response(res[0], res[1])

    retro_hunt = Tracker.RetroHunt(task_uuid)
    dict_task = retro_hunt.get_meta(options={'creator', 'date', 'description', 'progress', 'filters', 'nb_objs', 'tags'})
    rule_content = Tracker.get_yara_rule_content(dict_task['rule'])
    dict_task['filters'] = json.dumps(dict_task['filters'], indent=4)

    if objs:
        dict_task['objs'] = ail_objects.get_objects_meta(retro_hunt.get_objs(), flask_context=True)
    else:
        dict_task['objs'] = []

    return render_template("show_retro_hunt.html", dict_task=dict_task,
                           rule_content=rule_content,
                           bootstrap_label=bootstrap_label)


@hunters.route('/retro_hunt/add', methods=['GET', 'POST'])
@login_required
@login_analyst
def retro_hunt_add_task():
    if request.method == 'POST':
        name = request.form.get("name", '')
        description = request.form.get("description", '')
        timeout = request.form.get("timeout", 30)
        # TAGS
        tags = request.form.get("tags", [])
        taxonomies_tags = request.form.get('taxonomies_tags')
        if taxonomies_tags:
            try:
                taxonomies_tags = json.loads(taxonomies_tags)
            except:
                taxonomies_tags = []
        else:
            taxonomies_tags = []
        galaxies_tags = request.form.get('galaxies_tags')
        if galaxies_tags:
            try:
                galaxies_tags = json.loads(galaxies_tags)
            except:
                galaxies_tags = []
        else:
            galaxies_tags = []
        # custom tags
        if tags:
            tags = tags.split()
            escaped_tags = []
            for tag in tags:
                escaped_tags.append(escape(tag))
            tags = escaped_tags
        else:
            tags = []
        tags = tags + taxonomies_tags + galaxies_tags
        # mails = request.form.get("mails", [])
        # if mails:
        #     mails = mails.split()

        # FILTERS
        filters = {}
        for obj_type in Tracker.get_objects_tracked():
            new_filter = request.form.get(f'{obj_type}_obj')
            if new_filter == 'on':
                filters[obj_type] = {}
                # Date From
                date_from = request.form.get(f'date_from_{obj_type}', '').replace('-', '')
                if date_from:
                    filters[obj_type]['date_from'] = date_from
                # Date to
                date_to = request.form.get(f'date_to_{obj_type}', '').replace('-', '')
                if date_to:
                    filters[obj_type]['date_to'] = date_to
                # Mimetypes
                mimetypes = request.form.get(f'mimetypes_{obj_type}', [])
                if mimetypes:
                    mimetypes = json.loads(mimetypes)
                    filters[obj_type]['mimetypes'] = mimetypes
                # Sources
                sources = request.form.get(f'sources_{obj_type}', [])
                if sources:
                    sources = json.loads(sources)
                    filters[obj_type]['sources'] = sources
                # Subtypes
                for obj_subtype in ail_core.get_object_all_subtypes(obj_type):
                    subtype = request.form.get(f'filter_{obj_type}_{obj_subtype}')
                    if subtype == 'on':
                        if 'subtypes' not in filters[obj_type]:
                            filters[obj_type]['subtypes'] = []
                        filters[obj_type]['subtypes'].append(obj_subtype)

        # YARA #
        yara_default_rule = request.form.get("yara_default_rule")
        yara_custom_rule =  request.form.get("yara_custom_rule")
        if yara_custom_rule:
            rule = yara_custom_rule
            rule_type='yara_custom'
        else:
            rule = yara_default_rule
            rule_type='yara_default'

        user_id = current_user.get_id()

        input_dict = {"name": name, "description": description, "creator": user_id,
                      "rule": rule, "type": rule_type,
                      "tags": tags, "filters": filters, "timeout": timeout,  # "mails": mails
                      }

        res = Tracker.api_create_retro_hunt_task(input_dict, user_id)
        if res[1] == 200:
            return redirect(url_for('hunters.retro_hunt_all_tasks'))
        else:
            ## TODO: use modal
            return create_json_response(res[0], res[1])
    else:
        return render_template("add_retro_hunt_task.html",
                               all_yara_files=Tracker.get_all_default_yara_files(),
                               tags_selector_data=Tag.get_tags_selector_data(),
                               items_sources=item_basic.get_all_items_sources(r_list=True))

@hunters.route('/retro_hunt/task/pause', methods=['GET'])
@login_required
@login_analyst
def retro_hunt_pause_task():
    task_uuid = request.args.get('uuid', None)
    res = Tracker.api_pause_retro_hunt_task(task_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('hunters.retro_hunt_all_tasks'))

@hunters.route('/retro_hunt/task/resume', methods=['GET'])
@login_required
@login_analyst
def retro_hunt_resume_task():
    task_uuid = request.args.get('uuid', None)
    res = Tracker.api_resume_retro_hunt_task(task_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('hunters.retro_hunt_all_tasks'))

@hunters.route('/retro_hunt/task/delete', methods=['GET'])
@login_required
@login_analyst
def retro_hunt_delete_task():
    task_uuid = request.args.get('uuid', None)
    res = Tracker.api_delete_retro_hunt_task(task_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('hunters.retro_hunt_all_tasks'))


##  - -  ##
