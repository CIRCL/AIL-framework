#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib.objects import abstract_subtype_object
from lib.objects import ail_objects
from lib.objects import CryptoCurrencies
from lib.objects import Usernames
from packages import Date

# ============ BLUEPRINT ============
objects_subtypes = Blueprint('objects_subtypes', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ FUNCTIONS ============

# TODO VERIFY SUBTYPE
def subtypes_objects_dashboard(obj_type, f_request):
    if request.method == 'POST':
        date_from = f_request.form.get('from')
        date_to = f_request.form.get('to')
        subtype = f_request.form.get('subtype')
        show_objects = bool(f_request.form.get('show_objects'))
        t_obj_type = obj_type.replace('-', '_')
        endpoint_dashboard = url_for(f'objects_subtypes.objects_dashboard_{t_obj_type}')
        endpoint_dashboard = f'{endpoint_dashboard}?from={date_from}&to={date_to}'
        if subtype:
            if subtype == 'All types':
                subtype = None
            if subtype:
                if not ail_objects.is_valid_object_subtype(obj_type, subtype):
                    subtype = None
            if subtype:
                endpoint_dashboard = f'{endpoint_dashboard}&subtype={subtype}'
        if show_objects:
            endpoint_dashboard = f'{endpoint_dashboard}&show_objects={show_objects}'
        return redirect(endpoint_dashboard)
    else:
        date_from = f_request.args.get('from')
        date_to = f_request.args.get('to')
        subtype = f_request.args.get('subtype')
        show_objects = bool(f_request.args.get('show_objects'))
    # Date
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    daily_type_chart = date_from == date_to
    # Subtype
    if subtype == 'All types':
        subtype = None
    if subtype:
        if not ail_objects.is_valid_object_subtype(obj_type, subtype):
            subtype = None

    objs = []
    if show_objects:
        subtypes_objs = abstract_subtype_object.get_subtypes_objs_by_daterange(obj_type, date_from, date_to,
                                                                               subtype=subtype)
        if subtypes_objs:
            for obj_t, obj_subtype, obj_id in subtypes_objs:
                objs.append(ail_objects.get_object_meta(obj_t, obj_subtype, obj_id, options={'sparkline'}, flask_context=True))

    t_obj_type = obj_type.replace('-', '_')
    endpoint_dashboard = f'objects_subtypes.objects_dashboard_{t_obj_type}'
    return render_template('subtypes_objs_dashboard.html', date_from=date_from, date_to=date_to,
                           daily_type_chart = daily_type_chart, show_objects=show_objects,
                           obj_type=obj_type, subtype=subtype, objs=objs,
                           subtypes = ail_core.get_object_all_subtypes(obj_type),
                           endpoint_dashboard=endpoint_dashboard)


# ============= ROUTES ==============

@objects_subtypes.route("/objects/chats", methods=['GET'])
@login_required
@login_read_only
def objects_dashboard_chat():
    return subtypes_objects_dashboard('chat', request)

@objects_subtypes.route("/objects/cryptocurrencies", methods=['GET'])
@login_required
@login_read_only
def objects_dashboard_cryptocurrency():
    return subtypes_objects_dashboard('cryptocurrency', request)

@objects_subtypes.route("/objects/pgps", methods=['GET'])
@login_required
@login_read_only
def objects_dashboard_pgp():
    return subtypes_objects_dashboard('pgp', request)

@objects_subtypes.route("/objects/usernames", methods=['GET'])
@login_required
@login_read_only
def objects_dashboard_username():
    return subtypes_objects_dashboard('username', request)

@objects_subtypes.route("/objects/usernames/search", methods=['GET', 'POST'])
@login_required
@login_read_only
def objects_username_search():
    if request.method == 'POST':
        to_search = request.form.get('to_search')
        subtype = request.form.get('search_subtype')
        case_sensitive = bool(request.form.get('case_sensitive'))
        if case_sensitive:
            case_sensitive = 1
        else:
            case_sensitive = 0
        page = request.form.get('page', 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1
        return redirect(url_for('objects_subtypes.objects_username_search', search=to_search, page=page, subtype=subtype, case_sensitive=case_sensitive))
    else:
        to_search = request.args.get('search')
        subtype = request.args.get('subtype')  # TODO sanityze
        case_sensitive = request.args.get('case_sensitive', False)
        if case_sensitive and case_sensitive != '0':
            case_sensitive = True
        else:
            case_sensitive = False
        page = request.args.get('page', 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1

        usernames = Usernames.Usernames()
        if not usernames.is_valid_search(subtype, to_search):
            return create_json_response({'status': 'error', 'message': 'Invalid Username'}, 400)

        search_result = usernames.search_by_id(to_search, [subtype], page, case_sensitive=case_sensitive)

        if search_result:
            ids = sorted(search_result.keys())
            dict_page = ail_core.paginate_iterator(ids, nb_obj=500, page=page)
            dict_objects = usernames.get_metas(subtype, dict_page['list_elem'], options={'icon', 'sparkline'})  # TODO OPTIONS
        else:
            dict_objects = {}
            dict_page = {}

        return render_template("username/search_usernames_result.html", dict_objects=dict_objects, search_result=search_result,
                               dict_page=dict_page, subtypes=ail_core.get_object_all_subtypes('username'),
                               to_search=to_search, subtype=subtype, case_sensitive=case_sensitive)

@objects_subtypes.route("/objects/user-accounts", methods=['GET'])
@login_required
@login_read_only
def objects_dashboard_user_account():
    return subtypes_objects_dashboard('user-account', request)

# TODO REDIRECT
@objects_subtypes.route("/objects/subtypes/post", methods=['POST'])
@login_required
@login_read_only
def objects_subtypes_dashboard_post():
    obj_type = request.form.get('obj_type')
    if obj_type not in ail_core.get_objects_with_subtypes():
        return create_json_response({'error': 'Invalid Object type'}, 400)
    return subtypes_objects_dashboard(obj_type, request)

@objects_subtypes.route("/objects/subtypes/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_subtypes_range_json():
    obj_type = request.args.get('type')
    if obj_type not in ail_core.get_objects_with_subtypes():
        return create_json_response({'error': 'Invalid Object type'}, 400)
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    return jsonify(abstract_subtype_object.get_subtypes_objs_range_json(obj_type, date_from, date_to))

@objects_subtypes.route("/objects/subtypes/search", methods=['POST'])
@login_required
@login_read_only
def objects_subtypes_search():
    obj_type = request.form.get('type')
    subtype = request.form.get('subtype')
    obj_id = request.form.get('id')
    if obj_type not in ail_core.get_objects_with_subtypes():
        return create_json_response({'error': 'Invalid Object type'}, 400)
    obj = ail_objects.get_object(obj_type, subtype, obj_id)
    if not obj.exists():
        abort(404)
    else:
        # TODO Search object
        return redirect(obj.get_link(flask_context=True))

@objects_subtypes.route("/objects/subtypes/graphline/json", methods=['GET'])
@login_required
@login_read_only
def objects_cve_graphline_json():
    obj_type = request.args.get('type')
    subtype = request.args.get('subtype')
    obj_id = request.args.get('id')
    if obj_type not in ail_core.get_objects_with_subtypes():
        return create_json_response({'error': 'Invalid Object type'}, 400)
    obj = ail_objects.get_object(obj_type, subtype, obj_id)
    if not obj.exists():
        abort(404)
    else:
        return jsonify(obj.get_graphline())
