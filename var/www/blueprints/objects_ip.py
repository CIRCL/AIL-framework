#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import json
import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_user, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from  lib.ail_core import paginate_iterator
from lib.objects import IPAddresses
from packages import Date
from lib import search_engine

# ============ BLUEPRINT ============
objects_ip = Blueprint('objects_ip', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/ip'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

# ============ FUNCTIONS ============
def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============
@objects_ip.route("/objects/ips", methods=['GET'])
@login_required
@login_read_only
def objects_ips():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = IPAddresses.IPs().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("IPDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)

@objects_ip.route("/objects/ip/post", methods=['POST'])
@login_required
@login_read_only
def objects_ips_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_ip.objects_ips', date_from=date_from, date_to=date_to, show_objects=show_objects))

@objects_ip.route("/objects/ip/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_ip_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(IPAddresses.IPs().api_get_chart_nb_by_daterange(date_from, date_to))

# @objects_ip.route("/objects/ssh_key/search_post", methods=['POST'])
# @login_required
# @login_user
# def objects_ssh_key_search_post():
#     to_search = request.form.get('to_search')
#     page = request.form.get('page', 1)
#     try:
#         page = int(page)
#     except (TypeError, ValueError):
#         page = 1
#     return redirect(
#         url_for('objects_gtracker.objects_ssh_key_search', search=to_search, page=page))

# @objects_ip.route("/objects/ssh_key/search", methods=['GET'])
# @login_required
# @login_user
# def objects_ssh_key_search():
#     user_id = current_user.get_user_id()
#     to_search = request.args.get('search')
#     page = request.args.get('page', 1)
#     try:
#         page = int(page)
#     except (TypeError, ValueError):
#         page = 1
#
#     ssh_keys = SSHKeys.SSHKeys()
#     search_engine.log(user_id, 'ssh_key', to_search)
#     search_result = ssh_keys.search_by_content(to_search, r_pos=True, case_sensitive=False, regex=False)
#
#     if search_result:
#         ids = sorted(search_result.keys())
#         dict_page = paginate_iterator(ids, nb_obj=500, page=page)
#         dict_objects = ssh_keys.get_metas(dict_page['list_elem'], options={'sparkline'})
#     else:
#         dict_objects = {}
#         dict_page = {}
#
#     return render_template("search_ssh_key_result.html", dict_objects=dict_objects, search_result=search_result,
#                            dict_page=dict_page,
#                            to_search=to_search)

