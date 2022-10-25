#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import item_basic
from lib.objects.Items import Item
from lib import Tag
from export import Export


# ============ BLUEPRINT ============
objects_item = Blueprint('objects_item', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/item'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============


# ============= ROUTES ==============
@objects_item.route("/object/item")
@login_required
@login_read_only
def showItem():  # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not item_basic.exist_item(item_id):
        abort(404)

    item = Item(item_id)
    meta = item.get_meta(options=['content', 'crawler', 'duplicates', 'lines', 'size'])

    meta['name'] = meta['id'].replace('/', ' / ')
    meta['father'] = item_basic.get_item_parent(item_id)
    ## EXPORT SECTION
    # # TODO: ADD in Export SECTION
    meta['hive_case'] = Export.get_item_hive_cases(item_id)

    return render_template("show_item.html", bootstrap_label=bootstrap_label,
                            modal_add_tags=Tag.get_modal_add_tags(meta['id'], object_type='item'),
                            is_hive_connected=Export.get_item_hive_cases(item_id),
                            meta=meta)

    # kvrocks data

    # # TODO: dynamic load:
    ## duplicates
    ## correlations

    ## Dynamic Path FIX

@objects_item.route("/object/item/html2text")
@login_required
@login_read_only
def html2text(): # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not item_basic.exist_item(item_id):
        abort(404)
    item = Item(item_id)
    return item.get_html2text_content()

@objects_item.route("/object/item/raw_content")
@login_required
@login_read_only
def item_raw_content(): # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not item_basic.exist_item(item_id):
        abort(404)
    item = Item(item_id)
    return Response(item.get_content(), mimetype='text/plain')

@objects_item.route("/object/item/download")
@login_required
@login_read_only
def item_download(): # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not item_basic.exist_item(item_id):
        abort(404)
    item = Item(item_id)
    return send_file(item.get_raw_content(), download_name=item_id, as_attachment=True)
