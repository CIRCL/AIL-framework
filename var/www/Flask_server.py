#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import redis
import configparser
import random
import json
import datetime
import time
import calendar
from flask import Flask, render_template, jsonify, request, Request, session, redirect, url_for
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

import bcrypt

import flask
import importlib
import os
import re
from os.path import join
import sys
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
sys.path.append('./modules/')
import Paste
from Date import Date

from User import User

from pytaxonomies import Taxonomies

# Import config
import Flask_config

def flask_init():
    # check if an account exists
    if not r_serv_db.exists('user:all'):
        password = secrets.token_urlsafe()
        create_user_db('admin@admin.test', password, role='admin',default=True)
    # add default roles
    if not r_serv_db.exists('ail:all_role'):
        r_serv_db.zadd('ail:all_role', 1, 'admin')
        r_serv_db.zadd('ail:all_role', 2, 'analyst')

def hashing_password(bytes_password):
    hashed = bcrypt.hashpw(bytes_password, bcrypt.gensalt())
    return hashed

def verify_password(id, bytes_password):
    hashed_password = r_serv_db.hget('user:all', id)
    if bcrypt.checkpw(password, hashed):
        return True
    else:
        return False

def check_password_strength(password):
    result = regex_password.match(password)
    if result:
        return True
    else:
        return False


def create_user_db(username_id , password, default=False, role=None, update=False):
    password = password.encode()
    password_hash = hashing_password(password)
    r_serv_db.hset('user:all', username_id, password_hash)
    if update:
        r_serv_db.hdel('user_metadata:{}'.format(username_id), 'change_passwd')
        if username_id=='admin@admin.test':
            os.remove(default_passwd_file)
    else:
        if default:
            r_serv_db.hset('user_metadata:{}'.format(username_id), 'change_passwd', True)
        if role:
            if role in get_all_role():
                r_serv_db.sadd('user_role:{}'.format(role), username_id)

def get_all_role():
    return r_serv_db.zrange('ail:all_role', 0 , -1)

# CONFIG #
cfg = Flask_config.cfg
baseUrl = cfg.get("Flask", "baseurl")
baseUrl = baseUrl.replace('/', '')
if baseUrl != '':
    baseUrl = '/'+baseUrl

default_passwd_file = os.path.join(os.environ['AIL_HOME'], 'DEFAULT_PASSWORD')

regex_password = r'^(?=(.*\d){2})(?=.*[a-z])(?=.*[A-Z]).{10,}$'
regex_password = re.compile(regex_password)

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
    f = open('templates/ignored_modules.txt', 'w')
    f.close()

# Dynamically import routes and functions from modules
# Also, prepare header.html
to_add_to_header_dico = {}
for root, dirs, files in os.walk('modules/'):
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
with open('templates/header_base.html', 'r') as f:
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
with open('templates/header.html', 'w') as f:
    f.write(modified_header)

flask_init()


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

# ========== ROUTES ============
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        #next_page = request.form.get('next_page')

        if username is not None:
            user = User.get(username)
            if user and user.check_password(password):
                login_user(user) ## TODO: use remember me ?
                print(user.is_active)
                if user.request_password_change():
                    return redirect(url_for('change_password'))
                else:
                    return redirect(url_for('dashboard.index'))
            else:
                return 'incorrect password'

        return 'none'

    else:
        #next_page = request.args.get('next')
        return render_template("login.html")

@app.route('/change_password', methods=['POST', 'GET'])
@login_required
def change_password():
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    # # TODO: display errors message

    if current_user.is_authenticated and password1!=None and password1==password2:
        if check_password_strength(password1):
            user_id = current_user.get_id()
            create_user_db(user_id , password1, update=True)
            return redirect(url_for('dashboard.index'))
        else:
            return render_template("change_password.html")
    else:
        return render_template("change_password.html")

@app.route('/role', methods=['POST', 'GET'])
def role():
    return 'ERROR role'

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/create_user')
@login_required
def create_user():
    username = request.form.get('username')
    password = request.form.get('password')
    #role = request.form.get('role') ## TODO: create role

    ## TODO: validate username
    ## TODO: validate password

    username = 'admin@admin.test'
    password = 'admin'

    if r_serv_db.hexists('user:all', username):
        return 'this id is not available'

    create_user_db(username, password)

    return 'True'


@app.route('/searchbox/')
def searchbox():
    return render_template("searchbox.html")


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
    app.run(host='0.0.0.0', port=7000, threaded=True)
