#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json
import random

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort
from flask_login import login_required, current_user, login_user, logout_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import create_user_db, check_password_strength, check_user_role_integrity
from Role_Manager import login_admin, login_analyst

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import Correlate_object
import Domain

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Cryptocurrency
import Pgp
import Decoded

bootstrap_label = Flask_config.bootstrap_label
vt_enabled = Flask_config.vt_enabled

# ============ BLUEPRINT ============
correlation = Blueprint('correlation', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/correlation'))

# ============ VARIABLES ============

######
### graph_line_json
### 'hashDecoded.pgpdump_graph_line_json'
### 'hashDecoded.cryptocurrency_graph_line_json'
###
######

# ============ FUNCTIONS ============

def sanitise_graph_mode(graph_mode):
    if graph_mode not in ('inter', 'union'):
        return 'union'
    else:
        return graph_mode

def sanitise_nb_max_nodes(nb_max_nodes):
    try:
        nb_max_nodes = int(nb_max_nodes)
        if nb_max_nodes < 2:
            nb_max_nodes = 300
    except:
        nb_max_nodes = 300
    return nb_max_nodes

def sanitise_correlation_names(correlation_names):
    '''
    correlation_names ex = 'pgp,crypto'
    '''
    all_correlation_names = Correlate_object.get_all_correlation_names()
    if correlation_names is None:
        return all_correlation_names
    else:
        l_correlation_names = []
        for correl in correlation_names.split(','):
            if correl in all_correlation_names:
                l_correlation_names.append(correl)
        if l_correlation_names:
            return l_correlation_names
        else:
            return all_correlation_names

def sanitise_correlation_objects(correlation_objects):
    '''
    correlation_objects ex = 'domain,decoded'
    '''
    all_correlation_objects = Correlate_object.get_all_correlation_objects()
    if correlation_objects is None:
        return all_correlation_objects
    else:
        l_correlation_objects = []
        for correl in correlation_objects.split(','):
            if correl in all_correlation_objects:
                l_correlation_objects.append(correl)
        if l_correlation_objects:
            return l_correlation_objects
        else:
            return all_correlation_objects

def get_card_metadata(object_type, correlation_id, type_id=None):
    card_dict = {}
    if object_type == 'cryptocurrency':
        card_dict["sparkline"] = Cryptocurrency.cryptocurrency.get_list_nb_previous_correlation_object(type_id, correlation_id, 6)
        card_dict["icon"] = Correlate_object.get_correlation_node_icon(object_type, type_id)
    elif object_type == 'pgp':
        card_dict["sparkline"] = Pgp.pgp.get_list_nb_previous_correlation_object(type_id, correlation_id, 6)
        card_dict["icon"] = Correlate_object.get_correlation_node_icon(object_type, type_id)
    elif object_type == 'decoded':
        card_dict["sparkline"] = Decoded.get_list_nb_previous_hash(correlation_id, 6)
        card_dict["icon"] = Correlate_object.get_correlation_node_icon(object_type, value=correlation_id)
        card_dict["vt"] = Decoded.get_decoded_vt_report(correlation_id)
        card_dict["vt"]["status"] = vt_enabled
    elif object_type == 'domain':
        card_dict["icon"] = Correlate_object.get_correlation_node_icon(object_type, value=correlation_id)
        card_dict["tags"] = Domain.get_domain_tags(correlation_id)
    elif object_type == 'paste':
        card_dict["icon"] = Correlate_object.get_correlation_node_icon(object_type, value=correlation_id)
    return card_dict

# ============= ROUTES ==============
@correlation.route('/correlation/show_correlation', methods=['GET', 'POST']) # GET + POST
@login_required
@login_analyst
def show_correlation():
    if request.method == 'POST':
        object_type = request.form.get('object_type')
        type_id = request.form.get('type_id')
        correlation_id = request.form.get('correlation_id')
        max_nodes = request.form.get('max_nb_nodes_in')
        mode = request.form.get('mode')
        if mode:
            mode = 'inter'
        else:
            mode = 'union'

        ## get all selected correlations
        correlation_names = []
        correlation_objects = []
        #correlation_names
        correl_option = request.form.get('CryptocurrencyCheck')
        if correl_option:
            correlation_names.append('cryptocurrency')
        correl_option = request.form.get('PgpCheck')
        if correl_option:
            correlation_names.append('pgp')
        correl_option = request.form.get('DecodedCheck')
        if correl_option:
            correlation_names.append('decoded')
        # correlation_objects
        correl_option = request.form.get('DomainCheck')
        if correl_option:
            correlation_objects.append('domain')
        correl_option = request.form.get('PasteCheck')
        if correl_option:
            correlation_objects.append('paste')

        # list as params
        correlation_names = ",".join(correlation_names)
        correlation_objects = ",".join(correlation_objects)

        # redirect to keep history and bookmark
        return redirect(url_for('correlation.show_correlation', object_type=object_type, type_id=type_id, correlation_id=correlation_id, mode=mode,
                                            max_nodes=max_nodes, correlation_names=correlation_names, correlation_objects=correlation_objects))

    # request.method == 'GET'
    else:
        object_type = request.args.get('object_type')
        type_id = request.args.get('type_id')
        correlation_id = request.args.get('correlation_id')
        max_nodes = sanitise_nb_max_nodes(request.args.get('max_nodes'))
        mode = sanitise_graph_mode(request.args.get('mode'))

        correlation_names = sanitise_correlation_names(request.args.get('correlation_names'))
        correlation_objects = sanitise_correlation_objects(request.args.get('correlation_objects'))

        # check if correlation_id exist
        if not Correlate_object.exist_object(object_type, correlation_id, type_id=type_id):
            abort(404) # return 404
        # oject exist
        else:
            dict_object = {"object_type": object_type, "correlation_id": correlation_id}
            dict_object["max_nodes"] = max_nodes
            dict_object["mode"] = mode
            dict_object["correlation_names"] = correlation_names
            dict_object["correlation_names_str"] = ",".join(correlation_names)
            dict_object["correlation_objects"] = correlation_objects
            dict_object["correlation_objects_str"] = ",".join(correlation_objects)
            dict_object["metadata"] = Correlate_object.get_object_metadata(object_type, correlation_id, type_id=type_id)
            if type_id:
                dict_object["metadata"]['type_id'] = type_id
            dict_object["metadata_card"] = get_card_metadata(object_type, correlation_id, type_id=type_id)
            return render_template("show_correlation.html", dict_object=dict_object, bootstrap_label=bootstrap_label)


@correlation.route('/correlation/graph_node_json')
@login_required
@login_analyst
def graph_node_json(): # # TODO: use post
    correlation_id = request.args.get('correlation_id')
    type_id = request.args.get('type_id')
    object_type = request.args.get('object_type')
    max_nodes = sanitise_nb_max_nodes(request.args.get('max_nodes'))

    correlation_names = sanitise_correlation_names(request.args.get('correlation_names'))
    correlation_objects = sanitise_correlation_objects(request.args.get('correlation_objects'))

    mode = sanitise_graph_mode(request.args.get('mode'))

    res = Correlate_object.get_graph_node_object_correlation(object_type, correlation_id, mode, correlation_names, correlation_objects, requested_correl_type=type_id, max_nodes=max_nodes)
    return jsonify(res)
