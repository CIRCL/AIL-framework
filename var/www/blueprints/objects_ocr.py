#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import json
import os
import sys

from io import BytesIO

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file, send_from_directory
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only, no_cache

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import Language
from lib import Tag
from lib.objects import Ocrs

from packages import Date

# ============ BLUEPRINT ============
objects_ocr = Blueprint('objects_ocr', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/ocr'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ FUNCTIONS ============
@objects_ocr.route('/ocr/<path:filename>')
@login_required
@login_read_only
@no_cache
def ocr_image(filename):
    if not filename:
        abort(404)
    if not 64 <= len(filename) <= 70:
        abort(404)
    filename = filename.replace('/', '')
    ocr = Ocrs.Ocr(filename)
    return send_file(BytesIO(ocr.draw_bounding_boxs()), mimetype='image/png')


@objects_ocr.route("/objects/ocrs", methods=['GET'])
@login_required
@login_read_only
def objects_ocrs():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = Ocrs.Ocrs().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("OcrDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)


@objects_ocr.route("/objects/ocrs/post", methods=['POST'])
@login_required
@login_read_only
def objects_ocrs_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_ocr.objects_ocrs', date_from=date_from, date_to=date_to, show_objects=show_objects))


@objects_ocr.route("/objects/ocrs/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_ocrs_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(Ocrs.Ocrs().api_get_chart_nb_by_daterange(date_from, date_to))


@objects_ocr.route("/objects/ocr", methods=['GET'])
@login_required
@login_read_only
def object_ocr():
    obj_id = request.args.get('id')
    target = request.args.get('target')
    if target == "Don't Translate":
        target = None
    meta = Ocrs.api_get_ocr(obj_id, target)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    else:
        meta = meta[0]
        languages = Language.get_translation_languages()
        return render_template("ShowOcr.html", meta=meta,
                               bootstrap_label=bootstrap_label,
                               ail_tags=Tag.get_modal_add_tags(meta['id'], meta['type'], meta['subtype']),
                               translation_languages=languages, translation_target=target)


# ============= ROUTES ==============

