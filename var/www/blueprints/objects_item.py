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

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item
import Tag

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'export'))
import Export

# ============ BLUEPRINT ============
objects_item = Blueprint('objects_item', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/item'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============


# ============= ROUTES ==============
@objects_item.route("/object/item") #completely shows the paste in a new tab
@login_required
@login_read_only
def showItem(): # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not Item.exist_item(item_id):
        abort(404)

    dict_item = {}
    dict_item['id'] = item_id
    dict_item['name'] = dict_item['id'].replace('/', ' / ')
    dict_item['father'] = Item.get_item_parent(item_id)
    dict_item['content'] = Item.get_item_content(item_id)
    dict_item['metadata'] = Item.get_item_metadata(item_id, item_content=dict_item['content'])
    dict_item['tags'] = Tag.get_obj_tag(item_id)
    #dict_item['duplicates'] = Item.get_item_nb_duplicates(item_id)
    dict_item['duplicates'] = Item.get_item_duplicates_dict(item_id)
    dict_item['crawler'] = Item.get_crawler_matadata(item_id, ltags=dict_item['tags'])

    ## EXPORT SECTION
    # # TODO: ADD in Export SECTION
    dict_item['hive_case'] = Export.get_item_hive_cases(item_id)

    return render_template("show_item.html", bootstrap_label=bootstrap_label,
                            modal_add_tags=Tag.get_modal_add_tags(dict_item['id'], object_type='item'),
                            is_hive_connected=Export.get_item_hive_cases(item_id),
                            dict_item=dict_item)

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
    if not item_id or not Item.exist_item(item_id):
        abort(404)
    return Item.get_item_content_html2text(item_id)

@objects_item.route("/object/item/raw_content")
@login_required
@login_read_only
def item_raw_content(): # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not Item.exist_item(item_id):
        abort(404)
    return Response(Item.get_item_content(item_id), mimetype='text/plain')

@objects_item.route("/object/item/download")
@login_required
@login_read_only
def item_download(): # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not Item.exist_item(item_id):
        abort(404)
    return send_file(Item.get_raw_content(item_id), attachment_filename=item_id, as_attachment=True)
