#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for tracked items
'''
import json
import redis
import datetime
import calendar
import flask
from flask import Flask, render_template, jsonify, request, Blueprint, url_for, redirect, Response, escape

from Role_Manager import login_admin, login_analyst
from flask_login import login_required, current_user

import re
from pprint import pprint
import Levenshtein

# ---------------------------------------------------------------

import Paste
import Term

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl
r_serv_term = Flask_config.r_serv_term
r_serv_cred = Flask_config.r_serv_cred
r_serv_db = Flask_config.r_serv_db
bootstrap_label = Flask_config.bootstrap_label

hunter = Blueprint('hunter', __name__, template_folder='templates')

# ============ FUNCTIONS ============

# ============ ROUTES ============

@hunter.route("/trackers")
@login_required
@login_analyst
def tracked_menu():
    user_id = current_user.get_id()
    user_term = Term.get_all_user_tracked_terms(user_id)
    global_term = Term.get_all_global_tracked_terms()
    return render_template("trackersManagement.html", user_term=user_term, global_term=global_term, bootstrap_label=bootstrap_label)

@hunter.route("/trackers/word")
@login_required
@login_analyst
def tracked_menu_word():
    filter_type = 'word'
    user_id = current_user.get_id()
    user_term = Term.get_all_user_tracked_terms(user_id, filter_type='word')
    global_term = Term.get_all_global_tracked_terms(filter_type='word')
    return render_template("trackersManagement.html", user_term=user_term, global_term=global_term, bootstrap_label=bootstrap_label, filter_type=filter_type)

@hunter.route("/trackers/set")
@login_required
@login_analyst
def tracked_menu_set():
    filter_type = 'set'
    user_id = current_user.get_id()
    user_term = Term.get_all_user_tracked_terms(user_id, filter_type=filter_type)
    global_term = Term.get_all_global_tracked_terms(filter_type=filter_type)
    return render_template("trackersManagement.html", user_term=user_term, global_term=global_term, bootstrap_label=bootstrap_label, filter_type=filter_type)

@hunter.route("/trackers/regex")
@login_required
@login_analyst
def tracked_menu_regex():
    filter_type = 'regex'
    user_id = current_user.get_id()
    user_term = Term.get_all_user_tracked_terms(user_id, filter_type=filter_type)
    global_term = Term.get_all_global_tracked_terms(filter_type=filter_type)
    return render_template("trackersManagement.html", user_term=user_term, global_term=global_term, bootstrap_label=bootstrap_label, filter_type=filter_type)


@hunter.route("/tracker/add", methods=['GET', 'POST'])
@login_required
@login_analyst
def add_tracked_menu():
    if request.method == 'POST':
        term = request.form.get("term")
        term_type  = request.form.get("tracker_type")
        nb_words = request.form.get("nb_word", 1)
        description = request.form.get("description", '')
        level = request.form.get("level", 0)
        tags = request.form.get("tags", [])
        mails = request.form.get("mails", [])

        if level == 'on':
            level = 1

        if mails:
            mails = mails.split()
        if tags:
            tags = tags.split()

        input_dict = {"term": term, "type": term_type, "nb_words": nb_words, "tags": tags, "mails": mails, "level": level, "description": description}
        user_id = current_user.get_id()
        res = Term.parse_json_term_to_add(input_dict, user_id)
        if res[1] == 200:
            return redirect(url_for('hunter.tracked_menu'))
        else:
            ## TODO: use modal
            return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
    else:
        return render_template("Add_tracker.html")

@hunter.route("/tracker/show_tracker")
@login_required
@login_analyst
def show_tracker():
    user_id = current_user.get_id()
    term_uuid = request.args.get('uuid', None)
    res = Term.check_term_uuid_valid_access(term_uuid, user_id)
    if res: # invalid access
        return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if date_from:
        date_from = date_from.replace('-', '')
    if date_to:
        date_to = date_to.replace('-', '')

    tracker_metadata = Term.get_term_metedata(term_uuid, user_id=True, level=True, description=True, tags=True, mails=True, sparkline=True)

    if date_from:
        res = Term.parse_get_tracker_term_item({'uuid': term_uuid, 'date_from': date_from, 'date_to': date_to}, user_id)
        if res[1] !=200:
            return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
        tracker_metadata['items'] = res[0]['items']
        tracker_metadata['date_from'] = res[0]['date_from']
        tracker_metadata['date_to'] = res[0]['date_to']
    else:
        tracker_metadata['items'] = []
        tracker_metadata['date_from'] = ''
        tracker_metadata['date_to'] = ''

    return render_template("showTracker.html", tracker_metadata=tracker_metadata, bootstrap_label=bootstrap_label)

@hunter.route("/tracker/update_tracker_description", methods=['POST'])
@login_required
@login_analyst
def update_tracker_description():
    user_id = current_user.get_id()
    term_uuid = request.form.get('uuid')
    res = Term.check_term_uuid_valid_access(term_uuid, user_id)
    if res: # invalid access
        return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
    description = escape( str(request.form.get('description', '')) )
    Term.replace_tracker_description(term_uuid, description)
    return redirect(url_for('hunter.show_tracker', uuid=term_uuid))

@hunter.route("/tracker/update_tracker_tags", methods=['POST'])
@login_required
@login_analyst
def update_tracker_tags():
    user_id = current_user.get_id()
    term_uuid = request.form.get('uuid')
    res = Term.check_term_uuid_valid_access(term_uuid, user_id)
    if res: # invalid access
        return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
    tags = request.form.get('tags')
    if tags:
        tags = tags.split()
    else:
        tags = []
    Term.replace_tracked_term_tags(term_uuid, tags)
    return redirect(url_for('hunter.show_tracker', uuid=term_uuid))

@hunter.route("/tracker/update_tracker_mails", methods=['POST'])
@login_required
@login_analyst
def update_tracker_mails():
    user_id = current_user.get_id()
    term_uuid = request.form.get('uuid')
    res = Term.check_term_uuid_valid_access(term_uuid, user_id)
    if res: # invalid access
        return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
    mails = request.form.get('mails')
    if mails:
        mails = mails.split()
    else:
        mails = []
    res = Term.replace_tracked_term_mails(term_uuid, mails)
    if res: # invalid mail
        return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
    return redirect(url_for('hunter.show_tracker', uuid=term_uuid))

@hunter.route("/tracker/delete", methods=['GET'])
@login_required
@login_analyst
def delete_tracker():
    user_id = current_user.get_id()
    term_uuid = request.args.get('uuid')
    res = Term.parse_tracked_term_to_delete({'uuid': term_uuid}, user_id)
    if res[1] !=200:
        return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
    return redirect(url_for('hunter.tracked_menu'))

@hunter.route("/tracker/get_json_tracker_stats", methods=['GET'])
@login_required
@login_analyst
def get_json_tracker_stats():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if date_from:
        date_from = date_from.replace('-', '')
    if date_to:
        date_to = date_to.replace('-', '')

    tracker_uuid = request.args.get('uuid')

    if date_from and date_to:
        res = Term.get_list_tracked_term_stats_by_day([tracker_uuid], date_from=date_from, date_to=date_to)
    else:
        res = Term.get_list_tracked_term_stats_by_day([tracker_uuid])
    return jsonify(res)

# ========= REGISTRATION =========
app.register_blueprint(hunter, url_prefix=baseUrl)
