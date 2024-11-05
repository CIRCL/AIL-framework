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
from lib.objects import BarCodes

from packages import Date

# ============ BLUEPRINT ============
objects_barcode = Blueprint('objects_barcode', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/barcode'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ FUNCTIONS ============

@objects_barcode.route("/objects/barcodes", methods=['GET'])
@login_required
@login_read_only
def objects_barcodes():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = BarCodes.Barcodes().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("BarcodeDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)


@objects_barcode.route("/objects/barcodes/post", methods=['POST'])
@login_required
@login_read_only
def objects_barcodes_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_barcode.objects_barcodes', date_from=date_from, date_to=date_to, show_objects=show_objects))


@objects_barcode.route("/objects/barcodes/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_barcodes_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(BarCodes.Barcodes().api_get_chart_nb_by_daterange(date_from, date_to))


@objects_barcode.route("/objects/barcode", methods=['GET'])
@login_required
@login_read_only
def object_barcode():
    obj_id = request.args.get('id')
    meta = BarCodes.api_get_barcode(obj_id)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    else:
        meta = meta[0]
        return render_template("ShowBarcode.html", meta=meta,
                               bootstrap_label=bootstrap_label,
                               ail_tags=Tag.get_modal_add_tags(meta['id'], meta['type'], meta['subtype']))


# ============= ROUTES ==============

