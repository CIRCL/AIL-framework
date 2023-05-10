#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for tracked items
'''
import os
import sys
import json
import flask
from flask import Flask, render_template, jsonify, request, Blueprint, url_for, redirect, Response, escape

from Role_Manager import login_admin, login_analyst, login_read_only
from flask_login import login_required, current_user

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import ail_objects
from lib import item_basic
from lib import Tracker
from lib import Tag
from packages import Date


# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl
bootstrap_label = Flask_config.bootstrap_label

hunter = Blueprint('hunter', __name__, template_folder='templates')

# ============ FUNCTIONS ============

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ ROUTES ============

@hunter.route("/tracker/edit", methods=['GET', 'POST'])
@login_required
@login_analyst
def edit_tracked_menu():
    user_id = current_user.get_id()
    tracker_uuid = request.args.get('uuid', None)

    res = Tracker.api_is_allowed_to_edit_tracker(tracker_uuid, user_id) # check if is author or admin
    if res[1] != 200: # invalid access
        return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

    tracker = Tracker.Tracker(tracker_uuid)
    dict_tracker = tracker.get_meta(options={'description', 'level', 'mails', 'sources', 'tags', 'user', 'webhook'})
    dict_tracker['tags'] = ' '.join(dict_tracker['tags'])
    dict_tracker['mails'] = ' '.join(dict_tracker['mails'])

    if dict_tracker['type'] == 'set':
        dict_tracker['tracker'], dict_tracker['nb_words'] = dict_tracker['tracker'].split(';')
        dict_tracker['tracker'] = dict_tracker['tracker'].replace(',', ' ')
    elif dict_tracker['type'] == 'yara': #is_valid_default_yara_rule
        if Tracker.is_default_yara_rule(dict_tracker['tracker']):
            dict_tracker['yara_file'] = dict_tracker['tracker'].split('/')
            dict_tracker['yara_file'] = dict_tracker['yara_file'][-2] + '/' + dict_tracker['yara_file'][-1]
            dict_tracker['content'] = None
        else:
            dict_tracker['yara_file'] = None
            dict_tracker['content'] = Tracker.get_yara_rule_content(dict_tracker['tracker'])

    return render_template("edit_tracker.html", dict_tracker=dict_tracker,
                                all_sources=item_basic.get_all_items_sources(r_list=True),
                                all_yara_files=Tracker.get_all_default_yara_files())

    ## TO EDIT
    # word
    # set of word + nb words
    # regex
    # yara custom
    # yara default ???? => allow edit ?

    #### EDIT SHow Trackers ??????????????????????????????????????????????????

@hunter.route("/tracker/show_tracker")
@login_required
@login_read_only
def show_tracker():
    user_id = current_user.get_id()
    tracker_uuid = request.args.get('uuid', None)
    res = Tracker.api_is_allowed_to_edit_tracker(tracker_uuid, user_id)
    if res[1] != 200: # invalid access
        return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if date_from:
        date_from = date_from.replace('-', '')
    if date_to:
        date_to = date_to.replace('-', '')

    tracker = Tracker.Tracker(tracker_uuid)
    meta = tracker.get_meta(options={'description', 'level', 'mails', 'filters', 'sparkline', 'tags',
                                     'user', 'webhook'})

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
        date_from, date_to = Date.sanitise_daterange(meta['first_seen'], meta['last_seen'])
        objs = tracker.get_objs_by_daterange(date_from, date_to)
        meta['objs'] = ail_objects.get_objects_meta(objs, flask_context=True)
    else:
        date_from = ''
        date_to = ''
        meta['objs'] = []

    meta['date_from'] = date_from
    meta['date_to'] = date_to
    print(meta['filters'])
    meta['item_sources'] = sorted(meta['filters'].get('item', {}).get('sources', []))
    # meta['filters'] = json.dumps(meta['filters'], indent=4)

    return render_template("showTracker.html", tracker_metadata=meta,
                           yara_rule_content=yara_rule_content,
                           typo_squatting=typo_squatting,
                           bootstrap_label=bootstrap_label)

@hunter.route("/tracker/update_tracker_description", methods=['POST'])
@login_required
@login_analyst
def update_tracker_description():
    user_id = current_user.get_id()
    term_uuid = request.form.get('uuid')
    res = Tracker.api_is_allowed_to_edit_tracker(term_uuid, user_id)
    if res[1] != 200: # invalid access
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
    res = Tracker.api_is_allowed_to_edit_tracker(term_uuid, user_id)
    if res[1] != 200: # invalid access
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
    res = Tracker.api_is_allowed_to_edit_tracker(term_uuid, user_id)
    if res[1] != 200: # invalid access
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

@hunter.route("/tracker/get_json_tracker_stats", methods=['GET'])
@login_required
@login_read_only
def get_json_tracker_stats():
    user_id = current_user.get_id()
    tracker_uuid = request.args.get('uuid')
    res = Tracker.api_check_tracker_acl(tracker_uuid, user_id)
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

@hunter.route("/tracker/yara/default_rule/content", methods=['GET'])
@login_required
@login_read_only
def get_default_yara_rule_content():
    default_yara_rule = request.args.get('rule_name')
    res = Tracker.api_get_default_rule_content(default_yara_rule)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]


# ========= REGISTRATION =========
app.register_blueprint(hunter, url_prefix=baseUrl)
