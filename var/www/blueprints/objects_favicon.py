#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file, send_from_directory
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only, no_cache

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import Favicons
from packages import Date

# ============ BLUEPRINT ============
objects_favicon = Blueprint('objects_favicon', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/favicon'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============
@objects_favicon.route('/favicon/<path:filename>')
@login_required
@login_read_only
@no_cache
def favicon(filename):
    if not filename:
        abort(404)
    if not 9 <= len(filename) <= 11:
        abort(404)
    filename = filename.replace('/', '')
    fav = Favicons.Favicon(filename)
    return send_from_directory(Favicons.FAVICON_FOLDER, fav.get_rel_path(), as_attachment=False, mimetype='image')


@objects_favicon.route("/objects/favicons", methods=['GET'])
@login_required
@login_read_only
def objects_favicons():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = Favicons.Favicons().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    print(dict_objects)

    return render_template("FaviconDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)


@objects_favicon.route("/objects/favicons/post", methods=['POST'])
@login_required
@login_read_only
def objects_favicons_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_favicon.objects_favicons', date_from=date_from, date_to=date_to, show_objects=show_objects))


@objects_favicon.route("/objects/favicons/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_favicons_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(Favicons.Favicons().api_get_chart_nb_by_daterange(date_from, date_to))

# ============= ROUTES ==============

