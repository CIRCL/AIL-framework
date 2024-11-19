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
from lib.objects import Titles
from packages import Date

# ============ BLUEPRINT ============
objects_title = Blueprint('objects_title', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/title'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

# ============ FUNCTIONS ============
def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============
@objects_title.route("/objects/titles", methods=['GET'])
@login_required
@login_read_only
def objects_titles():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = Titles.Titles().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("TitleDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)

@objects_title.route("/objects/title/post", methods=['POST'])
@login_required
@login_read_only
def objects_titles_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_title.objects_titles', date_from=date_from, date_to=date_to, show_objects=show_objects))

@objects_title.route("/objects/title/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_title_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(Titles.Titles().api_get_chart_nb_by_daterange(date_from, date_to))

@objects_title.route("/objects/title/search_post", methods=['POST'])
@login_required
@login_user
def objects_title_search_post():
    to_search = request.form.get('to_search')
    search_type = request.form.get('search_type', 'id')
    case_sensitive = request.form.get('case_sensitive')
    case_sensitive = bool(case_sensitive)
    page = request.form.get('page', 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    return redirect(
        url_for('objects_title.objects_title_search', search=to_search, page=page,
                search_type=search_type, case_sensitive=case_sensitive))

@objects_title.route("/objects/title/search", methods=['GET'])
@login_required
@login_user
def objects_title_search():
    to_search = request.args.get('search')
    type_to_search = request.args.get('search_type', 'id')
    case_sensitive = request.args.get('case_sensitive')
    case_sensitive = bool(case_sensitive)
    page = request.args.get('page', 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    titles = Titles.Titles()

    if type_to_search == 'id':
        if len(type_to_search) == 64:
            title = Titles.Title(to_search)
            if not title.exists():
                abort(404)
            else:
                return redirect(title.get_link(flask_context=True))
        else:
            search_result = titles.search_by_id(to_search, r_pos=True, case_sensitive=case_sensitive)
    elif type_to_search == 'content':
        search_result = titles.search_by_content(to_search, r_pos=True, case_sensitive=case_sensitive)
    else:
        return create_json_response({'error': 'Unknown search type'}, 400)

    if search_result:
        ids = sorted(search_result.keys())
        dict_page = paginate_iterator(ids, nb_obj=500, page=page)
        dict_objects = titles.get_metas(dict_page['list_elem'], options={'sparkline'})
    else:
        dict_objects = {}
        dict_page = {}

    return render_template("search_title_result.html", dict_objects=dict_objects, search_result=search_result,
                           dict_page=dict_page,
                           to_search=to_search, case_sensitive=case_sensitive, type_to_search=type_to_search)

