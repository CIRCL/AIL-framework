#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import Titles
from packages import Date

# ============ BLUEPRINT ============
objects_title = Blueprint('objects_title', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/title'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============
@objects_title.route("/objects/title", methods=['GET'])
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

@objects_title.route("/objects/title/search", methods=['POST'])
@login_required
@login_read_only
def objects_title_search():
    to_search = request.form.get('object_id')

    # TODO SANITIZE ID
    # TODO Search all
    title = Titles.Title(to_search)
    if not title.exists():
        abort(404)
    else:
        return redirect(title.get_link(flask_context=True))

# ============= ROUTES ==============

