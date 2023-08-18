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
from lib import ail_core
from lib.objects import abstract_subtype_object
from lib.objects import ail_objects
from lib.objects import Chats
from packages import Date

# ============ BLUEPRINT ============
objects_chat = Blueprint('objects_chat', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/chat'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============ FUNCTIONS ============

# ============= ROUTES ==============


@objects_chat.route("/objects/chat/messages", methods=['GET'])
@login_required
@login_read_only
def objects_dashboard_chat():
    chat = request.args.get('id')
    subtype = request.args.get('subtype')
    chat = Chats.Chat(chat, subtype)
    if chat.exists():
        messages = chat.get_messages()
        meta = chat.get_meta({'icon'})
        print(meta)
        return render_template('ChatMessages.html', meta=meta, messages=messages, bootstrap_label=bootstrap_label)
    else:
        return abort(404)



