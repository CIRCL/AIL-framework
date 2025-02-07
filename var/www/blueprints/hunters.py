#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
"""

import os
import sys
import json

from flask import render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort
from flask_login import login_required, current_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import login_admin, login_org_admin, login_user, login_user_no_api, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib.objects import ail_objects
from lib import chats_viewer
from lib import item_basic
from lib import Tracker
from lib import Tag
from packages import Date


bootstrap_label = Flask_config.bootstrap_label

# ============ BLUEPRINT ============
hunters = Blueprint('hunters', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/hunter'))

# ============ VARIABLES ============


# ============ FUNCTIONS ============
def api_validator(api_response):
    if api_response:
        return Response(json.dumps(api_response[0], indent=2, sort_keys=True), mimetype='application/json'), api_response[1]

def create_json_response(data, status_code):
    if status_code == 403:
        abort(403)
    elif status_code == 404:
        abort(404)
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============

@hunters.route("/yara/rule/default/content", methods=['GET'])
@login_required
@login_read_only
def get_default_yara_rule_content():
    default_yara_rule = request.args.get('rule')
    res = Tracker.api_get_default_rule_content(default_yara_rule)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

##################
#    TRACKERS    #
##################

@hunters.route('/trackers', methods=['GET'])
@login_required
@login_read_only
def trackers_dashboard():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    trackers = Tracker.get_trackers_dashboard(user_org, user_id)
    for t in trackers:
        t['obj'] = ail_objects.get_obj_basic_meta(ail_objects.get_obj_from_global_id(t['obj']))
    stats = Tracker.get_trackers_stats(user_org, user_id)
    return render_template("trackers_dashboard.html", trackers=trackers, stats=stats, bootstrap_label=bootstrap_label)

@hunters.route("/trackers/all")
@login_required
@login_read_only
def tracked_menu():
    user_id = current_user.get_user_id()
    org_trackers = Tracker.get_org_trackers_meta(current_user.get_org())
    user_trackers = Tracker.get_user_trackers_meta(user_id)
    global_trackers = Tracker.get_global_trackers_meta()
    return render_template("trackersManagement.html", user_trackers=user_trackers, org_trackers=org_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label)

@hunters.route("/trackers/word")
@login_required
@login_read_only
def tracked_menu_word():
    tracker_type = 'word'
    user_id = current_user.get_user_id()
    org_trackers = Tracker.get_org_trackers_meta(current_user.get_org(), tracker_type='word')
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type='word')
    global_trackers = Tracker.get_global_trackers_meta(tracker_type='word')
    return render_template("trackersManagement.html", user_trackers=user_trackers, org_trackers=org_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/trackers/set")
@login_required
@login_read_only
def tracked_menu_set():
    tracker_type = 'set'
    user_id = current_user.get_user_id()
    org_trackers = Tracker.get_org_trackers_meta(current_user.get_org(), tracker_type=tracker_type)
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type=tracker_type)
    global_trackers = Tracker.get_global_trackers_meta(tracker_type=tracker_type)
    return render_template("trackersManagement.html", user_trackers=user_trackers, org_trackers=org_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/trackers/regex")
@login_required
@login_read_only
def tracked_menu_regex():
    tracker_type = 'regex'
    user_id = current_user.get_user_id()
    org_trackers = Tracker.get_org_trackers_meta(current_user.get_org(), tracker_type=tracker_type)
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type=tracker_type)
    global_trackers = Tracker.get_global_trackers_meta(tracker_type=tracker_type)
    return render_template("trackersManagement.html", user_trackers=user_trackers, org_trackers=org_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/trackers/yara")
@login_required
@login_read_only
def tracked_menu_yara():
    tracker_type = 'yara'
    user_id = current_user.get_user_id()
    org_trackers = Tracker.get_org_trackers_meta(current_user.get_org(), tracker_type=tracker_type)
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type=tracker_type)
    global_trackers = Tracker.get_global_trackers_meta(tracker_type=tracker_type)
    return render_template("trackersManagement.html", user_trackers=user_trackers, org_trackers=org_trackers, global_trackers=global_trackers, bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/trackers/typosquatting")
@login_required
@login_read_only
def tracked_menu_typosquatting():
    tracker_type = 'typosquatting'
    user_id = current_user.get_user_id()
    org_trackers = Tracker.get_org_trackers_meta(current_user.get_org(), tracker_type=tracker_type)
    user_trackers = Tracker.get_user_trackers_meta(user_id, tracker_type=tracker_type)
    global_trackers = Tracker.get_global_trackers_meta(tracker_type=tracker_type)
    return render_template("trackersManagement.html", user_trackers=user_trackers, org_trackers=org_trackers, global_trackers=global_trackers,
                           bootstrap_label=bootstrap_label, tracker_type=tracker_type)

@hunters.route("/trackers/admin")
@login_required
@login_admin
def tracked_menu_admin():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    org_trackers = Tracker.get_orgs_trackers_meta(user_org)
    user_trackers = Tracker.get_users_trackers_meta(user_id)
    return render_template("trackersManagement.html", user_trackers=user_trackers, org_trackers=org_trackers, global_trackers=[],
                           bootstrap_label=bootstrap_label)


@hunters.route("/tracker/show", methods=['GET', 'POST'])
@login_required
@login_read_only
def show_tracker():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    user_role = current_user.get_role()
    filter_obj_types = []

    if request.method == 'POST':
        tracker_uuid = request.form.get('tracker_uuid', None)
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        for obj_type in Tracker.get_objects_tracked():
            new_filter = request.form.get(f'{obj_type}_obj')
            if new_filter:
                filter_obj_types.append(obj_type)
        if sorted(filter_obj_types) == Tracker.get_objects_tracked():
            filter_obj_types = []
    else:
        tracker_uuid = request.args.get('uuid', None)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

    res = Tracker.api_check_tracker_acl(tracker_uuid, user_org, user_id, user_role, 'view')
    if res:  # invalid access
        return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

    if date_from:
        date_from = date_from.replace('-', '')
    if date_to:
        date_to = date_to.replace('-', '')

    tracker = Tracker.Tracker(tracker_uuid)
    meta = tracker.get_meta(options={'description', 'level', 'mails', 'org', 'org_name', 'filters', 'sparkline', 'tags',
                                     'user', 'webhooks', 'nb_objs'})

    if meta['type'] == 'yara':
        yara_rule_content = Tracker.get_yara_rule_content(meta['tracked'])
    else:
        yara_rule_content = None

    if meta['type'] == 'typosquatting':
        typo_squatting = Tracker.get_tracked_typosquatting_domains(meta['tracked'])
        sorted(typo_squatting)
    else:
        typo_squatting = set()

    if date_from:
        date_from, date_to = Date.sanitise_daterange(date_from, date_to)
        objs = tracker.get_objs_by_daterange(date_from, date_to, filter_obj_types)
        meta['objs'] = ail_objects.get_objects_meta(objs, options={'last_full_date'}, flask_context=True)
    else:
        date_from = ''
        date_to = ''
        meta['objs'] = []

    meta['date_from'] = date_from
    meta['date_to'] = date_to
    meta['item_sources'] = sorted(meta['filters'].get('item', {}).get('sources', []))
    if meta['filters']:
        meta['filters'] = json.dumps(meta['filters'], indent=4)

    return render_template("tracker_show.html", meta=meta,
                            rule_content=yara_rule_content,
                            typo_squatting=typo_squatting,
                            filter_obj_types=filter_obj_types,
                            bootstrap_label=bootstrap_label)

def parse_add_edit_request(request_form):
    to_track = request_form.get("tracker")
    tracker_uuid = request_form.get("tracker_uuid")
    tracker_type = request_form.get("tracker_type")
    nb_words = request_form.get("nb_word", 1)
    description = request.form.get("description", '')
    webhook = request_form.get("webhook", '')
    level = request_form.get("level", 0)
    mails = request_form.get("mails", [])

    # TAGS
    tags = request_form.get("tags", [])
    taxonomies_tags = request_form.get('taxonomies_tags')
    if taxonomies_tags:
        try:
            taxonomies_tags = json.loads(taxonomies_tags)
        except:
            taxonomies_tags = []
    else:
        taxonomies_tags = []
    galaxies_tags = request_form.get('galaxies_tags')
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
    escaped = []
    for tag in tags:
        escaped.append(tag)
    tags = escaped + taxonomies_tags + galaxies_tags

    # YARA #
    if tracker_type == 'yara':
        yara_default_rule = request_form.get("yara_default_rule")
        yara_custom_rule = request_form.get("yara_custom_rule")
        if yara_custom_rule:
            to_track = yara_custom_rule
            tracker_type = 'yara_custom'
        else:
            to_track = yara_default_rule
            tracker_type = 'yara_default'

    level = int(level)
    if mails:
        mails = mails.split()
    else:
        mails = []

    # FILTERS
    filters = {}
    for obj_type in Tracker.get_objects_tracked():
        new_filter = request_form.get(f'{obj_type}_obj')
        if new_filter == 'on':
            filters[obj_type] = {}
            # Mimetypes
            mimetypes = request_form.get(f'mimetypes_{obj_type}', [])
            if mimetypes:
                mimetypes = json.loads(mimetypes)
                filters[obj_type]['mimetypes'] = mimetypes
            # Sources
            sources = request_form.get(f'sources_{obj_type}', [])
            if sources:
                sources = json.loads(sources)
                filters[obj_type]['sources'] = sources
            excludes = request_form.get(f'sources_{obj_type}_exclude', [])
            if excludes:
                excludes = json.loads(excludes)
                filters[obj_type]['excludes'] = excludes
            # Subtypes
            for obj_subtype in ail_core.get_object_all_subtypes(obj_type):
                subtype = request_form.get(f'filter_{obj_type}_{obj_subtype}')
                if subtype == 'on':
                    if 'subtypes' not in filters[obj_type]:
                        filters[obj_type]['subtypes'] = []
                    filters[obj_type]['subtypes'].append(obj_subtype)

    input_dict = {"tracked": to_track, "type": tracker_type,
                  "tags": tags, "mails": mails, "filters": filters,
                  "level": level, "description": description, "webhook": webhook}
    if tracker_uuid:
        input_dict['uuid'] = tracker_uuid
    if tracker_type == 'set':
        try:
            input_dict['nb_words'] = int(nb_words)
        except (ValueError, TypeError):
            input_dict['nb_words'] = 1
    return input_dict

@hunters.route("/tracker/add", methods=['GET', 'POST'])
@login_required
@login_user_no_api
def add_tracked_menu():
    if request.method == 'POST':
        input_dict = parse_add_edit_request(request.form)
        user_id = current_user.get_user_id()
        org = current_user.get_org()
        res = Tracker.api_add_tracker(input_dict, org, user_id)
        if res[1] == 200:
            return redirect(url_for('hunters.trackers_dashboard'))
        else:
            return create_json_response(res[0], res[1])
    else:
        return render_template("tracker_add.html",
                               dict_tracker={},
                               all_sources=item_basic.get_all_items_sources(r_list=True),
                               tags_selector_data=Tag.get_tags_selector_data(),
                               all_yara_files=Tracker.get_all_default_yara_files())

@hunters.route("/tracker/edit", methods=['GET', 'POST'])
@login_required
@login_user_no_api
def tracker_edit():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    user_role = current_user.get_role()
    if request.method == 'POST':
        input_dict = parse_add_edit_request(request.form)
        res = Tracker.api_edit_tracker(input_dict, user_org, user_id, user_role)
        if res[1] == 200:
            return redirect(url_for('hunters.show_tracker', uuid=res[0].get('uuid')))
        else:
            return create_json_response(res[0], res[1])
    else:
        tracker_uuid = request.args.get('uuid', None)
        res = Tracker.api_check_tracker_acl(tracker_uuid, user_org, user_id, user_role, 'edit')
        if res:  # invalid access
            return create_json_response(res[0], res[1])

        tracker = Tracker.Tracker(tracker_uuid)
        dict_tracker = tracker.get_meta(options={'description', 'level', 'mails', 'filters', 'tags', 'webhooks'})
        if dict_tracker['type'] == 'yara':
            if not Tracker.is_default_yara_rule(dict_tracker['tracked']):
                dict_tracker['content'] = Tracker.get_yara_rule_content(dict_tracker['tracked'])
        elif dict_tracker['type'] == 'set':
            tracked, nb_words = dict_tracker['tracked'].rsplit(';', 1)
            tracked = tracked.replace(',', ' ')
            dict_tracker['tracked'] = tracked
            dict_tracker['nb_words'] = nb_words

        taxonomies_tags, galaxies_tags, custom_tags = Tag.sort_tags_taxonomies_galaxies_customs(dict_tracker['tags'])
        tags_selector_data = Tag.get_tags_selector_data()
        tags_selector_data['taxonomies_tags'] = taxonomies_tags
        tags_selector_data['galaxies_tags'] = galaxies_tags
        dict_tracker['tags'] = custom_tags
        return render_template("tracker_add.html",
                               dict_tracker=dict_tracker,
                               all_sources=item_basic.get_all_items_sources(r_list=True),
                               tags_selector_data=tags_selector_data,
                               all_yara_files=Tracker.get_all_default_yara_files())

@hunters.route('/tracker/delete', methods=['GET'])
@login_required
@login_user_no_api
def tracker_delete():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    user_role = current_user.get_role()
    tracker_uuid = request.args.get('uuid')
    res = Tracker.api_delete_tracker({'uuid': tracker_uuid}, user_org, user_id, user_role)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    else:
        return redirect(url_for('hunters.trackers_dashboard'))


@hunters.route("/tracker/graph/json", methods=['GET'])
@login_required
@login_read_only
def get_json_tracker_graph():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    user_role = current_user.get_role()
    tracker_uuid = request.args.get('uuid')
    res = Tracker.api_check_tracker_acl(tracker_uuid, user_org, user_id, user_role, 'view')
    if res:
        return create_json_response(res[0], res[1])

    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if date_from:
        date_from = date_from.replace('-', '')
    if date_to:
        date_to = date_to.replace('-', '')
    if date_from and date_to:
        res = Tracker.get_trackers_graph_by_day([tracker_uuid], date_from=date_from, date_to=date_to)
    else:
        res = Tracker.get_trackers_graph_by_day([tracker_uuid])
    return jsonify(res)

@hunters.route('/tracker/object/add', methods=['GET'])
@login_required
@login_user
def tracker_object_add():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    user_role = current_user.get_role()
    tracker_uuid = request.args.get('uuid')
    object_global_id = request.args.get('gid')
    if object_global_id.startswith('messages::'):
        obj = ail_objects.get_obj_from_global_id(object_global_id)
        date = obj.get_date()
    else:
        date = request.args.get('date')  # TODO check daterange
    res = Tracker.api_tracker_add_object({'uuid': tracker_uuid, 'gid': object_global_id, 'date': date}, user_org, user_id, user_role)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    else:
        if request.referrer:
            return redirect(request.referrer)
        else:
            return redirect(url_for('hunters.show_tracker', uuid=tracker_uuid))

@hunters.route('/tracker/object/remove', methods=['GET'])
@login_required
@login_user_no_api
def tracker_object_remove():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    user_role = current_user.get_role()
    tracker_uuid = request.args.get('uuid')
    object_global_id = request.args.get('gid')
    res = Tracker.api_tracker_remove_object({'uuid': tracker_uuid, 'gid': object_global_id}, user_org, user_id, user_role)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    else:
        if request.referrer:
            return redirect(request.referrer)
        else:
            return redirect(url_for('hunters.show_tracker', uuid=tracker_uuid))


@hunters.route('/tracker/objects', methods=['GET'])
@login_required
@login_admin
def tracker_objects():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    user_role = current_user.get_role()
    tracker_uuid = request.args.get('uuid', None)
    res = Tracker.api_check_tracker_acl(tracker_uuid, user_org, user_id, user_role, 'edit')
    if res:  # invalid access
        return create_json_response(res[0], res[1])

    tracker = Tracker.Tracker(tracker_uuid)
    meta = tracker.get_meta(options={'description', 'sparkline', 'tags', 'nb_objs'})
    if meta['type'] == 'yara':
        yara_rule_content = Tracker.get_yara_rule_content(meta['tracked'])
    else:
        yara_rule_content = None

    chats, messages = chats_viewer.get_message_report(tracker.get_objs())

    meta['date'] = Date.get_current_utc_full_time()

    return render_template("messages_report.html", meta=meta, yara_rule_content=yara_rule_content,
                           chats=chats, messages=messages, bootstrap_label=bootstrap_label)

    # TODO

    # Manual - Title
    #        - Summary

    # Messages table

    # Timeline messages by chats - line
    # pie charts NB messages all chats
    # Barchart NB messages by days

####################
#    RETRO HUNT    #
####################

@hunters.route('/retro_hunt/tasks', methods=['GET'])
@login_required
@login_read_only
def retro_hunt_all_tasks():
    user_org = current_user.get_org()
    retro_hunts_global = Tracker.get_retro_hunt_metas(Tracker.get_retro_hunts_global())
    retro_hunts_org = Tracker.get_retro_hunt_metas(Tracker.get_retro_hunts_org(user_org))
    return render_template("retro_hunt_tasks.html", retro_hunts_global=retro_hunts_global, retro_hunts_org=retro_hunts_org, bootstrap_label=bootstrap_label)

@hunters.route('/retro_hunt/tasks/admin', methods=['GET'])
@login_required
@login_admin
def retro_hunt_all_tasks_admin():
    retro_hunts_org = Tracker.get_retro_hunt_metas(Tracker.get_retro_hunts_orgs())
    return render_template("retro_hunt_tasks.html", retro_hunts_global=[], retro_hunts_org=retro_hunts_org, bootstrap_label=bootstrap_label)

@hunters.route('/retro_hunt/task/show', methods=['GET'])
@login_required
@login_read_only
def retro_hunt_show_task():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()

    task_uuid = request.args.get('uuid', None)
    objs = request.args.get('objs', False)

    # date_from_item = request.args.get('date_from')
    # date_to_item = request.args.get('date_to')
    # if date_from_item:
    #     date_from_item = date_from_item.replace('-', '')
    # if date_to_item:
    #     date_to_item = date_to_item.replace('-', '')

    res = Tracker.api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return create_json_response(res[0], res[1])
    retro_hunt = Tracker.RetroHunt(task_uuid)
    res = Tracker.api_check_retro_hunt_acl(retro_hunt, user_org, user_id, user_role, 'view')
    if res:
        return res

    dict_task = retro_hunt.get_meta(options={'creator', 'date', 'description', 'level', 'org', 'org_name', 'progress', 'filters', 'nb_objs', 'tags'})
    rule_content = Tracker.get_yara_rule_content(dict_task['rule'])
    dict_task['filters'] = json.dumps(dict_task['filters'], indent=4)

    if objs:
        dict_task['objs'] = ail_objects.get_objects_meta(retro_hunt.get_objs(), options={'last_full_date'}, flask_context=True)
    else:
        dict_task['objs'] = []

    return render_template("show_retro_hunt.html", dict_task=dict_task,
                           rule_content=rule_content,
                           bootstrap_label=bootstrap_label)


@hunters.route('/retro_hunt/add', methods=['GET', 'POST'])
@login_required
@login_user
def retro_hunt_add_task():
    if request.method == 'POST':
        level = request.form.get("level", 1)
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

        user_org = current_user.get_org()
        user_id = current_user.get_user_id()

        input_dict = {"level": level, "name": name, "description": description, "creator": user_id,
                      "rule": rule, "type": rule_type,
                      "tags": tags, "filters": filters, "timeout": timeout,  # "mails": mails
                      }

        res = Tracker.api_create_retro_hunt_task(input_dict, user_org, user_id)
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
@login_user
def retro_hunt_pause_task():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    task_uuid = request.args.get('uuid', None)
    res = Tracker.api_pause_retro_hunt_task(user_org, user_id, user_role, task_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('hunters.retro_hunt_all_tasks'))

@hunters.route('/retro_hunt/task/resume', methods=['GET'])
@login_required
@login_user
def retro_hunt_resume_task():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    task_uuid = request.args.get('uuid', None)
    res = Tracker.api_resume_retro_hunt_task(user_org, user_id, user_role, task_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('hunters.retro_hunt_all_tasks'))

@hunters.route('/retro_hunt/task/delete', methods=['GET'])
@login_required
@login_org_admin
def retro_hunt_delete_task():
    user_org = current_user.get_org()
    user_id = current_user.get_id()
    user_role = current_user.get_role()
    task_uuid = request.args.get('uuid', None)
    res = Tracker.api_delete_retro_hunt_task(user_org, user_id, user_role, task_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('hunters.retro_hunt_all_tasks'))


##  - -  ##
