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
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib import chats_viewer
from lib import Language
from lib import Tag

# ============ BLUEPRINT ============
chats_explorer = Blueprint('chats_explorer', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/chats_explorer'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ FUNCTIONS ============

# ============= ROUTES ==============

@chats_explorer.route("/chats/explorer", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_dashboard():
    return

@chats_explorer.route("chats/explorer/protocols", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_protocols():
    protocols = chats_viewer.get_chat_protocols_meta()
    return render_template('chats_protocols.html', protocols=protocols)

@chats_explorer.route("chats/explorer/networks", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_networks():
    protocol = request.args.get('protocol')
    networks = chats_viewer.get_chat_service_instances_by_protocol(protocol)
    if len(networks) == 1:
        instance_uuid = list(networks.values())[0]
        return redirect(url_for('chats_explorer.chats_explorer_instance', uuid=instance_uuid))
    else:
        return render_template('chats_networks.html', protocol=protocol, networks=networks)


@chats_explorer.route("chats/explorer/instance", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_instance():
    intance_uuid = request.args.get('uuid')
    chat_instance = chats_viewer.api_get_chat_service_instance(intance_uuid)
    if chat_instance[1] != 200:
        return create_json_response(chat_instance[0], chat_instance[1])
    else:
        chat_instance = chat_instance[0]
        return render_template('chat_instance.html', chat_instance=chat_instance)

@chats_explorer.route("chats/explorer/chat", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_chat():
    chat_id = request.args.get('id')
    instance_uuid = request.args.get('uuid')
    target = request.args.get('target')
    chat = chats_viewer.api_get_chat(chat_id, instance_uuid, translation_target=target)
    if chat[1] != 200:
        return create_json_response(chat[0], chat[1])
    else:
        chat = chat[0]
        languages = Language.get_translation_languages()
        return render_template('chat_viewer.html', chat=chat, bootstrap_label=bootstrap_label, translation_languages=languages, translation_target=target)

@chats_explorer.route("chats/explorer/messages/stats/week", methods=['GET'])
@login_required
@login_read_only
def chats_explorer_messages_stats_week():
    chat_id = request.args.get('id')
    instance_uuid = request.args.get('uuid')
    week = chats_viewer.api_get_nb_message_by_week(chat_id, instance_uuid)
    if week[1] != 200:
        return create_json_response(week[0], week[1])
    else:
        return jsonify(week[0])

@chats_explorer.route("/chats/explorer/subchannel", methods=['GET'])
@login_required
@login_read_only
def objects_subchannel_messages():
    subchannel_id = request.args.get('id')
    instance_uuid = request.args.get('uuid')
    target = request.args.get('target')
    subchannel = chats_viewer.api_get_subchannel(subchannel_id, instance_uuid, translation_target=target)
    if subchannel[1] != 200:
        return create_json_response(subchannel[0], subchannel[1])
    else:
        subchannel = subchannel[0]
        languages = Language.get_translation_languages()
        return render_template('SubChannelMessages.html', subchannel=subchannel, bootstrap_label=bootstrap_label, translation_languages=languages, translation_target=target)

@chats_explorer.route("/chats/explorer/thread", methods=['GET'])
@login_required
@login_read_only
def objects_thread_messages():
    thread_id = request.args.get('id')
    instance_uuid = request.args.get('uuid')
    target = request.args.get('target')
    thread = chats_viewer.api_get_thread(thread_id, instance_uuid, translation_target=target)
    if thread[1] != 200:
        return create_json_response(thread[0], thread[1])
    else:
        meta = thread[0]
        languages = Language.get_translation_languages()
        return render_template('ThreadMessages.html', meta=meta, bootstrap_label=bootstrap_label, translation_languages=languages, translation_target=target)

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

@chats_explorer.route("/objects/message", methods=['GET'])
@login_required
@login_read_only
def objects_message():
    message_id = request.args.get('id')
    message = chats_viewer.api_get_message(message_id)
    if message[1] != 200:
        return create_json_response(message[0], message[1])
    else:
        message = message[0]
        languages = Language.get_translation_languages()
        return render_template('ChatMessage.html', meta=message, bootstrap_label=bootstrap_label,
                               modal_add_tags=Tag.get_modal_add_tags(message['id'], object_type='message'))

@chats_explorer.route("/objects/user-account", methods=['GET'])
@login_required
@login_read_only
def objects_user_account():
    instance_uuid = request.args.get('subtype')
    user_id = request.args.get('id')
    user_account = chats_viewer.api_get_user_account(user_id, instance_uuid)
    if user_account[1] != 200:
        return create_json_response(user_account[0], user_account[1])
    else:
        user_account = user_account[0]
        return render_template('user_account.html', meta=user_account, bootstrap_label=bootstrap_label)