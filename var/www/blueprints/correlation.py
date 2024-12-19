#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort
from flask_login import login_required

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import login_admin, login_read_only


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import ail_objects
from lib import chats_viewer
from lib import Tag

bootstrap_label = Flask_config.bootstrap_label
vt_enabled = Flask_config.vt_enabled

# ============ BLUEPRINT ============
correlation = Blueprint('correlation', __name__,
                        template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/correlation'))

# ============ VARIABLES ============

# ============ FUNCTIONS ============

def sanitise_graph_mode(graph_mode):
    if graph_mode not in ('inter', 'union'):
        return 'union'
    else:
        return graph_mode

def sanitise_nb_max_nodes(nb_max_nodes):
    try:
        nb_max_nodes = int(nb_max_nodes)
        if nb_max_nodes < 2 and nb_max_nodes != 0:
            nb_max_nodes = 300
    except (TypeError, ValueError):
        nb_max_nodes = 300
    return nb_max_nodes

def sanitise_level(level):
    try:
        level = int(level)
        if level < 0:
            level = 2
    except (TypeError, ValueError):
        level = 2
    return level

def sanitise_objs_hidden(objs_hidden):
    if objs_hidden:
        objs_hidden = set(objs_hidden.split(','))  # TODO sanitize objects
    else:
        objs_hidden = set()
    return objs_hidden

# ============= ROUTES ==============
@correlation.route('/correlation/show', methods=['GET', 'POST'])
@login_required
@login_read_only
def show_correlation():
    if request.method == 'POST':
        object_type = request.form.get('obj_type')
        subtype = request.form.get('subtype')
        obj_id = request.form.get('obj_id')
        max_nodes = request.form.get('max_nb_nodes_in')
        mode = request.form.get('mode')
        if mode:
            mode = 'inter'
        else:
            mode = 'union'
        level = sanitise_level(request.form.get('level'))

        ## get all selected correlations
        filter_types = []
        for ob_type in ail_objects.get_all_objects():
            correl_option = request.form.get(f'{ob_type}_Check')
            if correl_option:
                filter_types.append(ob_type)

        # list as params
        filter_types = ",".join(filter_types)

        # redirect to keep history and bookmark
        return redirect(url_for('correlation.show_correlation', type=object_type, subtype=subtype, id=obj_id, mode=mode,
                                max_nodes=max_nodes, level=level, filter=filter_types))

    # request.method == 'GET'
    else:
        obj_type = request.args.get('type')
        subtype = request.args.get('subtype', '')
        obj_id = request.args.get('id')
        max_nodes = sanitise_nb_max_nodes(request.args.get('max_nodes'))
        mode = sanitise_graph_mode(request.args.get('mode'))
        level = sanitise_level(request.args.get('level'))
        objs_hidden = sanitise_objs_hidden(request.args.get('hidden'))
        obj_to_hide = request.args.get('hide')
        if obj_to_hide:
            objs_hidden.add(obj_to_hide)

        related_btc = bool(request.args.get('related_btc', False))

        filter_types = ail_objects.sanitize_objs_types(request.args.get('filter', '').split(','), default=True)

        # check if obj_id exist
        if not ail_objects.exists_obj(obj_type, subtype, obj_id):
            return abort(404)
        # object exist
        else: # TODO remove old dict key
            dict_object = {"type": obj_type,
                           "id": obj_id,
                           "object_type": obj_type,
                           "max_nodes": max_nodes, "mode": mode, "level": level,
                           "filter": filter_types, "filter_str": ",".join(filter_types),
                           "hidden": objs_hidden, "hidden_str": ",".join(objs_hidden),

                           "correlation_id": obj_id,
                           "metadata": ail_objects.get_object_meta(obj_type, subtype, obj_id,
                                                                   options={'tags'}, flask_context=True),
                           "nb_correl": ail_objects.get_obj_nb_correlations(obj_type, subtype, obj_id)
                           }
            if subtype:
                dict_object["subtype"] = subtype
                dict_object["metadata"]['type_id'] = subtype
            else:
                dict_object["subtype"] = ''
            dict_object["metadata_card"] = ail_objects.get_object_card_meta(obj_type, subtype, obj_id, related_btc=related_btc)
            dict_object["metadata_card"]['tags_safe'] = True
            return render_template("show_correlation.html", dict_object=dict_object, bootstrap_label=bootstrap_label,
                                   tags_selector_data=Tag.get_tags_selector_data(),
                                   meta=dict_object["metadata_card"],
                                   ail_tags=dict_object["metadata_card"]["add_tags_modal"])

@correlation.route('/correlation/get/description')
@login_required
@login_read_only
def get_description():
    object_id = request.args.get('object_id')
    obj_type, subtype, obj_id = ail_objects.get_obj_type_subtype_id_from_global_id(object_id)

    # check if obj exist
    # # TODO: return error json
    if not ail_objects.exists_obj(obj_type, subtype, obj_id):
        return Response(json.dumps({"status": "error", "reason": "404 Not Found"}, indent=2, sort_keys=True), mimetype='application/json'), 404
    # object exist
    else:
        options = {'icon', 'tags', 'tags_safe'}
        if obj_type == 'message':
            options.add('content')
            options.add('chat')
        res = ail_objects.get_object_meta(obj_type, subtype, obj_id, options=options,
                                          flask_context=True)
        if 'tags' in res:
            res['tags'] = list(res['tags'])

        if obj_type == 'message':
            chat_id = res['chat']
            subtype = object_id[9:].split('/', 1)[0]
            meta_chats = ail_objects.get_object_meta('chat', subtype, chat_id, options={'username', 'str_username'})
            if meta_chats["username"]:
                res['chat'] = f'{meta_chats["username"]} - {meta_chats["name"]}'
            else:
                res['chat'] = f'{meta_chats["name"]}'

        return jsonify(res)

@correlation.route('/correlation/graph_node_json')
@login_required
@login_read_only
def graph_node_json():
    obj_id = request.args.get('id')
    subtype = request.args.get('subtype')
    obj_type = request.args.get('type')
    max_nodes = sanitise_nb_max_nodes(request.args.get('max_nodes'))
    level = sanitise_level(request.args.get('level'))

    hidden = request.args.get('hidden')
    if hidden:
        hidden = set(hidden.split(','))
    else:
        hidden = set()

    filter_types = ail_objects.sanitize_objs_types(request.args.get('filter', '').split(','))

    json_graph = ail_objects.get_correlations_graph_node(obj_type, subtype, obj_id, filter_types=filter_types, max_nodes=max_nodes, level=level, objs_hidden=hidden, flask_context=True)
    #json_graph = Correlate_object.get_graph_node_object_correlation(obj_type, obj_id, 'union', correlation_names, correlation_objects, requested_correl_type=subtype, max_nodes=max_nodes)
    return jsonify(json_graph)

@correlation.route('/correlation/delete', methods=['GET'])
@login_required
@login_admin
def correlation_delete():
    obj_type = request.args.get('type')
    subtype = request.args.get('subtype', '')
    obj_id = request.args.get('id')

    if not ail_objects.exists_obj(obj_type, subtype, obj_id):
        return abort(404)

    ail_objects.delete_obj_correlations(obj_type, subtype, obj_id)
    return redirect(url_for('correlation.show_correlation', type=obj_type, subtype=subtype, id=obj_id))

@correlation.route('/correlation/tags/add', methods=['POST'])
@login_required
@login_admin
def correlation_tags_add():
    obj_id = request.form.get('tag_obj_id')
    subtype = request.form.get('tag_subtype', '')
    obj_type = request.form.get('tag_obj_type')
    nb_max = sanitise_nb_max_nodes(request.form.get('tag_nb_max'))
    level = sanitise_level(request.form.get('tag_level'))
    filter_types = ail_objects.sanitize_objs_types(request.form.get('tag_filter', '').split(','))
    hidden = sanitise_objs_hidden(request.form.get('tag_hidden'))

    if not ail_objects.exists_obj(obj_type, subtype, obj_id):
        return abort(404)

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
    if taxonomies_tags or galaxies_tags:
        if not Tag.is_valid_tags_taxonomies_galaxy(taxonomies_tags, galaxies_tags):
            return {'error': 'Invalid tag(s)'}, 400
        tags = taxonomies_tags + galaxies_tags
    else:
        tags = []

    if tags:
        ail_objects.obj_correlations_objs_add_tags(obj_type, subtype, obj_id, tags, filter_types=filter_types,
                                                   objs_hidden=hidden,
                                                   lvl=level + 1, nb_max=nb_max)
    return redirect(url_for('correlation.show_correlation',
                            type=obj_type, subtype=subtype, id=obj_id,
                            level=level,
                            max_nodes=nb_max,
                            hidden=hidden, hidden_str=",".join(hidden),
                            filter=",".join(filter_types)))

#####################################################################################

@correlation.route('/relationships/graph_node_json')
@login_required
@login_read_only
def relationships_graph_node_json():
    obj_id = request.args.get('id')
    subtype = request.args.get('subtype')
    obj_type = request.args.get('type')
    max_nodes = sanitise_nb_max_nodes(request.args.get('max_nodes'))
    level = sanitise_level(request.args.get('level'))

    filter_types = ail_objects.sanitize_objs_types(request.args.get('filter', '').split(','))
    relationships = ail_objects.sanitize_relationships(request.args.get('relationships', '').split(','))

    json_graph = ail_objects.get_relationships_graph_node(obj_type, subtype, obj_id, relationships=relationships, filter_types=filter_types, max_nodes=max_nodes, level=level, flask_context=True)
    return jsonify(json_graph)

@correlation.route('/relationships/chord_graph_json')
@login_required
@login_read_only
def relationships_chord_graph_json():
    obj_id = request.args.get('id')
    subtype = request.args.get('subtype')
    obj_type = request.args.get('type')

    chat_json_graph = ail_objects.get_chat_relationships_cord_graph(obj_type, subtype, obj_id)
    meta = chats_viewer.enrich_chat_relationships_labels(chat_json_graph)

    return jsonify({'meta': meta, 'data': chat_json_graph})

@correlation.route('/relationships/chord_mentions_graph_json')
@login_required
@login_read_only
def relationships_chord_mentions_graph_json():
    obj_id = request.args.get('id')
    subtype = request.args.get('subtype')
    obj_type = request.args.get('type')

    chat_json_graph = ail_objects.get_chat_relationships_mentions_cord_graph(obj_type, subtype, obj_id)
    meta = chats_viewer.enrich_chat_relationships_labels(chat_json_graph)

    return jsonify({'meta': meta, 'data': chat_json_graph})

@correlation.route('/relationship/show', methods=['GET', 'POST'])
@login_required
@login_read_only
def show_relationship():
    if request.method == 'POST':
        object_type = request.form.get('obj_type')
        subtype = request.form.get('subtype')
        obj_id = request.form.get('obj_id')
        max_nodes = request.form.get('max_nb_nodes_in')
        level = sanitise_level(request.form.get('level'))

        ## get all selected relationships
        relationships = []
        for relationship in ail_objects.get_relationships():
            rel_option = request.form.get(f'relationship_{relationship}_Check')
            if rel_option:
                relationships.append(relationship)

        relationships = ",".join(relationships)

        ## get all selected objects types
        filter_types = []
        for ob_type in ail_objects.get_all_objects():
            correl_option = request.form.get(f'{ob_type}_Check')
            if correl_option:
                filter_types.append(ob_type)

        # list as params
        filter_types = ",".join(filter_types)

        # redirect to keep history and bookmark
        return redirect(url_for('correlation.show_relationship', type=object_type, subtype=subtype, id=obj_id,
                                filter=filter_types, relationships=relationships,
                                max_nodes=max_nodes, level=level))

    # request.method == 'GET'
    else:
        obj_type = request.args.get('type')
        subtype = request.args.get('subtype', '')
        obj_id = request.args.get('id')
        max_nodes = sanitise_nb_max_nodes(request.args.get('max_nodes'))
        level = sanitise_level(request.args.get('level'))

        filter_types = ail_objects.sanitize_objs_types(request.args.get('filter', '').split(','), default=True)
        relationships = ail_objects.sanitize_relationships(request.args.get('relationships', '').split(','))

        # check if obj_id exist
        if not ail_objects.exists_obj(obj_type, subtype, obj_id):
            return abort(404)
        # object exist
        else: # TODO remove old dict key
            dict_object = {"type": obj_type,
                           "id": obj_id,
                           "object_type": obj_type,
                           "max_nodes": max_nodes, "level": level,
                           "correlation_id": obj_id,
                           "relationships": relationships, "relationships_str": ",".join(relationships),
                           "filter": filter_types, "filter_str": ",".join(filter_types),
                           "metadata": ail_objects.get_object_meta(obj_type, subtype, obj_id, options={'tags', 'info', 'icon', 'username'}, flask_context=True),
                           "nb_relation": ail_objects.get_obj_nb_relationships(obj_type, subtype, obj_id)
                           }
            if subtype:
                dict_object["subtype"] = subtype
                dict_object["metadata"]['type_id'] = subtype
            else:
                dict_object["subtype"] = ''
            dict_object["metadata_card"] = ail_objects.get_object_card_meta(obj_type, subtype, obj_id)
            dict_object["metadata_card"]['tags_safe'] = True
            return render_template("show_relationship.html", dict_object=dict_object, bootstrap_label=bootstrap_label,
                                   tags_selector_data=Tag.get_tags_selector_data(),
                                   meta=dict_object["metadata_card"],
                                   ail_tags=dict_object["metadata_card"]["add_tags_modal"])

