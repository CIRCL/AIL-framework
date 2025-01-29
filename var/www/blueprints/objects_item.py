#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import difflib
import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file, send_from_directory
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_user, login_read_only, no_cache

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader
from lib import chats_viewer
from lib import item_basic
from lib.objects.Items import Item
from lib.objects.Screenshots import Screenshot
from lib import Tag

from lib import Investigations
from lib import module_extractor


# ============ BLUEPRINT ============
objects_item = Blueprint('objects_item', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/item'))

# ============ VARIABLES ============
config_loader = ConfigLoader.ConfigLoader()
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']
DiffMaxLineLength = config_loader.get_config_int('Flask', 'DiffMaxLineLength')
max_preview_modal = config_loader.get_config_int('Flask', 'max_preview_modal')
SCREENSHOT_FOLDER = ConfigLoader.get_screenshots_dir()
config_loader = None

# ============ FUNCTIONS ============


# ============= ROUTES ==============

@objects_item.route('/screenshot/<path:filename>')
@login_required
@login_read_only
@no_cache
def screenshot(filename):
    if not filename:
        abort(404)
    if not 64 <= len(filename) <= 70:
        abort(404)
    filename = filename.replace('/', '')
    s = Screenshot(filename)
    return send_from_directory(SCREENSHOT_FOLDER, s.get_rel_path(add_extension=True), as_attachment=False, mimetype='image')

@objects_item.route("/object/item")
@login_required
@login_read_only
def showItem():  # # TODO: support post
    user_org = current_user.get_org()
    item_id = request.args.get('id')
    if not item_id or not item_basic.exist_item(item_id):
        abort(404)

    item = Item(item_id)
    meta = item.get_meta(options={'content', 'crawler', 'duplicates', 'file_name', 'investigations', 'lines', 'size'})
    if meta['file_name']:
        message = chats_viewer.api_get_message(item.get_message())
        if message[1] == 200:
            message = message[0]
        else:
            message = None
    else:
        message = None

    meta['name'] = meta['id'].replace('/', ' / ')
    meta['father'] = item_basic.get_item_parent(item_id)
    ## EXPORT SECTION
    # # TODO: ADD in Export SECTION
    # meta['hive_case'] = Export.get_item_hive_cases(item_id)
    meta['hive_case'] = None

    if meta.get('investigations'):
        invests = []
        for investigation_uuid in meta['investigations']:
            inv = Investigations.Investigation(investigation_uuid)
            if not inv.check_level(user_org):
                continue

            invests.append(inv.get_metadata(r_str=True))
        meta['investigations'] = invests
    else:
        meta['investigations'] = []

    extracted = module_extractor.extract(current_user.get_user_id(), 'item', '', item.id, content=meta['content'])
    extracted_matches = module_extractor.get_extracted_by_match(extracted)

    return render_template("show_item.html", bootstrap_label=bootstrap_label,
                           modal_add_tags=Tag.get_modal_add_tags(meta['id'], object_type='item'),
                           is_hive_connected=False,
                           meta=meta, message=message,
                           extracted=extracted, extracted_matches=extracted_matches)

    # kvrocks data

    # # TODO: dynamic load:
    ## duplicates
    ## correlations

    ## Dynamic Path FIX

@objects_item.route("/objects/item/html2text")
@login_required
@login_read_only
def html2text(): # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not item_basic.exist_item(item_id):
        abort(404)
    item = Item(item_id)
    return item.get_html2text_content()

@objects_item.route("/objects/item/raw_content")
@login_required
@login_read_only
def item_raw_content(): # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not item_basic.exist_item(item_id):
        abort(404)
    item = Item(item_id)
    return Response(item.get_content(), mimetype='text/plain')

@objects_item.route("/objects/item/download")
@login_required
@login_read_only
def item_download():  # # TODO: support post
    item_id = request.args.get('id')
    if not item_id or not item_basic.exist_item(item_id):
        abort(404)
    item = Item(item_id)
    return send_file(item.get_raw_content(), download_name=item_id, as_attachment=True)

@objects_item.route("/objects/item/content/more")
@login_required
@login_read_only
def item_content_more():
    item_id = request.args.get('id', '')
    item = Item(item_id)
    item_content = item.get_content()
    to_return = item_content[max_preview_modal-1:]
    return to_return

@objects_item.route("/objects/item/diff")
@login_required
@login_user
def object_item_diff():
    id1 = request.args.get('s1', '')
    id2 = request.args.get('s2', '')
    item1 = Item(id1)
    item2 = Item(id2)
    item1_content = item1.get_content()
    item2_content = item2.get_content()
    i1_max_len = item1.get_meta_lines(content=item1_content)['max_length']
    i2_max_len = item2.get_meta_lines(content=item2_content)['max_length']
    if i1_max_len > DiffMaxLineLength or i2_max_len > DiffMaxLineLength:
        return jsonify({'error': "Can't make the difference as the lines are too long."}), 400
    lines1 = item1_content.splitlines()
    lines2 = item2_content.splitlines()
    htmldiff = difflib.HtmlDiff()
    diff = htmldiff.make_file(lines1, lines2)
    return diff

@objects_item.route("/objects/item/preview")
@login_required
@login_read_only
def item_preview():
    item_id = request.args.get('id')
    if not item_id or not item_basic.exist_item(item_id):
        abort(404)

    item = Item(item_id)
    meta = item.get_meta(options={'content', 'crawler', 'lines', 'mimetype', 'parent', 'size'})
    initsize = len(meta['content'])
    if len(meta['content']) > max_preview_modal:
        meta['content'] = meta['content'][0:max_preview_modal]
    meta['nb_correlations'] = item.get_nb_correlations()

    misp_eventid = None  # TODO SHOW MISP EVENT
    misp_url = None  # TODO SHOW MISP EVENT
    hive_caseid = None  # TODO SHOW HIVE CASE
    hive_url = None  # TODO SHOW HIVE CASE

    return render_template("show_item_min.html", bootstrap_label=bootstrap_label,
                           meta=meta, initsize=initsize,

                           misp_eventid=misp_eventid, misp_url=misp_url,
                           hive_caseid=hive_caseid, hive_url=hive_url)

