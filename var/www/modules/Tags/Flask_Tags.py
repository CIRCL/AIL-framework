#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for

from Role_Manager import login_admin, login_analyst, login_read_only
from flask_login import login_required

import json
import datetime

from pytaxonomies import Taxonomies
from pymispgalaxies import Galaxies, Clusters

# ============ VARIABLES ============
import Flask_config
from lib import Tag

app = Flask_config.app
baseUrl = Flask_config.baseUrl
r_serv_tags = Flask_config.r_serv_tags

Tags = Blueprint('Tags', __name__, template_folder='templates')

# ============ FUNCTIONS ============

# TODO:
# TODO:
# TODO:
# TODO:
# TODO:
# TODO:
# # TODO: replace me with get_tag_selector_dict()
def get_tags_with_synonyms(tag):
    str_synonyms = ' - synonyms: '
    synonyms = r_serv_tags.smembers('synonym_tag_' + tag)
    # synonyms to display
    for synonym in synonyms:
        str_synonyms = str_synonyms + synonym + ', '
    # add real tag
    if str_synonyms != ' - synonyms: ':
        return {'name':tag + str_synonyms,'id':tag}
    else:
        return {'name':tag,'id':tag}





# ============= ROUTES ==============

@Tags.route("/Tags/get_all_tags_taxonomies")
@login_required
@login_read_only
def get_all_tags_taxonomies():

    active_taxonomie = r_serv_tags.smembers('active_taxonomies')

    list_tags = []
    for taxonomie in active_taxonomie:
        # l_tags = taxonomies.get(taxonomie).machinetags()
        l_tags = r_serv_tags.smembers('active_tag_' + taxonomie)
        for tag in l_tags:
            list_tags.append( tag )

    return jsonify(list_tags)

@Tags.route("/Tags/get_all_tags_galaxies")
@login_required
@login_read_only
def get_all_tags_galaxy():

    active_galaxies = r_serv_tags.smembers('active_galaxies')

    list_tags = []
    for galaxy in active_galaxies:
        l_tags = r_serv_tags.smembers('active_tag_galaxies_' + galaxy)
        for tag in l_tags:
            list_tags.append(get_tags_with_synonyms(tag))

    return jsonify(list_tags)

@Tags.route("/Tags/get_tags_taxonomie")
@login_required
@login_read_only
def get_tags_taxonomie():

    taxonomie = request.args.get('taxonomie')

    taxonomies = Taxonomies()
    list_taxonomies = list(taxonomies.keys())

    active_taxonomie = r_serv_tags.smembers('active_taxonomies')

    #verify input
    if taxonomie in list_taxonomies:
        if taxonomie in active_taxonomie:

            list_tags = []
            l_tags = r_serv_tags.smembers('active_tag_' + taxonomie)
            for tag in l_tags:
                list_tags.append( tag )

            return jsonify(list_tags)

        else:
            return 'this taxonomie is disable'
    else:
        return 'INCORRECT INPUT'

@Tags.route("/Tags/get_tags_galaxy")
@login_required
@login_read_only
def get_tags_galaxy():

    galaxy = request.args.get('galaxy')

    active_galaxies = r_serv_tags.smembers('active_galaxies')

    #verify input
    if galaxy in active_galaxies:

        list_tags = []
        l_tags = r_serv_tags.smembers('active_tag_galaxies_' + galaxy)
        for tag in l_tags:
            list_tags.append(get_tags_with_synonyms(tag))

        return jsonify(list_tags)

    else:
        return 'this galaxy is disable'

# @Tags.route("/Tags/tag_validation")
# @login_required
# @login_analyst
# def tag_validation():
#
#     path = request.args.get('paste')
#     tag = request.args.get('tag')
#     status = request.args.get('status')
#
#     if (status == 'fp' or status == 'tp') and r_serv_tags.sismember('list_tags', tag):
#
#         if status == 'tp':
#             r_serv_statistics.sadd('tp:'+tag, path)
#             r_serv_statistics.srem('fp:'+tag, path)
#         else:
#             r_serv_statistics.sadd('fp:'+tag, path)
#             r_serv_statistics.srem('tp:'+tag, path)
#
#         return redirect(url_for('objects_item.showItem', id=path))
#     else:
#         return 'input error'










# ========= REGISTRATION =========
app.register_blueprint(Tags, url_prefix=baseUrl)
