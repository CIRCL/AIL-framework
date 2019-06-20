#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the rest api
'''

import os
import re
import sys
import json
import redis
import datetime

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response
from flask_login import login_required

from functools import wraps

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_cache = Flask_config.r_cache
r_serv_db = Flask_config.r_serv_db
r_serv_onion = Flask_config.r_serv_onion
r_serv_metadata = Flask_config.r_serv_metadata

restApi = Blueprint('restApi', __name__, template_folder='templates')

# ============ AUTH FUNCTIONS ============

def check_token_format(strg, search=re.compile(r'[^a-zA-Z0-9_-]').search):
    return not bool(search(strg))

def verify_token(token):
    if len(token) != 55:
        return False

    if not check_token_format(token):
        return False

    if r_serv_db.hexists('user:tokens', token):
        return True
    else:
        return False

# ============ DECORATOR ============

def token_required(funct):
    @wraps(funct)
    def api_token(*args, **kwargs):
        data = authErrors()
        if data:
            return Response(json.dumps(data[0], indent=2, sort_keys=True), mimetype='application/json'), data[1]
        else:
            return funct(*args, **kwargs)
    return api_token

def get_auth_from_header():
    token = request.headers.get('Authorization').replace(' ', '') # remove space
    return token

def authErrors():
    # Check auth
    if not request.headers.get('Authorization'):
        return ({'status': 'error', 'reason': 'Authentication needed'}, 401)
    token = get_auth_from_header()
    data = None
    # verify token format

    try:
        authenticated = False
        if verify_token(token):
            authenticated = True

        if not authenticated:
            data = ({'status': 'error', 'reason': 'Authentication failed'}, 401)
    except Exception as e:
        print(e)
        data = ({'status': 'error', 'reason': 'Malformed Authentication String'}, 400)
    if data:
        return data
    else:
        return None

# ============ FUNCTIONS ============

def one():
    return 1

# ============= ROUTES ==============

# @restApi.route("/api", methods=['GET'])
# @login_required
# def api():
#     return 'api doc'

@restApi.route("api/items", methods=['POST'])
@token_required
def items():
    item = request.args.get('id')

    return Response(json.dumps({'test': 2}), mimetype='application/json')

# ========= REGISTRATION =========
app.register_blueprint(restApi, url_prefix=baseUrl)
