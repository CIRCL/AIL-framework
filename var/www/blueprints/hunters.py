#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json
import random

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, make_response
from flask_login import login_required, current_user, login_user, logout_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import item_basic
from lib import Tracker


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

@hunters.route('/retro_hunt/tasks', methods=['GET'])
@login_required
@login_read_only
def retro_hunt_all_tasks():
    retro_hunts = Tracker.get_all_retro_hunt_tasks_with_metadata()
    return render_template("retro_hunt_tasks.html", retro_hunts=retro_hunts, bootstrap_label=bootstrap_label)

@hunters.route('/retro_hunt/task/show', methods=['GET'])
@login_required
@login_read_only
def retro_hunt_show_task():
    task_uuid = request.args.get('uuid', None)

    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from:
        date_from = date_from.replace('-', '')
    if date_to:
        date_to = date_to.replace('-', '')

    res = Tracker.api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return create_json_response(res[0], res[1])

    dict_task = Tracker.get_retro_hunt_task_metadata(task_uuid, date=True, progress=True, creator=True,
                                                        sources=True, tags=True, description=True)
    rule_content = Tracker.get_yara_rule_content(dict_task['rule'])

    if date_from:
        res = Tracker.api_get_retro_hunt_items({'uuid': task_uuid, 'date_from': date_from, 'date_to': date_to})
        if res[1] != 200:
            return create_json_response(res[0], res[1])
        dict_task['items'] = res[0]['items']
        dict_task['date_from_input'] = res[0]['date_from']
        dict_task['date_to_input'] = res[0]['date_to']
    else:
        dict_task['items'] = []
        dict_task['date_from_input'] = dict_task['date_from']
        dict_task['date_to_input'] = dict_task['date_to']

    return render_template("show_retro_hunt.html", dict_task=dict_task,
                                    rule_content=rule_content,
                                    bootstrap_label=bootstrap_label)


@hunters.route('/retro_hunt/task/add', methods=['GET', 'POST'])
@login_required
@login_analyst
def retro_hunt_add_task():
    if request.method == 'POST':
        name = request.form.get("name", '')
        description = request.form.get("description", '')
        timeout = request.form.get("timeout", 30)
        tags = request.form.get("tags", [])
        if tags:
            tags = tags.split()
        # mails = request.form.get("mails", [])
        # if mails:
        #     mails = mails.split()

        sources = request.form.get("sources", [])
        if sources:
            sources = json.loads(sources)

        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        if date_from:
            date_from = date_from.replace('-', '')
        if date_to:
            date_to = date_to.replace('-', '')

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
                        "tags": tags, "sources": sources, "timeout": timeout, #"mails": mails,
                        "date_from": date_from, "date_to": date_to}

        res = Tracker.api_create_retro_hunt_task(input_dict, user_id)
        if res[1] == 200:
            return redirect(url_for('hunters.retro_hunt_all_tasks'))
        else:
            ## TODO: use modal
            return create_json_response(res[0], res[1])
    else:
        return render_template("add_retro_hunt_task.html",
                                all_yara_files=Tracker.get_all_default_yara_files(),
                                all_sources=item_basic.get_all_items_sources(r_list=True))

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


#### JSON ####

@hunters.route("/tracker/get_json_retro_hunt_nb_items_by_date", methods=['GET'])
@login_required
@login_read_only
def get_json_retro_hunt_nb_items_by_date():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if date_from:
        date_from = date_from.replace('-', '')
    if date_to:
        date_to = date_to.replace('-', '')

    task_uuid = request.args.get('uuid')

    if date_from and date_to:
        res = Tracker.get_retro_hunt_nb_item_by_day([task_uuid], date_from=date_from, date_to=date_to)
    else:
        res = Tracker.get_retro_hunt_nb_item_by_day([task_uuid])
    return jsonify(res)


##  - -  ##
