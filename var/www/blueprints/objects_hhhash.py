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
from lib.objects import HHHashs
from packages import Date

# ============ BLUEPRINT ============
objects_hhhash = Blueprint('objects_hhhash', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/hhhash'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============
@objects_hhhash.route("/objects/hhhashs", methods=['GET'])
@login_required
@login_read_only
def objects_hhhashs():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = HHHashs.HHHashs().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("HHHashDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)

@objects_hhhash.route("/objects/hhhash/post", methods=['POST'])
@login_required
@login_read_only
def objects_hhhashs_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_hhhash.objects_hhhashs', date_from=date_from, date_to=date_to, show_objects=show_objects))

@objects_hhhash.route("/objects/hhhash/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_hhhash_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(HHHashs.HHHashs().api_get_chart_nb_by_daterange(date_from, date_to))

# @objects_hhhash.route("/objects/hhhash/search", methods=['POST'])
# @login_required
# @login_read_only
# def objects_hhhashs_names_search():
#     to_search = request.form.get('object_id')
#
#     # TODO SANITIZE ID
#     # TODO Search all
#     cve = Cves.Cve(to_search)
#     if not cve.exists():
#         abort(404)
#     else:
#         return redirect(cve.get_link(flask_context=True))

# ============= ROUTES ==============

