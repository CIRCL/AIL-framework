#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import Cves
from packages import Date

# ============ BLUEPRINT ============
objects_cve = Blueprint('objects_cve', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/cve'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============
@objects_cve.route("/objects/cves", methods=['GET'])
@login_required
@login_read_only
def objects_cves():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = Cves.api_get_cves_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("CveDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)

@objects_cve.route("/objects/cve/post", methods=['POST'])
@login_required
@login_read_only
def objects_cves_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_cve.objects_cves', date_from=date_from, date_to=date_to, show_objects=show_objects))

@objects_cve.route("/objects/cve/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_cve_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(Cves.api_get_cves_range_by_daterange(date_from, date_to))

@objects_cve.route("/objects/cve/search", methods=['POST'])
@login_required
@login_read_only
def objects_cve_search():
    to_search = request.form.get('object_id')

    # TODO SANITIZE ID
    # TODO Search all
    cve = Cves.Cve(to_search)
    if not cve.exists():
        abort(404)
    else:
        return redirect(cve.get_link(flask_context=True))

@objects_cve.route("/objects/cve/graphline/json", methods=['GET'])
@login_required
@login_read_only
def objects_cve_graphline_json():
    cve_id = request.args.get('id')
    cve = Cves.Cve(cve_id)
    if not cve.exists():
        abort(404)
    return jsonify(Cves.get_cve_graphline(cve_id))

# ============= ROUTES ==============

