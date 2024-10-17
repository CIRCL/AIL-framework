#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import ssl
import json
import time
import uuid
import random
import logging
import logging.config

from flask import Flask, render_template, jsonify, request, Request, Response, session, redirect, url_for
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

import importlib
from os.path import join

sys.path.append('./modules/')

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.ail_users import AILUser, get_session_user
from lib import Tag
from lib import ail_core
from lib import ail_logger

from packages.git_status import clear_git_meta_cache

# Import config
import Flask_config

# Import Blueprint
from blueprints.root import root
from blueprints.crawler_splash import crawler_splash
from blueprints.correlation import correlation
from blueprints.languages_ui import languages_ui
from blueprints.tags_ui import tags_ui
from blueprints.import_export import import_export
from blueprints.investigations_b import investigations_b
from blueprints.objects_item import objects_item
from blueprints.hunters import hunters
from blueprints.old_endpoints import old_endpoints
from blueprints.ail_2_ail_sync import ail_2_ail_sync
from blueprints.settings_b import settings_b
from blueprints.objects_cve import objects_cve
from blueprints.objects_decoded import objects_decoded
from blueprints.objects_subtypes import objects_subtypes
from blueprints.objects_title import objects_title
from blueprints.objects_cookie_name import objects_cookie_name
from blueprints.objects_etag import objects_etag
from blueprints.objects_hhhash import objects_hhhash
from blueprints.objects_dom_hash import objects_dom_hash
from blueprints.chats_explorer import chats_explorer
from blueprints.objects_image import objects_image
from blueprints.objects_ocr import objects_ocr
from blueprints.objects_qrcode import objects_qrcode
from blueprints.objects_favicon import objects_favicon
from blueprints.api_rest import api_rest


Flask_dir = os.environ['AIL_FLASK']

# CONFIG #
config_loader = ConfigLoader()
baseUrl = config_loader.get_config_str("Flask", "baseurl")
host = config_loader.get_config_str("Flask", "host")
baseUrl = baseUrl.replace('/', '')
if baseUrl != '':
    baseUrl = '/'+baseUrl

try:
    FLASK_PORT = config_loader.get_config_int("Flask", "port")
except Exception:
    FLASK_PORT = 7000

# ========= REDIS =========#
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")

# logs
log_dir = os.path.join(os.environ['AIL_HOME'], 'logs')
if not os.path.isdir(log_dir):
    os.makedirs(log_dir)

# ========= LOGS =========#

access_logger = ail_logger.get_access_config(create=True)

class FilterLogErrors(logging.Filter):
    def filter(self, record):
        # print(dict(record.__dict__))
        if record.levelname == 'ERROR':
            if record.msg.startswith('Error on request:'):
                if 'ssl.SSLEOFError: EOF occurred in violation of protocol' in record.msg:
                    return False
        return True


logging.config.dictConfig(ail_logger.get_config(name='flask'))
flask_logger = logging.getLogger()
ignore_filter = FilterLogErrors()
for handler in flask_logger.handlers:
    handler.addFilter(ignore_filter)


# =========  TLS  =========#

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile=os.path.join(Flask_dir, 'server.crt'), keyfile=os.path.join(Flask_dir, 'server.key'))
ssl_context.suppress_ragged_eofs = True
# print(ssl_context.get_ciphers())
# =========       =========#

Flask_config.app = Flask(__name__, static_url_path=baseUrl+'/static/')
app = Flask_config.app
app.config['MAX_CONTENT_LENGTH'] = 900 * 1024 * 1024

# =========  BLUEPRINT  =========#
app.register_blueprint(root, url_prefix=baseUrl)
app.register_blueprint(crawler_splash, url_prefix=baseUrl)
app.register_blueprint(correlation, url_prefix=baseUrl)
app.register_blueprint(languages_ui, url_prefix=baseUrl)
app.register_blueprint(tags_ui, url_prefix=baseUrl)
app.register_blueprint(import_export, url_prefix=baseUrl)
app.register_blueprint(investigations_b, url_prefix=baseUrl)
app.register_blueprint(objects_item, url_prefix=baseUrl)
app.register_blueprint(hunters, url_prefix=baseUrl)
app.register_blueprint(old_endpoints, url_prefix=baseUrl)
app.register_blueprint(ail_2_ail_sync, url_prefix=baseUrl)
app.register_blueprint(settings_b, url_prefix=baseUrl)
app.register_blueprint(objects_cve, url_prefix=baseUrl)
app.register_blueprint(objects_decoded, url_prefix=baseUrl)
app.register_blueprint(objects_subtypes, url_prefix=baseUrl)
app.register_blueprint(objects_title, url_prefix=baseUrl)
app.register_blueprint(objects_cookie_name, url_prefix=baseUrl)
app.register_blueprint(objects_etag, url_prefix=baseUrl)
app.register_blueprint(objects_hhhash, url_prefix=baseUrl)
app.register_blueprint(objects_dom_hash, url_prefix=baseUrl)
app.register_blueprint(chats_explorer, url_prefix=baseUrl)
app.register_blueprint(objects_image, url_prefix=baseUrl)
app.register_blueprint(objects_ocr, url_prefix=baseUrl)
app.register_blueprint(objects_qrcode, url_prefix=baseUrl)
app.register_blueprint(objects_favicon, url_prefix=baseUrl)
app.register_blueprint(api_rest, url_prefix=baseUrl)

# =========       =========#

# ========= Cookie name ========
app.config.update(SESSION_COOKIE_NAME='ail_framework_{}'.format(ail_core.get_ail_uuid_int()))

# ========= session ========
app.secret_key = str(random.getrandbits(256))
login_manager = LoginManager()
login_manager.login_view = 'root.login'
login_manager.init_app(app)

# ========= LOGIN MANAGER ========

@login_manager.user_loader
def load_user(session_id):  # TODO USE Alternative ID
    # print(session)
    user_id = get_session_user(session_id)
    if user_id:
        user = AILUser.get(user_id)
        # print(user)
        return user
    return None

# ========= HEADER GENERATION ======== DEPRECATED


# Get headers items that should be ignored (not displayed)
toIgnoreModule = set()
try:
    with open('templates/ignored_modules.txt', 'r') as f:
        lines = f.read().splitlines()
        for line in lines:
            toIgnoreModule.add(line)

except IOError:
    pass

# Dynamically import routes and functions from modules
# Also, prepare header.html
to_add_to_header_dico = {}
for root, dirs, files in os.walk(os.path.join(Flask_dir, 'modules')):
    sys.path.append(join(root))

    # Ignore the module
    curr_dir = root.split('/')[1]
    if curr_dir in toIgnoreModule:
        continue

    for name in files:
        module_name = root.split('/')[-2]
        if name.startswith('Flask_') and name.endswith('.py'):
            if name == 'Flask_config.py':
                continue
            name = name.strip('.py')
            importlib.import_module(name)
        elif name == 'header_{}.html'.format(module_name):
            with open(join(root, name), 'r') as f:
                to_add_to_header_dico[module_name] = f.read()

# create header.html
with open(os.path.join(Flask_dir, 'templates', 'header_base.html'), 'r') as f:
    complete_header = f.read()
modified_header = complete_header

# Add the header in the supplied order
for module_name, txt in list(to_add_to_header_dico.items()):
    to_replace = '<!--{}-->'.format(module_name)
    if to_replace in complete_header:
        modified_header = modified_header.replace(to_replace, txt)
        del to_add_to_header_dico[module_name]

# Add the header for no-supplied order
to_add_to_header = []
for module_name, txt in to_add_to_header_dico.items():
    to_add_to_header.append(txt)

modified_header = modified_header.replace('<!--insert here-->', '\n'.join(to_add_to_header))

# Write the header.html file
with open(os.path.join(Flask_dir, 'templates', 'header.html'), 'w') as f:
    f.write(modified_header)

# ========= JINJA2 FUNCTIONS ========
def list_len(s):
    return len(s)
app.jinja_env.filters['list_len'] = list_len


# ========= CACHE CONTROL ========
@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'private, max-age=0'
    return response

# ========== USERS ============
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.update_last_seen()


# ========== ROUTES ============

#@app.route('/endpoints')
#def endpoints():
#    for rule in app.url_map.iter_rules():
#        str_endpoint = str(rule)
#        if len(str_endpoint)>5:
#            if str_endpoint[0:5]=='/api/': ## add baseUrl ???
#                print(str_endpoint)
#                #print(rule.endpoint) #internal endpoint name
#                #print(rule.methods)
#    return 'ok'

# ========== ERROR HANDLER ============

@app.errorhandler(405)
def _handle_client_error(e):
    if request.path.startswith('/api/'): ## # TODO: add baseUrl
        res_dict = {"status": "error", "reason": "Method Not Allowed: The method is not allowed for the requested URL"}
        anchor_id = request.path[8:]
        anchor_id = anchor_id.replace('/', '_')
        api_doc_url = 'https://github.com/ail-project/ail-framework/tree/master/doc#{}'.format(anchor_id)
        res_dict['documentation'] = api_doc_url
        return Response(json.dumps(res_dict) + '\n', mimetype='application/json'), 405
    else:
        return e

@app.errorhandler(403)
def error_page_not_found(e):
    if request.path.startswith('/api/'): ## # TODO: add baseUrl
        return Response(json.dumps({"status": "error", "reason": "403 Access Denied"}) + '\n', mimetype='application/json'), 403
    else:
        # avoid endpoint enumeration
        return page_forbidden(e)

@app.errorhandler(404)
def error_page_not_found(e):
    if request.path.startswith('/api/'): ## # TODO: add baseUrl
        return Response(json.dumps({"status": "error", "reason": "404 Not Found"}) + '\n', mimetype='application/json'), 404
    else:
        # avoid endpoint enumeration
        return page_not_found(e)

@app.errorhandler(500)
def _handle_client_error(e):
    if request.path.startswith('/api/'):
        return Response(json.dumps({"status": "error", "reason": "Server Error"}) + '\n', mimetype='application/json'), 500
    else:
        return e

@login_required
def page_forbidden(e):
    return render_template("error/403.html"), 403

@login_required
def page_not_found(e):
    # avoid endpoint enumeration
    return render_template('error/404.html'), 404


# ========== INITIAL taxonomies ============
default_taxonomies = ["infoleak", "gdpr", "fpf", "dark-web"]
# enable default taxonomies
for taxonomy in default_taxonomies:
    Tag.enable_taxonomy_tags(taxonomy)

# ========== GIT Cache ============
clear_git_meta_cache()

# rrrr = [str(p) for p in app.url_map.iter_rules()]
# for p in rrrr:
#     print(p)

# ============ MAIN ============

if __name__ == "__main__":
    app.run(host=host, port=FLASK_PORT, threaded=True, ssl_context=ssl_context)
