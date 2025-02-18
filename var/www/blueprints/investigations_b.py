#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: ail_investigations
"""

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_user_no_api, login_read_only

sys.path.append('modules')
import Flask_config

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_config
from lib import Investigations
from lib.objects import ail_objects
from lib import Tag

# ============ BLUEPRINT ============
investigations_b = Blueprint('investigations_b', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/investigations'))

# ============ VARIABLES ============
bootstrap_label = Flask_config.bootstrap_label

# ============ FUNCTIONS ============
def create_json_response(data, status_code):
    if status_code == 403:
        abort(403)
    elif status_code == 404:
        abort(404)
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============

@investigations_b.route("/investigations", methods=['GET'])
@login_required
@login_read_only
def investigations_dashboard():
    inv_global = Investigations.get_global_investigations_meta(r_str=True)
    inv_org = Investigations.get_org_investigations_meta(current_user.get_org(), r_str=True)
    return render_template("investigations.html", bootstrap_label=bootstrap_label,
                           inv_global=inv_global, inv_org=inv_org)

@investigations_b.route("/investigations/admin", methods=['GET'])
@login_required
@login_admin
def investigations_admin():
    inv_org = Investigations.get_orgs_investigations_meta(r_str=True)
    return render_template("investigations.html", bootstrap_label=bootstrap_label,
                           inv_global=[], inv_org=inv_org)


@investigations_b.route("/investigation", methods=['GET'])  # # FIXME: add /view ????
@login_required
@login_read_only
def show_investigation():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    investigation_uuid = request.args.get("uuid")
    misp_url = request.args.get("misp_url")
    investigation = Investigations.Investigation(investigation_uuid)
    if not investigation.exists():
        create_json_response({'status': 'error', 'reason': 'Investigation Not Found'}, 404)
    res = Investigations.api_check_investigation_acl(investigation, user_org, user_id, user_role, 'view')
    if res:
        return create_json_response(res[0], res[1])

    metadata = investigation.get_metadata(r_str=True, options={'org_name'})
    objs = []
    for obj in investigation.get_objects():
        obj_meta = ail_objects.get_object_meta(obj["type"], obj["subtype"], obj["id"], flask_context=True)
        comment = investigation.get_objects_comment(f'{obj["type"]}:{obj["subtype"]}:{obj["id"]}')
        if comment:
            obj_meta['comment'] = comment
        objs.append(obj_meta)
    misps = ail_config.get_user_misps_selector(user_id)
    return render_template("view_investigation.html", bootstrap_label=bootstrap_label,
                           misps=misps, misp_url=misp_url,
                           metadata=metadata, investigation_objs=objs)


@investigations_b.route("/investigation/add", methods=['GET', 'POST'])
@login_required
@login_user_no_api
def add_investigation():
    if request.method == 'POST':
        user_id = current_user.get_user_id()
        user_org = current_user.get_org()
        level = request.form.get("investigation_level")
        name = request.form.get("investigation_name")
        date = request.form.get("investigation_date")
        threat_level = request.form.get("threat_level")
        analysis = request.form.get("analysis")
        info = request.form.get("investigation_info")
        # tags
        taxonomies_tags = request.form.get('taxonomies_tags')
        if taxonomies_tags:
            try:
                taxonomies_tags = json.loads(taxonomies_tags)
            except Exception:
                taxonomies_tags = []
        else:
            taxonomies_tags = []
        galaxies_tags = request.form.get('galaxies_tags')
        if galaxies_tags:
            try:
                galaxies_tags = json.loads(galaxies_tags)
            except Exception:
                galaxies_tags = []
        tags = taxonomies_tags + galaxies_tags

        input_dict = {"user_org": user_org, "user_id": user_id, "level": level, "name": name,
                      "threat_level": threat_level, "date": date,
                      "analysis": analysis, "info": info, "tags": tags}
        res = Investigations.api_add_investigation(input_dict)
        if res[1] != 200:
            return create_json_response(res[0], res[1])

        return redirect(url_for('investigations_b.show_investigation', uuid=res[0]))
    else:
        return render_template("add_investigation.html", tags_selector_data=Tag.get_tags_selector_data())


@investigations_b.route("/investigation/edit", methods=['GET', 'POST'])
@login_required
@login_user_no_api
def edit_investigation():  # TODO CHECK ACL
    if request.method == 'POST':
        user_org = current_user.get_org()
        user_id = current_user.get_user_id()
        user_role = current_user.get_role()
        investigation_uuid = request.form.get("investigation_uuid")
        level = request.form.get("investigation_level")
        name = request.form.get("investigation_name")
        date = request.form.get("investigation_date")
        threat_level = request.form.get("threat_level")
        analysis = request.form.get("analysis")
        info = request.form.get("investigation_info")

        # tags
        taxonomies_tags = request.form.get('taxonomies_tags')
        if taxonomies_tags:
            try:
                taxonomies_tags = json.loads(taxonomies_tags)
            except Exception:
                taxonomies_tags = []
        else:
            taxonomies_tags = []
        galaxies_tags = request.form.get('galaxies_tags')
        if galaxies_tags:
            try:
                galaxies_tags = json.loads(galaxies_tags)
            except Exception:
                galaxies_tags = []
        tags = taxonomies_tags + galaxies_tags

        input_dict = {"user_id": user_id, "uuid": investigation_uuid, "level": level,
                      "name": name, "threat_level": threat_level,
                      "analysis": analysis, "info": info, "tags": tags}
        res = Investigations.api_edit_investigation(user_org, user_id, user_role, input_dict)
        if res[1] != 200:
            return create_json_response(res[0], res[1])

        return redirect(url_for('investigations_b.show_investigation', uuid=res[0]))
    else:
        investigation_uuid = request.args.get('uuid')
        investigation = Investigations.Investigation(investigation_uuid)
        metadata = investigation.get_metadata(r_str=False)
        taxonomies_tags, galaxies_tags = Tag.sort_tags_taxonomies_galaxies(metadata['tags'])
        tags_selector_data = Tag.get_tags_selector_data()
        tags_selector_data['taxonomies_tags'] = taxonomies_tags
        tags_selector_data['galaxies_tags'] = galaxies_tags
        return render_template("add_investigation.html", edit=True,
                               tags_selector_data=tags_selector_data, metadata=metadata)

@investigations_b.route("/investigation/delete", methods=['GET'])
@login_required
@login_user_no_api
def delete_investigation():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    investigation_uuid = request.args.get('uuid')
    input_dict = {"uuid": investigation_uuid}
    res = Investigations.api_delete_investigation(user_org, user_id, user_role, input_dict)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('investigations_b.investigations_dashboard'))

@investigations_b.route("/investigation/object/register", methods=['GET'])
@login_required
@login_user_no_api
def register_investigation():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    user_role = current_user.get_role()
    investigations_uuid = request.args.get('uuids')
    investigations_uuid = investigations_uuid.split(',')

    object_type = request.args.get('type')
    object_subtype = request.args.get('subtype')
    object_id = request.args.get('id')
    comment = request.args.get('comment')

    for investigation_uuid in investigations_uuid:
        input_dict = {"uuid": investigation_uuid, "id": object_id,
                      "type": object_type, "subtype": object_subtype}
        if comment:
            input_dict["comment"] = comment
        res = Investigations.api_register_object(user_org, user_id, user_role, input_dict)
        if res[1] != 200:
            return create_json_response(res[0], res[1])
    return redirect(url_for('investigations_b.investigations_dashboard'))

@investigations_b.route("/investigation/object/unregister", methods=['GET'])
@login_required
@login_user_no_api
def unregister_investigation():
    user_id = current_user.get_user_id()
    user_org = current_user.get_org()
    user_role = current_user.get_role()
    investigation_uuid = request.args.get('uuid')
    object_type = request.args.get('type')
    object_subtype = request.args.get('subtype')
    object_id = request.args.get('id')
    input_dict = {"uuid": investigation_uuid, "id": object_id,
                  "type": object_type, "subtype": object_subtype}
    res = Investigations.api_unregister_object(user_org, user_id, user_role, input_dict)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('investigations_b.show_investigation', uuid=investigation_uuid))


@investigations_b.route("/investigation/all/selector_json")
@login_required
@login_read_only
def get_investigations_selector_json():
    return jsonify(Investigations.get_investigations_selector(current_user.get_org()))

@investigations_b.route("/object/gid")
@login_required
@login_read_only
def get_object_gid():
    obj_global_id = request.args.get('gid')
    ail_obj = ail_objects.get_obj_from_global_id(obj_global_id)
    url = ail_obj.get_link(flask_context=True)
    return redirect(url)

#
# @investigations_b.route("/object/item") #completely shows the paste in a new tab
# @login_required
# @login_user
# def showItem(): # # TODO: support post
#     item_id = request.args.get('id')
#     if not item_id or not Item.exist_item(item_id):
#         abort(404)
#
#     return render_template("show_item.html", bootstrap_label=bootstrap_label)
