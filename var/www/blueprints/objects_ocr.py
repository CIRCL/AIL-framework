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
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only, no_cache

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import Language
from lib import Tag
from lib.objects import Ocrs

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
                               ail_tags=Tag.get_modal_add_tags(meta['id'], meta['type'], meta['subtype']),
                               translation_languages=languages, translation_target=target)


# ============= ROUTES ==============

