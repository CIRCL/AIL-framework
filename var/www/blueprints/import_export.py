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
from Role_Manager import login_admin, login_org_admin, login_read_only, login_user_no_api

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from exporter import MISPExporter
from exporter import TheHiveExporter
from lib.exceptions import MISPConnectionError
from lib.objects import ail_objects
from lib import ail_core
from lib import ail_config
from lib.Investigations import Investigation, api_check_investigation_acl

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
@login_user_no_api
def import_object():
    return render_template("import_object.html")


# TODO
# @import_export.route("/import_export/import_file", methods=['POST'])
# @login_required
# @login_admin
# def import_object_file():
#     error = None
#
#     is_file = False
#     if 'file' in request.files:
#         file = request.files['file']
#         if file:
#             if file.filename:
#                 is_file = True
#
#     all_imported_obj = []
#     if is_file:
#         filename = MispImport.sanitize_import_file_path(file.filename)
#         file.save(filename)
#         map_uuid_global_id = MispImport.import_objs_from_file(filename)
#         os.remove(filename)
#         for obj_uuid in map_uuid_global_id:
#             dict_obj = MispImport.get_global_id_from_id(map_uuid_global_id[obj_uuid])
#             obj = ail_objects.get_object(dict_obj['type'], dict_obj['subtype'], dict_obj['id'])
#             dict_obj['uuid'] = obj_uuid
#             dict_obj['url'] = obj.get_link(flask_context=True)
#             dict_obj['node'] = obj.get_svg_icon()
#             all_imported_obj.append(dict_obj)
#
#         if not all_imported_obj:
#             error = "error: Empty or invalid JSON file"
#
#     return render_template("import_object.html", all_imported_obj=all_imported_obj, error=error)


@import_export.route("/misp/objects/export", methods=['GET'])
@login_required
@login_user_no_api
def objects_misp_export():
    user_id = current_user.get_user_id()
    object_types = ail_core.get_all_objects_with_subtypes_tuple()
    to_export = MISPExporter.get_user_misp_objects_to_export(user_id)
    misps = ail_config.get_user_misps_selector(user_id)
    return render_template("export_object.html", object_types=object_types, to_export=to_export,
                           misps=misps)


@import_export.route("/misp/objects/export/post", methods=['POST'])
@login_required
@login_user_no_api
def objects_misp_export_post():
    user_id = current_user.get_user_id()

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
        object_types = ail_core.get_all_objects_with_subtypes_tuple()
        misps = ail_config.get_user_misps_selector(user_id)
        return render_template("export_object.html", object_types=object_types,
                               to_export=objects, l_obj_invalid=invalid_obj, misps=misps)

    export = request.form.get('export_to_misp', False)
    distribution = request.form.get('misp_event_distribution')
    threat_level = request.form.get('misp_threat_level_id')
    analysis = request.form.get('misp_event_analysis')
    info = request.form.get('misp_event_info')
    publish = request.form.get('misp_event_info', False)

    objs = ail_objects.get_objects(objects)
    if not objs:
        return create_json_response({'error': 'Empty Event, nothing to export'}, 400)

    if export:
        misp_uuid = request.form.get('user_misp')
        if misp_uuid:
            misp_uuid = misp_uuid[0:-1]

            if not misp_uuid:
                return create_json_response({'error': 'Undefined misp config uuid'}, 400)
            else:
                misp_uuid = misp_uuid[2:].split(':', 1)[0]
                if not ail_core.is_valid_uuid_v5(misp_uuid):
                    return create_json_response({'error': 'Invalid misp config uuid'}, 400)

                misp_meta = ail_config.api_get_user_misps(user_id, misp_uuid)
                if misp_meta[1] != 200:
                    return create_json_response(misp_meta[0], misp_meta[1])
                else:
                    misp_meta = misp_meta[0]

                misp = MISPExporter.MISPExporterAILObjects(url=misp_meta['url'], key=misp_meta['key'], ssl=misp_meta['ssl'])
                try:
                    event = misp.create_event(objs, distribution=distribution, threat_level=threat_level, analysis=analysis, info=info, export=export, publish=publish)
                except MISPConnectionError as e:
                    return create_json_response({"error": e.message}, 400)

                MISPExporter.delete_user_misp_objects_to_export(user_id)

                object_types = ail_core.get_all_objects_with_subtypes_tuple()
                misps = ail_config.get_user_misps_selector(user_id)
                return render_template("export_object.html", object_types=object_types,
                                       misp_url=event['url'], misps=misps)

    else:
        event = misp_exporter_objects.create_event(objs, distribution=distribution, threat_level=threat_level, analysis=analysis, info=info, export=export, publish=publish)

        # print(event)
        event_uuid = event[9:45]
        event = f'{{"Event": {event}}}'

        MISPExporter.delete_user_misp_objects_to_export(user_id)
        return send_file(io.BytesIO(event.encode()), as_attachment=True, download_name=f'ail_export_{event_uuid}.json')


@import_export.route("/misp/objects/export/add", methods=['GET'])
@login_required
@login_user_no_api
def add_object_id_to_export():
    user_id = current_user.get_user_id()
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
@login_user_no_api
def delete_object_id_to_export():
    user_id = current_user.get_user_id()
    obj_type = request.args.get('type')
    obj_id = request.args.get('id')
    obj_subtype = request.args.get('subtype')

    MISPExporter.delete_user_misp_object_to_export(user_id, obj_type, obj_subtype, obj_id)
    return jsonify(success=True)


@import_export.route("/investigation/misp/export", methods=['POST'])
@login_required
@login_user_no_api
def export_investigation():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    investigation_uuid = request.form.get("investigation_uuid")
    investigation = Investigation(investigation_uuid)

    if not investigation.exists():
        create_json_response({'status': 'error', 'reason': 'Investigation Not Found'}, 404)
    res = api_check_investigation_acl(investigation, user_org, user_id, user_role, 'view')
    if res:
        return create_json_response(res[0], res[1])

    # JSON Export
    export = request.form.get('export_to_misp', False)
    if not export:
        event = misp_exporter_investigation.export(investigation)
        event_uuid = event[9:45]
        event = f'{{"Event": {event}}}'
        return send_file(io.BytesIO(event.encode()), as_attachment=True, download_name=f'ail_export_{event_uuid}.json')
    # MISP Export
    else:
        misp_uuid = request.form.get('user_misp')
        if misp_uuid:
            misp_uuid = misp_uuid[0:-1]

            if not misp_uuid:
                return create_json_response({'error': 'Undefined misp config uuid'}, 400)
            else:
                misp_uuid = misp_uuid[2:].split(':', 1)[0]
                if not ail_core.is_valid_uuid_v5(misp_uuid):
                    return create_json_response({'error': 'Invalid misp config uuid'}, 400)

                misp_meta = ail_config.api_get_user_misps(user_id, misp_uuid)
                if misp_meta[1] != 200:
                    return create_json_response(misp_meta[0], misp_meta[1])
                else:
                    misp_meta = misp_meta[0]

                misp = MISPExporter.MISPExporterInvestigation(url=misp_meta['url'], key=misp_meta['key'], ssl=misp_meta['ssl'])
                try:
                    event = misp.export(investigation)
                except MISPConnectionError as e:
                    return create_json_response({"error": e.message}, 400)
                event_url = event['url']
                return redirect(url_for('investigations_b.show_investigation', uuid=investigation_uuid, misp_url=event_url))


@import_export.route("/thehive/objects/case/export", methods=['POST'])
@login_required
@login_admin
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
