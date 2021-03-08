#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: MISP format import export
'''

import os
import sys
import uuid
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

import AILObjects

# ============ BLUEPRINT ============
import_export = Blueprint('import_export', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/import_export'))

# ============ VARIABLES ============



# ============ FUNCTIONS ============


# ============= ROUTES ==============
@import_export.route('/import_export/import')
@login_required
@login_analyst
def import_object():
    return render_template("import_object.html")

@import_export.route("/import_export/import_file", methods=['POST'])
@login_required
@login_analyst
def import_object_file():
    error = None

    is_file = False
    if 'file' in request.files:
        file = request.files['file']
        if file:
            if file.filename:
                is_file = True

    all_imported_obj = []
    if is_file:
        filename = MispImport.sanitize_import_file_path(file.filename)
        file.save(filename)
        map_uuid_global_id = MispImport.import_objs_from_file(filename)
        os.remove(filename)
        for obj_uuid in map_uuid_global_id:
            dict_obj = Correlate_object.get_global_id_from_id(map_uuid_global_id[obj_uuid])
            dict_obj['uuid'] = obj_uuid
            dict_obj['url'] = Correlate_object.get_item_url(dict_obj['type'], dict_obj['id'], correlation_type=dict_obj['subtype'])
            dict_obj['node'] = Correlate_object.get_correlation_node_icon(dict_obj['type'], correlation_type=dict_obj['subtype'], value=dict_obj['id'])
            all_imported_obj.append(dict_obj)

        if not all_imported_obj:
            error = "error: Empty or invalid JSON file"

    return render_template("import_object.html", all_imported_obj=all_imported_obj, error=error)

@import_export.route('/import_export/export')
@login_required
@login_analyst
def export_object():
    user_id = current_user.get_id()

    # get user saved obj to export
    l_obj_to_export = AILObjects.get_user_list_of_obj_to_export(user_id)

    return render_template("export_object.html", l_obj_to_export=l_obj_to_export)

@import_export.route("/import_export/export_file", methods=['POST'])
@login_required
@login_analyst
def export_object_file():
    user_id = current_user.get_id()

    l_obj_to_export = []
    l_obj_invalid = []

    export_to_misp = False
    dict_misp_event_export = {}

    # Get new added Object
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
                AILObjects.add_user_object_to_export(user_id, obj_dict['type'], obj_dict['id'], obj_dict['lvl'], obj_subtype=obj_dict.get('subtype', None))
            else:
                if obj_id:
                    l_obj_invalid.append(obj_dict)
        else:
            dict_misp_event_export[str(obj_tuple)] = request.form.get(obj_tuple)

    if dict_misp_event_export.get('export_to_misp', None):
        export_to_misp = True
    else:
        dict_misp_event_export = None

    if l_obj_invalid:
        # get user saved obj to export # # TODO: # performance
        l_obj_to_export = AILObjects.get_user_list_of_obj_to_export(user_id)

        for obj_dict in l_obj_invalid: # set uuid input
            obj_dict['uuid'] = str(uuid.uuid4())
            obj_dict['type'] = Correlate_object.get_obj_str_type_subtype(obj_dict['type'], obj_dict.get('subtype', None))

        return render_template("export_object.html", l_obj_to_export=l_obj_to_export,
                                l_obj_invalid=l_obj_invalid, dict_misp_event_export=dict_misp_event_export)
    else:
        if export_to_misp and MispExport.ping_misp():
            event = MispExport.create_list_of_objs_to_export(l_obj_to_export, r_type='event')

            event_metadata = MispExport.create_misp_event(event, distribution=dict_misp_event_export.get('export_to_misp', None),
                                        threat_level_id=dict_misp_event_export.get('misp_threat_level_id', None),
                                        publish=dict_misp_event_export.get('misp_publish', None),
                                        analysis=dict_misp_event_export.get('misp_event_analysis', None),
                                        event_info=dict_misp_event_export.get('misp_event_info', None))

            AILObjects.delete_all_user_object_to_export(user_id)
            return render_template("export_object.html", l_obj_to_export=l_obj_to_export,
                                    event_metadata=event_metadata,
                                    l_obj_invalid=[], dict_misp_event_export=[])
        else:
            # get user saved obj to export # # TODO: # performance
            json_export = MispExport.create_list_of_objs_to_export(l_obj_to_export)
            export_filename = MispExport.get_export_filename(json_export)
            json_export = MispExport.create_in_memory_file(json_export.to_json())
            AILObjects.delete_all_user_object_to_export(user_id)
            return send_file(json_export, as_attachment=True, attachment_filename=export_filename)


@import_export.route("/import_export/add_object_id_to_export", methods=['GET'])
@login_required
@login_analyst
def add_object_id_to_export():
    user_id = current_user.get_id()
    user_id = current_user.get_id()
    obj_type = request.args.get('obj_type')
    obj_id = request.args.get('obj_id')
    obj_subtype = request.args.get('obj_subtype')
    obj_lvl = request.args.get('obj_lvl')
    AILObjects.add_user_object_to_export(user_id, obj_type, obj_id, obj_lvl, obj_subtype=obj_subtype)
    # redirect
    return redirect(url_for('import_export.export_object'))

# @import_export.route("/import_export/delete_object_id_to_export", methods=['GET'])
# @login_required
# @login_analyst
# def delete_object_id_to_export():
#     user_id = current_user.get_id()
#     obj_type = request.args.get('obj_type')
#     obj_id = request.args.get('obj_id')
#     obj_subtype = request.args.get('obj_subtype')
#     obj_lvl = request.args.get('obj_lvl')
#     AILObjects.delete_user_object_to_export(user_id, object_type, object_id, obj_lvl, obj_subtype=obj_subtype)
#     # redirect
#     return 'ok'
