#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import ssl
import time

import redis
import random
import logging
import logging.handlers
import configparser

from flask import Flask, render_template, jsonify, request, Request, session, redirect, url_for
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

import bcrypt

import flask
import importlib
from os.path import join
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
sys.path.append('./modules/')
import Paste
from Date import Date

from User import User

from pytaxonomies import Taxonomies

# Import config
import Flask_config

# Import Role_Manager
from Role_Manager import create_user_db, check_password_strength, check_user_role_integrity
from Role_Manager import login_admin, login_analyst

Flask_dir = os.environ['AIL_FLASK']

# CONFIG #
cfg = Flask_config.cfg
baseUrl = cfg.get("Flask", "baseurl")
baseUrl = baseUrl.replace('/', '')
if baseUrl != '':
    baseUrl = '/'+baseUrl

# ========= REDIS =========#
r_serv_db = redis.StrictRedis(
    host=cfg.get("ARDB_DB", "host"),
    port=cfg.getint("ARDB_DB", "port"),
    db=cfg.getint("ARDB_DB", "db"),
    decode_responses=True)
r_serv_tags = redis.StrictRedis(
    host=cfg.get("ARDB_Tags", "host"),
    port=cfg.getint("ARDB_Tags", "port"),
    db=cfg.getint("ARDB_Tags", "db"),
    decode_responses=True)

r_cache = redis.StrictRedis(
    host=cfg.get("Redis_Cache", "host"),
    port=cfg.getint("Redis_Cache", "port"),
    db=cfg.getint("Redis_Cache", "db"),
    decode_responses=True)

# logs
log_dir = os.path.join(os.environ['AIL_HOME'], 'logs')
if not os.path.isdir(log_dir):
    os.makedirs(logs_dir)

# log_filename = os.path.join(log_dir, 'flask_server.logs')
# logger = logging.getLogger()
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# handler_log = logging.handlers.TimedRotatingFileHandler(log_filename, when="midnight", interval=1)
# handler_log.suffix = '%Y-%m-%d.log'
# handler_log.setFormatter(formatter)
# handler_log.setLevel(30)
# logger.addHandler(handler_log)
# logger.setLevel(30)

# =========       =========#

# =========  TLS  =========#
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ssl_context.load_cert_chain(certfile=os.path.join(Flask_dir, 'server.crt'), keyfile=os.path.join(Flask_dir, 'server.key'))
#print(ssl_context.get_ciphers())
# =========       =========#

Flask_config.app = Flask(__name__, static_url_path=baseUrl+'/static/')
app = Flask_config.app
app.config['MAX_CONTENT_LENGTH'] = 900 * 1024 * 1024

# ========= session ========
app.secret_key = str(random.getrandbits(256))
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# ========= LOGIN MANAGER ========

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ========= HEADER GENERATION ========

# Get headers items that should be ignored (not displayed)
toIgnoreModule = set()
try:
    with open('templates/ignored_modules.txt', 'r') as f:
        lines = f.read().splitlines()
        for line in lines:
            toIgnoreModule.add(line)

except IOError:
    f = open(os.path.join(Flask_dir, 'templates', 'ignored_modules.txt'), 'w')
    f.close()

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
            #print('importing {}'.format(name))
            importlib.import_module(name)
        elif name == 'header_{}.html'.format(module_name):
            with open(join(root, name), 'r') as f:
                to_add_to_header_dico[module_name] = f.read()

#create header.html
complete_header = ""
with open(os.path.join(Flask_dir, 'templates', 'header_base.html'), 'r') as f:
    complete_header = f.read()
modified_header = complete_header

#Add the header in the supplied order
for module_name, txt in list(to_add_to_header_dico.items()):
    to_replace = '<!--{}-->'.format(module_name)
    if to_replace in complete_header:
        modified_header = modified_header.replace(to_replace, txt)
        del to_add_to_header_dico[module_name]

#Add the header for no-supplied order
to_add_to_header = []
for module_name, txt in to_add_to_header_dico.items():
    to_add_to_header.append(txt)

modified_header = modified_header.replace('<!--insert here-->', '\n'.join(to_add_to_header))

#Write the header.html file
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
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

# @app.route('/test', methods=['GET'])
# def test():
#     for rule in app.url_map.iter_rules():
#         print(rule)
#     return 'o'

# ========== ROUTES ============
@app.route('/login', methods=['POST', 'GET'])
def login():

    current_ip = request.remote_addr
    login_failed_ip = r_cache.get('failed_login_ip:{}'.format(current_ip))

    # brute force by ip
    if login_failed_ip:
        login_failed_ip = int(login_failed_ip)
        if login_failed_ip >= 5:
            error = 'Max Connection Attempts reached, Please wait {}s'.format(r_cache.ttl('failed_login_ip:{}'.format(current_ip)))
            return render_template("login.html", error=error)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        #next_page = request.form.get('next_page')

        if username is not None:
            user = User.get(username)
            login_failed_user_id = r_cache.get('failed_login_user_id:{}'.format(username))
            # brute force by user_id
            if login_failed_user_id:
                login_failed_user_id = int(login_failed_user_id)
                if login_failed_user_id >= 5:
                    error = 'Max Connection Attempts reached, Please wait {}s'.format(r_cache.ttl('failed_login_user_id:{}'.format(username)))
                    return render_template("login.html", error=error)

            if user and user.check_password(password):
                if not check_user_role_integrity(user.get_id()):
                    error = 'Incorrect User ACL, Please contact your administrator'
                    return render_template("login.html", error=error)
                login_user(user) ## TODO: use remember me ?
                if user.request_password_change():
                    return redirect(url_for('change_password'))
                else:
                    return redirect(url_for('dashboard.index'))
            # login failed
            else:
                # set brute force protection
                #logger.warning("Login failed, ip={}, username={}".format(current_ip, username))
                r_cache.incr('failed_login_ip:{}'.format(current_ip))
                r_cache.expire('failed_login_ip:{}'.format(current_ip), 300)
                r_cache.incr('failed_login_user_id:{}'.format(username))
                r_cache.expire('failed_login_user_id:{}'.format(username), 300)
                #

                error = 'Password Incorrect'
                return render_template("login.html", error=error)

        return 'please provide a valid username'

    else:
        #next_page = request.args.get('next')
        error = request.args.get('error')
        return render_template("login.html" , error=error)

@app.route('/change_password', methods=['POST', 'GET'])
@login_required
def change_password():
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')
    error = request.args.get('error')

    if error:
        return render_template("change_password.html", error=error)

    if current_user.is_authenticated and password1!=None:
        if password1==password2:
            if check_password_strength(password1):
                user_id = current_user.get_id()
                create_user_db(user_id , password1, update=True)
                return redirect(url_for('dashboard.index'))
            else:
                error = 'Incorrect password'
                return render_template("change_password.html", error=error)
        else:
            error = "Passwords don't match"
            return render_template("change_password.html", error=error)
    else:
        error = 'Please choose a new password'
        return render_template("change_password.html", error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# role error template
@app.route('/role', methods=['POST', 'GET'])
@login_required
def role():
    return render_template("error/403.html"), 403

@app.route('/searchbox/')
@login_required
@login_analyst
def searchbox():
    return render_template("searchbox.html")

# ========== ERROR HANDLER ============

@app.errorhandler(404)
@login_required
def page_not_found(e):
    # avoid endpoint enumeration
    return render_template('error/404.html'), 404

# ========== INITIAL taxonomies ============
# add default ail taxonomies
r_serv_tags.sadd('active_taxonomies', 'infoleak')
r_serv_tags.sadd('active_taxonomies', 'gdpr')
r_serv_tags.sadd('active_taxonomies', 'fpf')
# add default tags
taxonomies = Taxonomies()
for tag in taxonomies.get('infoleak').machinetags():
    r_serv_tags.sadd('active_tag_infoleak', tag)
for tag in taxonomies.get('gdpr').machinetags():
    r_serv_tags.sadd('active_tag_gdpr', tag)
for tag in taxonomies.get('fpf').machinetags():
    r_serv_tags.sadd('active_tag_fpf', tag)

# ========== INITIAL tags auto export ============
infoleak_tags = taxonomies.get('infoleak').machinetags()
infoleak_automatic_tags = []
for tag in taxonomies.get('infoleak').machinetags():
    if tag.split('=')[0][:] == 'infoleak:automatic-detection':
        r_serv_db.sadd('list_export_tags', tag)

r_serv_db.sadd('list_export_tags', 'infoleak:submission="manual"')
# ============ MAIN ============

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7000, threaded=True, ssl_context=ssl_context)
