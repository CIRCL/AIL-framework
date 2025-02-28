#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
"""

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_read_only, login_user_no_api

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib import chats_viewer
from lib import Language
from lib import Tag
from lib import module_extractor
from lib.objects import ail_objects

# ============ BLUEPRINT ============
chats_explorer = Blueprint('chats_explorer', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/chats_explorer'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ FUNCTIONS ============

# ============= ROUTES ==============

# @chats_explorer.route("/chats/explorer", methods=['GET'])
# @login_required
# @login_read_only
# def chats_explorer_dashboard():
#     return

@chats_explorer.route("chats/explorer/protocols", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_protocols():
    protocols = chats_viewer.get_chat_protocols_meta()
    return render_template('chats_protocols.html', protocols=protocols, username_subtypes=ail_core.get_object_all_subtypes('username'))

@chats_explorer.route("chats/explorer/networks", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_networks():
    protocol = request.args.get('protocol')
    networks = chats_viewer.get_chat_service_instances_by_protocol(protocol)
    if len(networks) == 1:
        instance_uuid = list(networks.values())[0]
        return redirect(url_for('chats_explorer.chats_explorer_instance', subtype=instance_uuid))
    else:
        return render_template('chats_networks.html', protocol=protocol, networks=networks)


@chats_explorer.route("chats/explorer/instances", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_instance():
    intance_uuid = request.args.get('subtype')
    chat_instance = chats_viewer.api_get_chat_service_instance(intance_uuid)
    if chat_instance[1] != 200:
        return create_json_response(chat_instance[0], chat_instance[1])
    else:
        chat_instance = chat_instance[0]
        return render_template('chat_instance.html', chat_instance=chat_instance,
                               bootstrap_label=bootstrap_label)

@chats_explorer.route("chats/explorer/chats/selector", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_chats_selector():
    return jsonify(chats_viewer.api_get_chats_selector())

@chats_explorer.route("chats/explorer/chat", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_chat():
    chat_id = request.args.get('id')
    instance_uuid = request.args.get('subtype')
    target = request.args.get('target')
    if target == "Don't Translate":
        target = None
    nb_messages = request.args.get('nb')
    mess = request.args.get('message')
    if mess:
        message = mess
        page = -1
        message_id = message.rsplit('/', 1)[-1]
    else:
        message = None
        message_id = None
        page = request.args.get('page')
    chat = chats_viewer.api_get_chat(chat_id, instance_uuid, translation_target=target, message=message, nb=nb_messages, page=page, heatmap=True)
    if chat[1] != 200:
        return create_json_response(chat[0], chat[1])
    else:
        chat = chat[0]
        languages = Language.get_translation_languages()
        languages_stats = chats_viewer.api_get_languages_stats('chat', instance_uuid, chat_id)
        return render_template('chat_viewer.html', chat=chat, bootstrap_label=bootstrap_label,
                               ail_tags=Tag.get_modal_add_tags(chat['id'], chat['type'], chat['subtype']),
                               message_id=message_id, languages_stats=languages_stats,
                               translation_languages=languages, translation_target=target)

@chats_explorer.route("chats/explorer/messages/stats/week", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_messages_stats_week():
    chat_type = request.args.get('type')
    instance_uuid = request.args.get('subtype')
    chat_id = request.args.get('id')
    week = chats_viewer.api_get_nb_message_by_week(chat_type, instance_uuid, chat_id)
    if week[1] != 200:
        return create_json_response(week[0], week[1])
    else:
        return jsonify(week[0])

@chats_explorer.route("chats/explorer/messages/stats/week/all", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_messages_stats_week_all():
    chat_type = request.args.get('type')
    instance_uuid = request.args.get('subtype')
    chat_id = request.args.get('id')
    week = chats_viewer.api_get_nb_week_messages(chat_type, instance_uuid, chat_id)  # TODO SELECT DATE
    if week[1] != 200:
        return create_json_response(week[0], week[1])
    else:
        return jsonify(week[0])

@chats_explorer.route("chats/explorer/messages/stats/year", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_messages_stats_year():
    chat_type = request.args.get('type')
    instance_uuid = request.args.get('subtype')
    chat_id = request.args.get('id')
    year = request.args.get('year')
    stats = chats_viewer.api_get_nb_year_messages(chat_type, instance_uuid, chat_id, year)
    if stats[1] != 200:
        return create_json_response(stats[0], stats[1])
    else:
        return jsonify(stats[0])

@chats_explorer.route("/chats/explorer/subchannel", methods=['GET'])
@login_required
@login_read_only
def objects_subchannel_messages():
    subchannel_id = request.args.get('id')
    instance_uuid = request.args.get('subtype')
    target = request.args.get('target')
    if target == "Don't Translate":
        target = None
    nb_messages = request.args.get('nb')
    mess = request.args.get('message')
    if mess:
        message = mess
        page = -1
        message_id = message.rsplit('/', 1)[-1]
    else:
        message = None
        message_id = None
        page = request.args.get('page')
    subchannel = chats_viewer.api_get_subchannel(subchannel_id, instance_uuid, translation_target=target, message=message, nb=nb_messages, page=page)
    if subchannel[1] != 200:
        return create_json_response(subchannel[0], subchannel[1])
    else:
        subchannel = subchannel[0]
        languages = Language.get_translation_languages()
        languages_stats = chats_viewer.api_get_languages_stats('chat-subchannel', instance_uuid, subchannel_id)
        return render_template('SubChannelMessages.html', subchannel=subchannel,
                               ail_tags=Tag.get_modal_add_tags(subchannel['id'], subchannel['type'], subchannel['subtype']),
                               message_id=message_id, languages_stats=languages_stats,
                               bootstrap_label=bootstrap_label, translation_languages=languages, translation_target=target)

@chats_explorer.route("/chats/explorer/thread", methods=['GET'])
@login_required
@login_read_only
def objects_thread_messages():
    thread_id = request.args.get('id')
    instance_uuid = request.args.get('subtype')
    target = request.args.get('target')
    if target == "Don't Translate":
        target = None
    nb_messages = request.args.get('nb')
    mess = request.args.get('message')
    if mess:
        message = mess
        page = -1
        message_id = message.rsplit('/', 1)[-1]
    else:
        message = None
        message_id = None
        page = request.args.get('page')
    thread = chats_viewer.api_get_thread(thread_id, instance_uuid, translation_target=target, message=message, nb=nb_messages, page=page)
    if thread[1] != 200:
        return create_json_response(thread[0], thread[1])
    else:
        meta = thread[0]
        languages = Language.get_translation_languages()
        return render_template('ThreadMessages.html', meta=meta, bootstrap_label=bootstrap_label,
                               message_id=message_id,
                               translation_languages=languages, translation_target=target)

@chats_explorer.route("/chats/explorer/participants", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_chat_participants():
    chat_type = request.args.get('type')
    chat_id = request.args.get('id')
    chat_subtype = request.args.get('subtype')
    meta = chats_viewer.api_get_chat_participants(chat_type, chat_subtype,chat_id)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    else:
        meta = meta[0]
        return render_template('chat_participants.html', meta=meta, bootstrap_label=bootstrap_label)


@chats_explorer.route("/chats/explorer/chat/download", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_chat_download():
    chat_id = request.args.get('id')
    chat_subtype = request.args.get('subtype')
    chat = chats_viewer.api_chat_messages(chat_subtype, chat_id)
    if chat[1] != 200:
        if chat[1] == 404:
            abort(404)
        else:
            return create_json_response(chat[0], chat[1])
    else:
        return jsonify(chat[0])

@chats_explorer.route("/chats/explorer/subchannel/download", methods=['GET'])
@login_required
@login_read_only
def objects_subchannel_messages_download():
    subchannel_id = request.args.get('id')
    instance_uuid = request.args.get('subtype')
    subchannel = chats_viewer.api_subchannel_messages(instance_uuid, subchannel_id)
    if subchannel[1] != 200:
        return create_json_response(subchannel[0], subchannel[1])
    else:
        return jsonify(subchannel[0])


@chats_explorer.route("/chats/explorer/thread/download", methods=['GET'])
@login_required
@login_read_only
def objects_thread_messages_download():
    thread_id = request.args.get('id')
    instance_uuid = request.args.get('subtype')
    thread = chats_viewer.api_thread_messages(instance_uuid, thread_id)
    if thread[1] != 200:
        return create_json_response(thread[0], thread[1])
    else:
        return jsonify(thread[0])


#### ####

@chats_explorer.route("/chats/explorer/chat/monitoring/request", methods=['GET', 'POST'])
@login_required
@login_user_no_api
def chat_monitoring_request():
    if request.method == 'POST':
        user_id = current_user.get_user_id()
        chat_type = request.form.get('type')
        username = request.form.get('username')
        invite = request.form.get('invite')
        description = request.form.get('description')
        if chat_type not in ['discord', 'telegram', 'other']:
            return create_json_response({"status": "error", "reason": "Invalid Chat Type"}, 400)
        if not username and not invite and not description:
            return create_json_response({"status": "error", "reason": "Please provide a username/username/invite/comment"}, 400)
        cm_uuid = chats_viewer.create_chat_monitoring_requests(user_id, chat_type, invite, username, description)
        return render_template('request_chat_monitoring.html', uuid=cm_uuid)
    else:
        return render_template('request_chat_monitoring.html')


@chats_explorer.route("/chats/explorer/chat/monitoring/request/admin", methods=['GET'])
@login_required
@login_admin
def chat_monitoring_requests():
    metas = chats_viewer.get_chats_monitoring_requests_metas()
    return render_template('chat_monitoring_requests.html', metas=metas)

#### ####


@chats_explorer.route("/objects/message", methods=['GET'])
@login_required
@login_read_only
def objects_message():
    message_id = request.args.get('id')
    target = request.args.get('target')
    if target == "Don't Translate":
        target = None
    message = chats_viewer.api_get_message(message_id, translation_target=target)
    if message[1] != 200:
        return create_json_response(message[0], message[1])
    else:
        message = message[0]
        languages = Language.get_translation_languages()
        container_url = ail_objects.get_obj_from_global_id(message['container']).get_link(flask_context=True)
        extracted = module_extractor.extract(current_user.get_user_id(), 'message', '', message['id'], content=message['content'])
        extracted_matches = module_extractor.get_extracted_by_match(extracted)
        message['extracted'] = extracted
        message['extracted_matches'] = extracted_matches
        return render_template('ChatMessage.html', meta=message, bootstrap_label=bootstrap_label,
                               translation_languages=languages, translation_target=target, container_url=container_url,
                               modal_add_tags=Tag.get_modal_add_tags(message['id'], object_type='message'))

@chats_explorer.route("/objects/message/translate", methods=['POST'])
@login_required
@login_user_no_api
def objects_message_translate():
    message_id = request.form.get('id')
    source = request.form.get('language_target')
    target = request.form.get('target')
    translation = request.form.get('translation')
    if target == "Don't Translate":
        target = None
    resp = chats_viewer.api_manually_translate_message(message_id, source, target, translation)
    if resp[1] != 200:
        return create_json_response(resp[0], resp[1])
    else:
        if request.referrer:
            return redirect(request.referrer)
        else:
            return redirect(url_for('chats_explorer.objects_message', id=message_id, target=target))

@chats_explorer.route("/objects/message/detect/language", methods=['GET'])
@login_required
@login_user_no_api
def objects_message_detect_language():
    message_id = request.args.get('id')
    target = request.args.get('target')
    resp = chats_viewer.api_message_detect_language(message_id)
    if resp[1] != 200:
        return create_json_response(resp[0], resp[1])
    else:
        if request.referrer:
            return redirect(request.referrer)
        else:
            return redirect(url_for('chats_explorer.objects_message', id=message_id, target=target))

@chats_explorer.route("/objects/user-account", methods=['GET'])
@login_required
@login_read_only
def objects_user_account():
    instance_uuid = request.args.get('subtype')
    user_id = request.args.get('id')
    target = request.args.get('target')
    if target == "Don't Translate":
        target = None
    user_account = chats_viewer.api_get_user_account(user_id, instance_uuid, translation_target=target)
    # print()
    # print(user_account[0]['usernames'])
    # print()
    if user_account[1] != 200:
        return create_json_response(user_account[0], user_account[1])
    else:
        user_account = user_account[0]
        languages = Language.get_translation_languages()
        return render_template('user_account.html', meta=user_account, bootstrap_label=bootstrap_label,
                               ail_tags=Tag.get_modal_add_tags(user_account['id'], user_account['type'], user_account['subtype']),
                               translation_languages=languages, translation_target=target)

@chats_explorer.route("/objects/user-account_usernames_timeline_json", methods=['GET']) # TODO API
@login_required
@login_read_only
def objects_user_account_usernames_timeline_json():
    subtype = request.args.get('subtype')
    user_id = request.args.get('id')
    json_graph = chats_viewer.get_user_account_usernames_timeline(subtype, user_id)
    return jsonify(json_graph)

@chats_explorer.route("/objects/user-account_chats_chord_json", methods=['GET']) # TODO API
@login_required
@login_read_only
def objects_user_account_chats_chord_json():
    subtype = request.args.get('subtype')
    user_id = request.args.get('id')
    json_graph = chats_viewer.get_user_account_chats_chord(subtype, user_id)
    return jsonify(json_graph)

@chats_explorer.route("/objects/user-account_mentions_chord_json", methods=['GET']) # TODO API
@login_required
@login_read_only
def objects_user_account_mentions_chord_json():
    subtype = request.args.get('subtype')
    user_id = request.args.get('id')
    json_graph = chats_viewer.get_user_account_mentions_chord(subtype, user_id)
    return jsonify(json_graph)

@chats_explorer.route("/objects/user-account/chat", methods=['GET'])
@login_required
@login_read_only
def objects_user_account_chat():
    instance_uuid = request.args.get('subtype')
    user_id = request.args.get('id')
    chat_id = request.args.get('chat_id')
    target = request.args.get('target')
    if target == "Don't Translate":
        target = None
    meta = chats_viewer.api_get_user_account_chat_messages(user_id, instance_uuid, chat_id, translation_target=target)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    else:
        meta = meta[0]
        languages = Language.get_translation_languages()
        return render_template('chats_explorer/user_chat_messages.html', meta=meta, bootstrap_label=bootstrap_label,
                               ail_tags=Tag.get_modal_add_tags(meta['user-account']['id'], meta['user-account']['type'], meta['user-account']['subtype']),
                               translation_languages=languages, translation_target=target)

@chats_explorer.route("objects/user-account/messages/stats/week/all", methods=['GET'])
@login_required
@login_read_only
def user_account_messages_stats_week_all():
    instance_uuid = request.args.get('subtype')
    user_id = request.args.get('id')
    week = chats_viewer.api_get_user_account_nb_all_week_messages(user_id, instance_uuid)
    if week[1] != 200:
        return create_json_response(week[0], week[1])
    else:
        return jsonify(week[0])

@chats_explorer.route("objects/user-account/messages/stats/year", methods=['GET'])
@login_required
@login_read_only
def user_account_messages_stats_year():
    instance_uuid = request.args.get('subtype')
    user_id = request.args.get('id')
    year = request.args.get('year')
    stats = chats_viewer.api_get_user_account_nb_year_messages(user_id, instance_uuid, year)
    if stats[1] != 200:
        return create_json_response(stats[0], stats[1])
    else:
        return jsonify(stats[0])
