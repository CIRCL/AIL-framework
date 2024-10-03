#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, abort
from flask_login import login_required

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import login_admin, login_user_no_api, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from packages import Date
from lib import Tag
from lib.objects import ail_objects

bootstrap_label = Flask_config.bootstrap_label

# ============ BLUEPRINT ============
tags_ui = Blueprint('tags_ui', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/tags'))

# ============ VARIABLES ============



# ============ FUNCTIONS ============


# ============= ROUTES ==============
@tags_ui.route('/tag/taxonomies')
@login_required
@login_read_only
def tags_taxonomies():
    taxonomies = Tag.get_taxonomies_meta()
    return render_template("tags/taxonomies.html", taxonomies=taxonomies)

@tags_ui.route('/tag/taxonomy')
@login_required
@login_read_only
def tags_taxonomy():
    taxonomy_name = request.args.get('taxonomy')
    taxonomy = Tag.get_taxonomy_meta(taxonomy_name, enabled=True, predicates=True, tags=True, enabled_tags=True)
    if not taxonomy:
        abort(404)
    return render_template("tags/taxonomy.html", taxonomy=taxonomy)

@tags_ui.route('/tag/taxonomy/enable')
@login_required
@login_admin
def taxonomy_enable():
    taxonomy = request.args.get('taxonomy')
    res = Tag.api_enable_taxonomy_tags({'taxonomy': taxonomy})
    if res:
        return jsonify(res[0]), res[1]
    else:
        return redirect(url_for('tags_ui.tags_taxonomy', taxonomy=taxonomy))

@tags_ui.route('/tag/taxonomy/disable')
@login_required
@login_admin
def taxonomy_disable():
    taxonomy = request.args.get('taxonomy')
    res = Tag.api_disable_taxonomy_tags({'taxonomy': taxonomy})
    if res:
        return jsonify(res[0]), res[1]
    else:
        return redirect(url_for('tags_ui.tags_taxonomy', taxonomy=taxonomy))

@tags_ui.route('/tag/taxonomy/enable_tags')
@login_required
@login_admin
def taxonomy_enable_tags():
    taxonomy = request.args.get('taxonomy')
    tags = request.args.getlist('tags')
    res = Tag.api_update_taxonomy_tag_enabled({'taxonomy': taxonomy, 'tags': tags})
    if res:
        return jsonify(res[0]), 1
    else:
        return redirect(url_for('tags_ui.tags_taxonomy', taxonomy=taxonomy))

@tags_ui.route('/tag/galaxies')
@login_required
@login_read_only
def tags_galaxies():
    galaxies = Tag.get_galaxies_meta()
    return render_template("tags/galaxies.html", galaxies=galaxies)

@tags_ui.route('/tag/galaxy')
@login_required
@login_read_only
def tags_galaxy():
    galaxy_name = request.args.get('galaxy')
    galaxy = Tag.get_cluster_meta(galaxy_name, enabled=True, tags=True)
    if not galaxy:
        abort(404)
    return render_template("tags/galaxy.html", galaxy=galaxy)

@tags_ui.route('/tag/galaxy/tag')
@login_required
@login_read_only
def tags_galaxy_tag():
    galaxy_type = request.args.get('galaxy')
    tag = request.args.get('tag')
    tag_meta = Tag.get_galaxy_tag_meta(galaxy_type, tag)
    if not tag_meta:
        abort(404)
    return render_template("tags/galaxy_tag.html", galaxy=galaxy_type, tag=tag_meta)

@tags_ui.route('/tag/galaxy/enable')
@login_required
@login_admin
def galaxy_enable():
    galaxy = request.args.get('galaxy')
    res = Tag.api_enable_galaxy_tags({'galaxy': galaxy})
    if res:
        return jsonify(res[0]), res[1]
    else:
        return redirect(url_for('tags_ui.tags_galaxy', galaxy=galaxy))

@tags_ui.route('/tag/galaxy/disable')
@login_required
@login_admin
def galaxy_disable():
    galaxy = request.args.get('galaxy')
    res = Tag.api_disable_galaxy_tags({'galaxy': galaxy})
    if res:
        return jsonify(res[0]), res[1]
    else:
        return redirect(url_for('tags_ui.tags_galaxy', galaxy=galaxy))

@tags_ui.route('/tag/galaxy/enable_tags')
@login_required
@login_admin
def galaxy_enable_tags():
    galaxy = request.args.get('galaxy')
    tags = request.args.getlist('tags')
    res = Tag.api_update_galaxy_tag_enabled({'galaxy': galaxy, 'tags': tags})
    if res:
        return jsonify(res[0]), 1
    else:
        return redirect(url_for('tags_ui.tags_galaxy', galaxy=galaxy))


@tags_ui.route('/tag/enabled')
@login_required
@login_read_only
def get_all_tags_enabled():
    return jsonify(Tag.get_enabled_tags_with_synonyms_ui())

@tags_ui.route('/tag/confirm')
@login_required
@login_user_no_api
def tag_confirm():
    tag = request.args.get('tag')
    obj_type = request.args.get('type')
    subtype = request.args.get('subtype', '')
    obj_id = request.args.get('id', '')
    obj = ail_objects.get_object(obj_type, subtype, obj_id)
    if not obj.exists():
        abort(404)
    Tag.confirm_tag(tag, obj)

    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(obj.get_link(flask_context=True))

@tags_ui.route('/tag/add_tags')
@login_required
@login_user_no_api
def add_tags():

    tags = request.args.get('tags')
    tagsgalaxies = request.args.get('tagsgalaxies')
    object_type = request.args.get('type')
    object_subtype = request.args.get('subtype')
    object_id = request.args.get('id')

    list_tag = tags.split(',')
    list_tag_galaxies = tagsgalaxies.split(',')

    res = Tag.api_add_obj_tags(tags=list_tag, galaxy_tags=list_tag_galaxies,
                               object_id=object_id, object_type=object_type, object_subtype=object_subtype)
    # error
    if res[1] != 200:
        return str(res[0])

    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(ail_objects.get_object_link(object_type, object_subtype, object_id, flask_context=True))

@tags_ui.route('/tag/delete_tag') # TODO FIX REQUEST PARAMETER
@login_required
@login_user_no_api
def delete_tag():
    object_type = request.args.get('type')
    subtype = request.args.get('subtype', '')
    object_id = request.args.get('id')
    tag = request.args.get('tag')

    res = Tag.api_delete_obj_tags(tags=[tag], object_id=object_id, object_type=object_type, subtype=subtype)
    if res[1] != 200:
        return str(res[0])
    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(ail_objects.get_object_link(object_type, subtype, object_id, flask_context=True))


@tags_ui.route('/tag/get_all_tags')
@login_required
@login_read_only
def get_all_tags():
    return jsonify(Tag.get_all_tags())

@tags_ui.route('/tag/get_taxonomies_customs_tags')
@login_required
@login_read_only
def get_all_taxonomies_customs_tags():
    return jsonify(Tag.get_taxonomies_customs_tags(r_list=True))

@tags_ui.route('/tag/get_all_obj_tags')
@login_required
@login_read_only
def get_all_obj_tags():
    object_type = request.args.get('object_type')
    res = ail_objects.api_sanitize_object_type(object_type)
    if res:
        return jsonify(res[0]), res[1]
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

@tags_ui.route('/tag/custum/tags/enabled/json')
@login_required
@login_read_only
def tag_custum_tags_enabled_json():
    return jsonify(Tag.get_custom_enabled_tags(r_list=True))

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
    dict_tagged = {"object_type": object_type, "object_name": object_type.title() + "s"}
    dict_tagged['date'] = Date.sanitise_date_range('', '', separator='-')
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/message')
@login_required
@login_read_only
def tags_search_messages():
    object_type = 'message'
    dict_tagged = {"object_type": object_type, "object_name": object_type.title() + "s"}
    dict_tagged['date'] = Date.sanitise_date_range('', '', separator='-')
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/image')
@login_required
@login_read_only
def tags_search_images():
    object_type = 'image'
    dict_tagged = {"object_type": object_type, "object_name": object_type.title() + "s"}
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/ocr')
@login_required
@login_read_only
def tags_search_ocrs():
    object_type = 'ocr'
    dict_tagged = {"object_type": object_type, "object_name": object_type.title() + "s"}
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/qrcode')
@login_required
@login_read_only
def tags_search_qrcodes():
    object_type = 'qrcode'
    dict_tagged = {"object_type": object_type, "object_name": object_type.title() + "s"}
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/domain')
@login_required
@login_read_only
def tags_search_domains():
    object_type = 'domain'
    dict_tagged = {"object_type": object_type, "object_name": object_type.title() + "s"}
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/decoded')
@login_required
@login_read_only
def tags_search_decoded():
    object_type = 'decoded'
    dict_tagged = {"object_type": object_type, "object_name": object_type.title() + "s"}
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/screenshot')
@login_required
@login_read_only
def tags_search_screenshot():
    object_type = 'screenshot'
    dict_tagged = {"object_type": object_type, "object_name": object_type.title() + "s"}
    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)

@tags_ui.route('/tag/search/get_obj_by_tags')
@login_required
@login_read_only
def get_obj_by_tags():

    # # TODO: sanitize all
    object_type = request.args.get('object_type')
    subtype = ''  # TODO: handle subtype
    ltags = request.args.get('ltags')
    page = request.args.get('page')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # remove date separator
    if date_from:
        date_from = date_from.replace('-', '')
    if date_to:
        date_to = date_to.replace('-', '')
    date_today = Date.get_today_date_str()
    if date_today == date_from == date_to:
        date_from = None
        date_to = None

    # TODO REFACTOR ME
    # unpack tags
    list_tags = ltags.split(',')
    list_tag = []
    for tag in list_tags:
        list_tag.append(tag.replace('"', '\"'))

    # object_type
    res = ail_objects.api_sanitize_object_type(object_type)
    if res:
        return jsonify(res)

    # page
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    # TODO REPLACE ME
    dict_obj = Tag.get_obj_by_tags(object_type, list_tag, date_from=date_from, date_to=date_to, page=page)
    # print(dict_obj)

    if dict_obj['tagged_obj']:
        dict_tagged = {
                       "tagged_obj": [], "page": dict_obj['page'], "nb_pages": dict_obj['nb_pages'],
                       "nb_first_elem": dict_obj['nb_first_elem'], "nb_last_elem": dict_obj['nb_last_elem'],
                       "nb_all_elem": dict_obj['nb_all_elem']}

        for obj_id in dict_obj['tagged_obj']:
            obj_metadata = ail_objects.get_object_meta(object_type, subtype, obj_id, flask_context=True)
            obj_metadata['id'] = obj_id
            dict_tagged["tagged_obj"].append(obj_metadata)

        dict_tagged['tab_keys'] = ail_objects.get_ui_obj_tag_table_keys(object_type)

        # return jsonify(dict_tagged)
    else:
        dict_tagged = {}
        dict_tagged['tag_last_seen'] = Tag.get_tags_min_last_seen(list_tag, r_int=False)

    dict_tagged['object_type'] = object_type
    dict_tagged['object_name'] = f'{object_type.title()}s'

    if len(list_tag) == 1:
        dict_tagged['current_tags'] = [ltags.replace('"', '\"')]
    else:
        dict_tagged['current_tags'] = list_tag
    dict_tagged['current_tags_str'] = ltags

    if 'date' in dict_obj:
        dict_tagged['date'] = dict_obj['date']

    return render_template("tags/search_obj_by_tags.html", bootstrap_label=bootstrap_label, dict_tagged=dict_tagged)


@tags_ui.route("/tags/auto_push")
@login_required
@login_admin
def auto_push():

    # TODO CHECK if misp or the hive connected

    meta = Tag.get_auto_push_enabled_meta()
    auto_push_tags = Tag.get_auto_push_tags()
    return render_template("tags_auto_push.html",
                           auto_push_tags=auto_push_tags,
                           meta=meta,
                           auto_push_status=Tag.get_auto_push_status())

@tags_ui.route("/tags/auto_push_post", methods=['POST'])
@login_required
@login_admin
def auto_push_post():
    tag_enabled_misp = request.form.getlist('tag_enabled_misp')
    tag_enabled_hive = request.form.getlist('tag_enabled_hive')

    Tag.api_add_auto_push_enabled_tags({'misp_tags': tag_enabled_misp, 'thehive_tags': tag_enabled_hive})
    return redirect(url_for('tags_ui.auto_push'))

@tags_ui.route("/tags/auto_push/misp/enable")
@login_required
@login_admin
def enable_misp_auto_push():
    Tag.enable_auto_push('misp')
    return redirect(url_for('tags_ui.auto_push'))

@tags_ui.route("/tags/auto_push/misp/disable")
@login_required
@login_admin
def disable_misp_auto_push():
    Tag.disable_auto_push('misp')
    return redirect(url_for('tags_ui.auto_push'))

@tags_ui.route("/tags/auto_push/thehive/enable")
@login_required
@login_admin
def enable_hive_auto_push():
    Tag.enable_auto_push('thehive')
    return redirect(url_for('tags_ui.auto_push'))

@tags_ui.route("/tags/auto_push/thehive/disable")
@login_required
@login_admin
def disable_hive_auto_push():
    Tag.disable_auto_push('thehive')
    return redirect(url_for('tags_ui.auto_push'))
