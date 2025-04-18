#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import json
import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_user, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from  lib.ail_core import paginate_iterator
from lib.objects import GTrackers
from packages import Date

# ============ BLUEPRINT ============
objects_gtracker = Blueprint('objects_gtracker', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/gtracker'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

# ============ FUNCTIONS ============
def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============
@objects_gtracker.route("/objects/gtrackers", methods=['GET'])
@login_required
@login_read_only
def objects_gtrackers():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = GTrackers.GTrackers().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("GtrackerDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)

@objects_gtracker.route("/objects/gtracker/post", methods=['POST'])
@login_required
@login_read_only
def objects_gtrackers_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_gtracker.objects_gtrackers', date_from=date_from, date_to=date_to, show_objects=show_objects))

@objects_gtracker.route("/objects/gtracker/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_gtracker_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(GTrackers.GTrackers().api_get_chart_nb_by_daterange(date_from, date_to))

@objects_gtracker.route("/objects/gtracker/search_post", methods=['POST'])
@login_required
@login_user
def objects_gtracker_search_post():
    to_search = request.form.get('to_search')
    search_type = request.form.get('search_type', 'id')
    case_sensitive = False
    page = request.form.get('page', 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    return redirect(
        url_for('objects_gtracker.objects_gtracker_search', search=to_search, page=page,
                search_type=search_type, case_sensitive=case_sensitive))

@objects_gtracker.route("/objects/gtracker/search", methods=['GET'])
@login_required
@login_user
def objects_gtracker_search():
    to_search = request.args.get('search')
    type_to_search = request.args.get('search_type', 'id')
    case_sensitive=False
    page = request.args.get('page', 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    gtrackers = GTrackers.GTrackers()

    if type_to_search == 'id':
        if len(type_to_search) == 64:
            gtracker = GTrackers.GTracker(to_search)
            if not gtracker.exists():
                abort(404)
            else:
                return redirect(gtracker.get_link(flask_context=True))
        else:
            search_result = gtrackers.search_by_id(to_search, r_pos=True, case_sensitive=case_sensitive)
    elif type_to_search == 'content':
        search_result = gtrackers.search_by_content(to_search, r_pos=True, case_sensitive=case_sensitive)
    else:
        return create_json_response({'error': 'Unknown search type'}, 400)

    if search_result:
        ids = sorted(search_result.keys())
        dict_page = paginate_iterator(ids, nb_obj=500, page=page)
        dict_objects = gtrackers.get_metas(dict_page['list_elem'], options={'sparkline'})
    else:
        dict_objects = {}
        dict_page = {}

    return render_template("search_gtracker_result.html", dict_objects=dict_objects, search_result=search_result,
                           dict_page=dict_page,
                           to_search=to_search, case_sensitive=case_sensitive, type_to_search=type_to_search)

