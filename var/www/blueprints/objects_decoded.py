#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import Decodeds


# ============ BLUEPRINT ============
objects_decoded = Blueprint('objects_decoded', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/decoded'))

# ============ VARIABLES ============


# ============ FUNCTIONS ============


# ============= ROUTES ==============

# # TODO: # FIXME: CHECK IF OBJ EXIST

@objects_decoded.route("/object/decoded/download") #completely shows the paste in a new tab
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
        return send_file(zip_content, attachment_filename=filename, as_attachment=True)
    else:
        abort(404)

@objects_decoded.route("/object/decoded/send_to_vt") #completely shows the paste in a new tab
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

@objects_decoded.route("/object/decoded/refresh_vt_report") #completely shows the paste in a new tab
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

@objects_decoded.route("/object/decoded/decoder_pie_chart_json", methods=['GET'])
@login_required
@login_read_only
def decoder_pie_chart_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    mimetype = request.args.get('type')
    return jsonify(Decodeds.api_pie_chart_decoder_json(date_from, date_to, mimetype))






#####################################################3
