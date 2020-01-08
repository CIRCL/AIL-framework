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
from Role_Manager import login_admin, login_analyst

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

# # add route : /crawlers/show_domain
# @tags_ui.route('/tags/search/domain')
# @login_required
# @login_analyst
# def showDomain():
#     date_from = request.args.get('date_from')
#     date_to = request.args.get('date_to')
#     tags = request.args.get('ltags')
#
#     print(date_from)
#     print(date_to)
#
#     dates = Date.sanitise_date_range(date_from, date_to)
#
#     if tags is None:
#         return 'tags_none'
#         #return render_template("Tags.html", date_from=dates['date_from'], date_to=dates['date_to'])
#     else:
#         tags = Tag.unpack_str_tags_list(tags)
#
#
#
#
#     return render_template("showDomain.html", dict_domain=dict_domain, bootstrap_label=bootstrap_label,
#                                 tag_type="domain"))
