#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys

from flask import render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import DomHashs
from packages import Date

# ============ BLUEPRINT ============
objects_dom_hash = Blueprint('objects_dom_hash', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/dom-hash'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============
@objects_dom_hash.route("/objects/dom-hashs", methods=['GET'])
@login_required
@login_read_only
def objects_dom_hashs():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = DomHashs.DomHashs().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("DomHashDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)

@objects_dom_hash.route("/objects/dom-hash/post", methods=['POST'])
@login_required
@login_read_only
def objects_dom_hashs_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_dom_hash.objects_dom_hashs', date_from=date_from, date_to=date_to, show_objects=show_objects))

@objects_dom_hash.route("/objects/dom-hash/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_dom_hash_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(DomHashs.DomHashs().api_get_chart_nb_by_daterange(date_from, date_to))

# @objects_dom_hash.route("/objects/dom-hash/search", methods=['POST'])
# @login_required
# @login_read_only
# def objects_dom_hash_search():
#     date_from = request.args.get('date_from')
#     date_to = request.args.get('date_to')
#     date = Date.sanitise_date_range(date_from, date_to)
#     date_from = date['date_from']
#     date_to = date['date_to']
#     return jsonify(HHHashs.HHHashs().api_get_chart_nb_by_daterange(date_from, date_to))
#
#     search_by_id

# @objects_dom_hash.route("/objects/dom-hash/graphline/json", methods=['GET'])
# @login_required
# @login_read_only
# def objects_dom_hash_graphline_json():
#     dom_hash_id = request.args.get('id')
#     cve = Cves.Cve(cve_id)
#     if not cve.exists():
#         abort(404)
#     return jsonify(Cves.get_cve_graphline(cve_id))

# ============= ROUTES ==============

