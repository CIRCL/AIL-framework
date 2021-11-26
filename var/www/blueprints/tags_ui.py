#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
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

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Date
import Tag

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import Correlate_object

r_cache = Flask_config.r_cache
r_serv_db = Flask_config.r_serv_db
r_serv_tags = Flask_config.r_serv_tags
bootstrap_label = Flask_config.bootstrap_label

# ============ BLUEPRINT ============
tags_ui = Blueprint('tags_ui', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/tags'))

# ============ VARIABLES ============



# ============ FUNCTIONS ============


# ============= ROUTES ==============
@tags_ui.route('/tag/add_tags')
@login_required
@login_analyst
def add_tags():

    tags = request.args.get('tags')
    tagsgalaxies = request.args.get('tagsgalaxies')
    object_id = request.args.get('object_id')
    object_type = request.args.get('object_type')

    list_tag = tags.split(',')
    list_tag_galaxies = tagsgalaxies.split(',')

    res = Tag.api_add_obj_tags(tags=list_tag, galaxy_tags=list_tag_galaxies, object_id=object_id, object_type=object_type)
    # error
    if res[1] != 200:
        return str(res[0])

    return redirect(Correlate_object.get_item_url(object_type, object_id))

@tags_ui.route('/tag/delete_tag')
@login_required
@login_analyst
def delete_tag():

    object_type = request.args.get('object_type')
    object_id = request.args.get('object_id')
    tag = request.args.get('tag')

    res = Tag.api_delete_obj_tags(tags=[tag], object_id=object_id, object_type=object_type)
    if res[1] != 200:
        return str(res[0])
    return redirect(Correlate_object.get_item_url(object_type, object_id))


@tags_ui.route('/tag/get_all_tags')
@login_required
@login_read_only
def get_all_tags():
    return jsonify(Tag.get_all_tags())

@tags_ui.route('/tag/get_all_obj_tags')
@login_required
@login_read_only
def get_all_obj_tags():
    object_type = request.args.get('object_type')
    res = Correlate_object.sanitize_object_type(object_type)
    if res:
        return jsonify(res)
    return jsonify(Tag.get_all_obj_tags(object_type))

@tags_ui.route('/tag/taxonomies/tags/enabled/json')
@login_required
@login_read_only
def tag_taxonomies_tags_enabled_json():
    return jsonify(Tag.get_taxonomies_enabled_tags(r_list=True))

@tags_ui.route('/tag/galaxies/tags/enabled/json')
@login_required
@login_read_only
def tag_galaxies_tags_enabled_json():
    tags = Tag.get_galaxies_enabled_tags()
    return jsonify(Tag.get_tags_selector_dict(tags))

@tags_ui.route('/tag/taxonomie/tags/enabled/json')
@login_required
@login_read_only
def tag_taxonomie_tags_enabled_json():
    taxonomie = request.args.get('taxonomie')
    return jsonify(Tag.get_taxonomie_enabled_tags(taxonomie, r_list=True))

@tags_ui.route('/tag/galaxy/tags/enabled/json')
@login_required
@login_read_only
def tag_galaxy_tags_enabled_json():
    galaxy = request.args.get('galaxy')
    tags = Tag.get_galaxy_enabled_tags(galaxy, r_list=True)
    return jsonify(Tag.get_tags_selector_dict(tags))

@tags_ui.route('/tag/search/item')
@login_required
@login_read_only
def tags_search_items():
    object_type = 'item'
    dict_tagged = {"object_type":object_type, "object_name":object_type.title() + "s"}
    dict_tagged['date'] = Date.sanitise_date_range('', '', separator='-')
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/domain')
@login_required
@login_read_only
def tags_search_domains():
    object_type = 'domain'
    dict_tagged = {"object_type":object_type, "object_name":object_type.title() + "s"}
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/decoded')
@login_required
@login_read_only
def tags_search_decoded():
    object_type = 'decoded'
    dict_tagged = {"object_type":object_type, "object_name":object_type.title() + "s"}
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/image')
@login_required
@login_read_only
def tags_search_images():
    object_type = 'image'
    dict_tagged = {"object_type":object_type, "object_name":object_type.title() + "s"}
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/get_obj_by_tags')
@login_required
@login_read_only
def get_obj_by_tags():

    # # TODO: sanityze all
    object_type = request.args.get('object_type')
    ltags = request.args.get('ltags')
    page = request.args.get('page')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # remove date separator
    if date_from:
        date_from = date_from.replace('-', '')
    if date_to:
        date_to = date_to.replace('-', '')

    # unpack tags
    list_tags = ltags.split(',')
    list_tag = []
    for tag in list_tags:
        list_tag.append(tag.replace('"','\"'))

    # object_type
    res = Correlate_object.sanitize_object_type(object_type)
    if res:
        return jsonify(res)

    # page
    try:
        page = int(page)
    except:
        page = 1

    dict_obj = Tag.get_obj_by_tags(object_type, list_tag, date_from=date_from, date_to=date_to, page=page)

    if dict_obj['tagged_obj']:
        dict_tagged = {"object_type":object_type, "object_name":object_type.title() + "s",
                        "tagged_obj":[], "page":dict_obj['page'] ,"nb_pages":dict_obj['nb_pages'],
                        "nb_first_elem":dict_obj['nb_first_elem'], "nb_last_elem":dict_obj['nb_last_elem'], "nb_all_elem":dict_obj['nb_all_elem']}

        for obj_id in dict_obj['tagged_obj']:
            obj_metadata = Correlate_object.get_object_metadata(object_type, obj_id)
            obj_metadata['id'] = obj_id
            dict_tagged["tagged_obj"].append(obj_metadata)

        dict_tagged['tab_keys'] = Correlate_object.get_obj_tag_table_keys(object_type)

        if len(list_tag) == 1:
            dict_tagged['current_tags'] = [ltags.replace('"', '\"')]
        else:
            dict_tagged['current_tags'] = list_tag
        dict_tagged['current_tags_str'] = ltags

        #return jsonify(dict_tagged)
    else:
        dict_tagged = {"object_type":object_type, "object_name":object_type.title() + "s"}

    if 'date' in dict_obj:
        dict_tagged['date'] = dict_obj['date']

    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)
