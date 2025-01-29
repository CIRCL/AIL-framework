#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys

from flask import render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib.objects import FilesNames
from packages import Date

# ============ BLUEPRINT ============
objects_file_name = Blueprint('objects_file_name', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/file-name'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============
@objects_file_name.route("/objects/file-names", methods=['GET'])
@login_required
@login_read_only
def objects_files_names():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = FilesNames.FilesNames().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("FileNameDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)

@objects_file_name.route("/objects/file-name/post", methods=['POST'])
@login_required
@login_read_only
def objects_files_names_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_file_name.objects_files_names', date_from=date_from, date_to=date_to, show_objects=show_objects))

@objects_file_name.route("/objects/file-name/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_file_name_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(FilesNames.FilesNames().api_get_chart_nb_by_daterange(date_from, date_to))

@objects_file_name.route("/objects/file-nam/search", methods=['GET', 'POST'])
@login_required
@login_read_only
def objects_files_names_search():
    if request.method == 'POST':
        to_search = request.form.get('to_search')
        case_sensitive = bool(request.form.get('case_sensitive'))
        if case_sensitive:
            case_sensitive = 1
        else:
            case_sensitive = 0
        page = request.form.get('page', 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1
        return redirect(url_for('objects_file_name.objects_files_names_search', search=to_search, page=page, case_sensitive=case_sensitive))
    else:
        to_search = request.args.get('search')
        page = request.args.get('page', 1)
        case_sensitive = request.args.get('case_sensitive', False)
        if case_sensitive and case_sensitive != '0':
            case_sensitive = True
        else:
            case_sensitive = False
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1

        filenames = FilesNames.FilesNames()
        search_result = filenames.search_by_id(to_search, page, case_sensitive=case_sensitive)

        if search_result:
            ids = sorted(search_result.keys())
            dict_page = ail_core.paginate_iterator(ids, nb_obj=500, page=page)
            dict_objects = filenames.get_metas(dict_page['list_elem'], options={'icon', 'sparkline', 'uuid'})
        else:
            dict_objects = {}
            dict_page = {}

        return render_template("file-name/search_file_name_result.html", dict_objects=dict_objects, search_result=search_result,
                               dict_page=dict_page, case_sensitive=case_sensitive,
                               to_search=to_search)

# ============= ROUTES ==============

