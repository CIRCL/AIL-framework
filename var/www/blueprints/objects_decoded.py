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
from lib.objects import Decodeds
from packages import Date

# ============ BLUEPRINT ============
objects_decoded = Blueprint('objects_decoded', __name__,
                            template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/decoded'))


# ============ VARIABLES ============


# ============ FUNCTIONS ============


# ============= ROUTES ==============

@objects_decoded.route("/objects/decodeds", methods=['GET', 'POST'])
@login_required
@login_read_only
def decodeds_dashboard():
    if request.method == 'POST':
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        mimetype = request.form.get('mimetype')
        algo = request.form.get('algo')
        show_decoded = request.form.get('show_decoded')
        return redirect(
            url_for('objects_decoded.decodeds_dashboard', date_from=date_from, date_to=date_to, mimetype=mimetype,
                    algo=algo, show=show_decoded))
    else:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        mimetype = request.args.get('mimetype')
        algo = request.args.get('algo')
        show_decoded = request.args.get('show')
        if show_decoded:
            show_decoded = True

    if mimetype == 'All types':
        mimetype = None
    if algo == 'All encoding':
        algo = None

    algo = Decodeds.sanitise_algo(algo)
    mimetype = Decodeds.sanitise_mimetype(mimetype)
    date_from, date_to = Date.sanitise_daterange(date_from, date_to)
    metas = []
    if show_decoded:
        decodeds = Decodeds.get_decodeds_by_daterange(date_from, date_to, algo=algo, mimetype=mimetype)
        metas = []
        for decoded_id in decodeds:
            decoded = Decodeds.Decoded(decoded_id)
            metas.append(decoded.get_meta(options={'sparkline', 'mimetype', 'icon', 'size', 'vt'}))

    # TODO GET PIE CHARTS

    return render_template("decoded/decodeds_dashboard.html", metas=metas, vt_enabled=Decodeds.is_vt_enabled(),
                           date_from=date_from, date_to=date_to, algo=algo, mimetype=mimetype,
                           algos=Decodeds.get_algos(), show_decoded=show_decoded,
                           mimetypes=Decodeds.get_all_mimetypes())

@objects_decoded.route("/objects/decodeds/search", methods=['POST'])
@login_required
@login_read_only
def decodeds_search():
    decoded_id = request.form.get('object_id')
    return redirect(url_for('correlation.show_correlation', type='decoded', id=decoded_id))

@objects_decoded.route("/objects/decoded/download")
@login_required
@login_read_only
def decoded_download():
    obj_id = request.args.get('id')

    # # TODO: sanitize hash
    obj_id = obj_id.split('/')[0]
    decoded = Decodeds.Decoded(obj_id)
    if decoded.exists():
        filename = f'{decoded.id}.zip'
        zip_content = decoded.get_zip_content()
        return send_file(zip_content, download_name=filename, as_attachment=True)
    else:
        abort(404)


@objects_decoded.route("/objects/decoded/send_to_vt")
@login_required
@login_read_only
def send_to_vt():
    obj_id = request.args.get('id')

    # # TODO: sanitize hash
    obj_id = obj_id.split('/')[0]
    decoded = Decodeds.Decoded(obj_id)
    if decoded.exists():
        decoded.send_to_vt()
        return jsonify(decoded.get_meta_vt())
    else:
        abort(404)


@objects_decoded.route("/objects/decoded/refresh_vt_report")
@login_required
@login_read_only
def refresh_vt_report():
    obj_id = request.args.get('id')

    # # TODO: sanitize hash
    obj_id = obj_id.split('/')[0]
    decoded = Decodeds.Decoded(obj_id)
    if decoded.exists():
        report = decoded.refresh_vt_report()
        return jsonify(hash=decoded.id, report=report)
    else:
        abort(404)


# TODO
@objects_decoded.route("/objects/decoded/algo_pie_chart/json", methods=['GET'])
@login_required
@login_read_only
def decoder_pie_chart_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    mimetype = request.args.get('mimetype')
    return jsonify(Decodeds.api_pie_chart_decoder_json(date_from, date_to, mimetype))

# TODO
@objects_decoded.route("/objects/decoded/mimetype_pie_chart/json", methods=['GET'])
@login_required
@login_read_only
def mimetype_pie_chart_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    algo = request.args.get('algo')
    return jsonify(Decodeds.api_pie_chart_mimetype_json(date_from, date_to, algo))

@objects_decoded.route("/objects/decoded/barchart/json", methods=['GET'])
@login_required
@login_read_only
def barchart_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    mimetype = request.args.get('mimetype')
    return jsonify(Decodeds.api_barchart_range_json(date_from, date_to , mimetype))

@objects_decoded.route("/objects/decoded/graphline/json", methods=['GET'])
@login_required
@login_read_only
def graphline_json():
    decoded_id = request.args.get('id')
    decoded = Decodeds.Decoded(decoded_id)
    if not decoded:
        abort(404)
    return jsonify(Decodeds.graphline_json(decoded_id))
