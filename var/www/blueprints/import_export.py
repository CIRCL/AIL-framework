#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: MISP format import export
"""
import io
import os
import sys
import json

from flask import render_template, jsonify, request, Blueprint, redirect, url_for, Response, send_file, abort
from flask_login import login_required, current_user

sys.path.append('modules')

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from exporter import MISPExporter
from exporter import TheHiveExporter
from lib.exceptions import MISPConnectionError
from lib.objects import ail_objects
from lib import ail_core
from lib.Investigations import Investigation

# ============ BLUEPRINT ============
import_export = Blueprint('import_export', __name__,
                          template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/import_export'))

# ============ VARIABLES ============
misp_exporter_objects = MISPExporter.MISPExporterAILObjects()
misp_exporter_investigation = MISPExporter.MISPExporterInvestigation()

thehive_exporter_item = TheHiveExporter.TheHiveExporterItem()


# ============ FUNCTIONS ============

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code


# ============= ROUTES ==============
@import_export.route('/import_export/import')
@login_required
@login_analyst
def import_object():
    return render_template("import_object.html")


# TODO
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
            dict_obj = MispImport.get_global_id_from_id(map_uuid_global_id[obj_uuid])
            obj = ail_objects.get_object(dict_obj['type'], dict_obj['subtype'], dict_obj['id'])
            dict_obj['uuid'] = obj_uuid
            dict_obj['url'] = obj.get_link(flask_context=True)
            dict_obj['node'] = obj.get_svg_icon()
            all_imported_obj.append(dict_obj)

        if not all_imported_obj:
            error = "error: Empty or invalid JSON file"

    return render_template("import_object.html", all_imported_obj=all_imported_obj, error=error)


@import_export.route("/misp/objects/export", methods=['GET'])
@login_required
@login_analyst
def objects_misp_export():
    user_id = current_user.get_id()
    object_types = ail_core.get_all_objects_with_subtypes_tuple()
    to_export = MISPExporter.get_user_misp_objects_to_export(user_id)
    return render_template("export_object.html", object_types=object_types, to_export=to_export)


@import_export.route("/misp/objects/export/post", methods=['POST'])
@login_required
@login_analyst
def objects_misp_export_post():
    user_id = current_user.get_id()

    # Get new added Object
    new_export = []
    user_lvl_export = {}
    for obj_tuple in list(request.form):
        # GET NEW LEVEL
        if obj_tuple[0] == '{':
            obj_j = obj_tuple.replace("'", "\"")
            obj_dict = json.loads(obj_j)  # TODO sanitize
            lvl = int(request.form.getlist(obj_tuple)[0])
            user_lvl_export[f"{obj_dict['type']}:{obj_dict['subtype']}:{obj_dict['id']}"] = lvl

        l_input = request.form.getlist(obj_tuple)
        if len(l_input) == 3:
            if l_input[0] != 'Object type...':
                new_type, new_subtype = l_input[0].split(':', 1)
                if not new_subtype:
                    new_subtype = ''
                new_export.append({'type': new_type, 'subtype': new_subtype, 'id': l_input[1], 'lvl': l_input[2]})

    objects = []
    invalid_obj = []
    for obj in new_export:
        if not ail_objects.exists_obj(obj['type'], obj['subtype'], obj['id']):
            invalid_obj.append(obj)
        else:
            objects.append(obj)
    for obj in MISPExporter.get_user_misp_objects_to_export(user_id):
        if not ail_objects.exists_obj(obj['type'], obj['subtype'], obj['id']):
            invalid_obj.append(obj)
        else:
            str_id = f"{obj['type']}:{obj['subtype']}:{obj['id']}"
            if str_id in user_lvl_export:
                obj['lvl'] = user_lvl_export[str_id]
            objects.append(obj)

    if invalid_obj:
        object_types = ail_objects.get_all_objects_with_subtypes_tuple()
        return render_template("export_object.html", object_types=object_types,
                               to_export=objects, l_obj_invalid=invalid_obj)

    export = request.form.get('export_to_misp', False)
    distribution = request.form.get('misp_event_distribution')
    threat_level = request.form.get('threat_level_id')
    analysis = request.form.get('misp_event_analysis')
    info = request.form.get('misp_event_info')
    publish = request.form.get('misp_event_info', False)

    objs = ail_objects.get_objects(objects)
    try:
        event = misp_exporter_objects.create_event(objs, distribution=distribution, threat_level=threat_level,
                                               analysis=analysis, info=info, export=export, publish=publish)
    except MISPConnectionError as e:
        return create_json_response({"error": e.message}, 400)

    MISPExporter.delete_user_misp_objects_to_export(user_id)
    if not export:
        event_uuid = event[10:46]
        # TODO ADD JAVASCRIPT REFRESH PAGE IF RESP == 200
        return send_file(io.BytesIO(event.encode()), as_attachment=True,
                         download_name=f'ail_export_{event_uuid}.json')
    else:
        object_types = ail_objects.get_all_objects_with_subtypes_tuple()
        return render_template("export_object.html", object_types=object_types,
                               misp_url=event['url'])


@import_export.route("/misp/objects/export/add", methods=['GET'])
@login_required
@login_analyst
def add_object_id_to_export():
    user_id = current_user.get_id()
    obj_type = request.args.get('type')
    obj_id = request.args.get('id')
    obj_subtype = request.args.get('subtype')
    obj_lvl = request.args.get('lvl')

    try:
        obj_lvl = int(obj_lvl)
    except:
        obj_lvl = 0

    if not ail_objects.exists_obj(obj_type, obj_subtype, obj_id):
        abort(404)
    MISPExporter.add_user_misp_object_to_export(user_id, obj_type, obj_subtype, obj_id, lvl=obj_lvl)
    # redirect
    return redirect(url_for('import_export.objects_misp_export'))


@import_export.route("/misp/objects/export/delete", methods=['GET'])
@login_required
@login_analyst
def delete_object_id_to_export():
    user_id = current_user.get_id()
    obj_type = request.args.get('type')
    obj_id = request.args.get('id')
    obj_subtype = request.args.get('subtype')

    MISPExporter.delete_user_misp_object_to_export(user_id, obj_type, obj_subtype, obj_id)
    return jsonify(success=True)


@import_export.route("/investigation/misp/export", methods=['GET'])
@login_required
@login_analyst
def export_investigation():
    investigation_uuid = request.args.get("uuid")
    investigation = Investigation(investigation_uuid)
    if not investigation.exists():
        abort(404)
    if misp_exporter_objects.ping_misp():
        event = misp_exporter_investigation.export(investigation)
        print(event)
    else:
        return Response(json.dumps({"error": "Can't reach MISP Instance"}, indent=2, sort_keys=True),
                        mimetype='application/json'), 400
    return redirect(url_for('investigations_b.show_investigation', uuid=investigation_uuid))


@import_export.route("/thehive/objects/case/export", methods=['POST'])
@login_required
@login_analyst
def create_thehive_case():
    description = request.form['hive_description']
    title = request.form['hive_case_title']
    threat_level = request.form['threat_level_hive']
    tlp = request.form['hive_tlp']
    item_id = request.form['obj_id']

    item = ail_objects.get_object('item', '', item_id)
    if not item.exists():
        abort(404)

    case_id = thehive_exporter_item.export(item.get_id(), description=description, title=title,
                                           threat_level=threat_level, tlp=tlp)
    if case_id:
        return redirect(thehive_exporter_item.get_case_url(case_id))
    else:
        return 'error'
