#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: MISP format import export
'''

import os
import sys
import json
import random

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response
from flask_login import login_required, current_user, login_user, logout_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import create_user_db, check_password_strength, check_user_role_integrity
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'export'))
import MispImport
import MispExport

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import Correlate_object

bootstrap_label = Flask_config.bootstrap_label

# ============ BLUEPRINT ============
import_export = Blueprint('import_export', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/import_export'))

# ============ VARIABLES ============



# ============ FUNCTIONS ============


# ============= ROUTES ==============
@import_export.route('/import_export/import')
@login_required
@login_analyst
def import_object():
    tags = request.args.get('tags')
    return render_template("import_object.html", bootstrap_label=bootstrap_label)

@import_export.route("/import_export/import_file", methods=['POST'])
@login_required
@login_analyst
def import_object_file():

    is_file = False
    if 'file' in request.files:
        file = request.files['file']
        if file:
            if file.filename:
                is_file = True

    if is_file:
        filename = MispImport.sanitize_import_file_path(file.filename)
        file.save(filename)
        map_uuid_global_id = MispImport.import_objs_from_file(filename)
        os.remove(filename)

    return render_template("import_object.html", bootstrap_label=bootstrap_label)

@import_export.route('/import_export/export')
@login_required
@login_analyst
def export_object():
    object_type = request.args.get('object_type')
    return render_template("export_object.html", bootstrap_label=bootstrap_label)
