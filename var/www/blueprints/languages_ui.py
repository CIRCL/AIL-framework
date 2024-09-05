#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
"""

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_user_no_api, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib import Language
from lib import Tag
from lib.objects import ail_objects

# ============ BLUEPRINT ============
languages_ui = Blueprint('languages_ui', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/chats_explorer'))

# ============ VARIABLES ============
# bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ FUNCTIONS ============

# ============= ROUTES ==============
@languages_ui.route("/languages/object/translate", methods=['POST'])
@login_required
@login_user_no_api
def translate_object():
    obj_type = request.form.get('type')
    subtype = request.form.get('subtype')
    obj_id = request.form.get('id')
    source = request.form.get('language_target')
    target = request.form.get('target')
    translation = request.form.get('translation')
    if target == "Don't Translate":
        target = None

    resp = ail_objects.api_manually_translate(obj_type, subtype, obj_id, source, target, translation)
    if resp[1] != 200:
        return create_json_response(resp[0], resp[1])
    else:
        if request.referrer:
            return redirect(request.referrer)
        else:
            if obj_type == 'ocr':
                return redirect(url_for('objects_ocr.object_ocr', id=obj_id, target=target))  # TODO change to support all objects

@languages_ui.route("/languages/object/detect/language", methods=['GET'])
@login_required
@login_user_no_api
def detect_object_language():
    obj_type = request.args.get('type')
    subtype = request.args.get('subtype')
    obj_id = request.args.get('id')
    target = request.args.get('target')

    resp = ail_objects.api_detect_language(obj_type, subtype, obj_id)
    if resp[1] != 200:
        return create_json_response(resp[0], resp[1])
    else:
        if request.referrer:
            return redirect(request.referrer)
        else:
            if obj_type == 'ocr':
                return redirect(url_for('objects_ocr.object_ocr', id=obj_id, target=target))  # TODO change to support all objects




