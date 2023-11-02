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

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import chats_viewer



############################################

from lib import ail_core
from lib.objects import ail_objects
from lib import chats_viewer
from lib.objects import Chats
from lib.objects import ChatSubChannels

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
    chat = chats_viewer.api_get_chat(chat_id, instance_uuid)
    if chat[1] != 200:
        return create_json_response(chat[0], chat[1])
    else:
        chat = chat[0]
        return render_template('chat_viewer.html', chat=chat)

@chats_explorer.route("/chats/explorer/subchannel", methods=['GET'])
@login_required
@login_read_only
def objects_subchannel_messages():
    subchannel_id = request.args.get('id')
    instance_uuid = request.args.get('uuid')
    subchannel = chats_viewer.api_get_subchannel(subchannel_id, instance_uuid)
    if subchannel[1] != 200:
        return create_json_response(subchannel[0], subchannel[1])
    else:
        subchannel = subchannel[0]
        return render_template('SubChannelMessages.html', subchannel=subchannel)

@chats_explorer.route("/chats/explorer/subchannel", methods=['GET'])
@login_required
@login_read_only
def objects_message():
    message_id = request.args.get('id')
    message = chats_viewer.api_get_message(message_id)
    if message[1] != 200:
        return create_json_response(message[0], message[1])
    else:
        message = message[0]
        return render_template('ChatMessage.html', message=message)

#############################################################################################
#############################################################################################
#############################################################################################


@chats_explorer.route("/objects/chat/messages", methods=['GET'])
@login_required
@login_read_only
def objects_dashboard_chat():
    chat = request.args.get('id')
    subtype = request.args.get('subtype')
    chat = Chats.Chat(chat, subtype)
    if chat.exists():
        messages, mess_tags = chat.get_messages()
        print(messages)
        print(chat.get_subchannels())
        meta = chat.get_meta({'icon', 'username'})
        if meta.get('username'):
            meta['username'] = ail_objects.get_obj_from_global_id(meta['username']).get_meta()
        print(meta)
        return render_template('ChatMessages.html', meta=meta, messages=messages, mess_tags=mess_tags, bootstrap_label=bootstrap_label)
    else:
        return abort(404)
