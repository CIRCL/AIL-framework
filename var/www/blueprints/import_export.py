#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: MISP format import export
'''

import os
import sys
import json
import random

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, send_file
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

@import_export.route("/import_export/export_file", methods=['POST'])
@login_required
@login_analyst
def export_object_file():
    l_obj_to_export = []
    l_obj_invalid = []
    for obj_tuple in list(request.form):
        l_input = request.form.getlist(obj_tuple)
        if len(l_input) == 3:
            obj_type = l_input[0]
            obj_id = l_input[1]
            lvl = l_input[2]
            lvl = MispExport.sanitize_obj_export_lvl(lvl)

            obj_subtype = obj_type.split(';')
            if len(obj_subtype) == 2:
                obj_type = obj_subtype[0]
                obj_subtype = obj_subtype[1]
            else:
                obj_subtype = None

            obj_dict = {'id': obj_id, 'type': obj_type, 'lvl': lvl}
            if obj_subtype:
                obj_dict['subtype'] = obj_subtype

            if MispExport.is_valid_obj_to_export(obj_type, obj_subtype, obj_id):
                l_obj_to_export.append(obj_dict)
            else:
                l_obj_invalid.append(obj_dict)
    print(l_obj_to_export)
    print(l_obj_invalid)

    if l_obj_to_export:

        json_export = MispExport.create_list_of_objs_to_export(l_obj_to_export)
        export_filename = MispExport.get_export_filename(json_export)
        json_export = MispExport.create_in_memory_file(json_export)
        return send_file(json_export, as_attachment=True, attachment_filename=export_filename)

    else:
        return render_template("export_object.html", bootstrap_label=bootstrap_label)
