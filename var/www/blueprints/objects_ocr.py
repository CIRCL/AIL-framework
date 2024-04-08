#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file, send_from_directory
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only, no_cache

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import Ocrs

# ============ BLUEPRINT ============
objects_ocr = Blueprint('objects_ocr', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/ocr'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

from io import BytesIO

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


# ============= ROUTES ==============

