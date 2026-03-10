#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
"""

import os
import sys
import json
import logging

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_read_only, login_user_no_api

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib import search_engine
from lib.objects import SSHKeys

logger = logging.getLogger()

# ============ BLUEPRINT ============
search_b = Blueprint('search_b', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/search'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

def log(user_id, index, to_search):
    logger.warning(f'{user_id} search: {index} - {to_search}')

# ============ FUNCTIONS ============

# ============= ROUTES ==============

@search_b.route("search", methods=['GET'])
@login_required
@login_read_only
def search_dashboard():
    user_id = current_user.get_user_id()
    search = request.args.get('q')
    indexes = request.args.get('scopes')
    if indexes:
        indexes_str = indexes
        indexes = indexes.split(',')
    else:
        indexes = []
        indexes_str = None

    last_seen_from = request.args.get('from')
    last_seen_to = request.args.get('to')

    page = request.args.get('page', 1)

    sort = request.args.get('sort', 'recent')

    # selected_scopes -> scope_human

    if search:
        r = search_engine.api_search({'indexes': indexes, 'search': search, 'page': page, 'user_id': user_id,
                                      'from': last_seen_from, 'to': last_seen_to, 'sort': sort})
        if r[1] != 200:
            return create_json_response(r[0], r[1])
        result, pagination = r[0]
    else:
        result = None
        pagination = None

    return render_template('search_dashboard.html',
                           bootstrap_label=bootstrap_label,
                           indexes_str=indexes_str,
                           selected_scopes=indexes,
                           to_search=search,
                           sort=sort,
                           last_seen_from=last_seen_from,
                           last_seen_to=last_seen_to,
                           result=result, pagination=pagination)

# username_subtypes=ail_core.get_object_all_subtypes('username')

@search_b.route("/search/advanced", methods=['GET'])
@login_required
@login_read_only
def search_advanced():
    return render_template('advanced_search.html',
                           username_subtypes=ail_core.get_object_all_subtypes('username'))

@search_b.route("/search/passivessh/host/ssh", methods=['GET', 'POST'])
@login_required
@login_read_only
def search_passivessh_host_ssh():
    if request.method == 'POST':
        search = request.form.get('search')
        return redirect(url_for('search_b.search_passivessh_host_ssh', search=search))
    else:
        user_id = current_user.get_user_id()
        search = request.args.get('search')
        # page = request.args.get('page', 1)

        log(user_id, 'ssh-host', search)
        r = SSHKeys.api_get_passive_ssh_host(search)
        result = json.dumps(r[0], indent=2)
        return render_template("search_passivessh.html",
                               to_search_host=search, result=result)

@search_b.route("/search/passivessh/host/history", methods=['GET', 'POST'])
@login_required
@login_read_only
def search_passivessh_host_history():
    if request.method == 'POST':
        search = request.form.get('search')
        return redirect(url_for('search_b.search_passivessh_host_history', search=search))
    else:
        user_id = current_user.get_user_id()
        search = request.args.get('search')
        # page = request.args.get('page', 1)

        log(user_id, 'ssh-history', search)
        r = SSHKeys.api_get_passive_ssh_host_history(search)
        result = json.dumps(r[0], indent=2)
        return render_template("search_passivessh.html",
                               to_search_history=search, result=result)

@search_b.route("/search/passivessh/fingerprint", methods=['GET', 'POST'])
@login_required
@login_read_only
def search_passivessh_fingerprint():
    if request.method == 'POST':
        search = request.form.get('search')
        return redirect(url_for('search_b.search_passivessh_fingerprint', search=search))
    else:
        user_id = current_user.get_user_id()
        search = request.args.get('search')
        # page = request.args.get('page', 1)

        log(user_id, 'ssh-fingerprint', search)
        r = SSHKeys.api_get_passive_ssh_fingerprint_hosts(search)
        result = json.dumps(r[0], indent=2)
        return render_template("search_passivessh.html",
                               to_search_fingerprint=search, result=result)
