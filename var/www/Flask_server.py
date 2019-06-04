#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import redis
import configparser
import json
import datetime
import time
import calendar
from flask import Flask, render_template, jsonify, request, Request
import flask
import importlib
import os
from os.path import join
import sys
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
sys.path.append('./modules/')
import Paste
from Date import Date

from pytaxonomies import Taxonomies

# Import config
import Flask_config

# CONFIG #
cfg = Flask_config.cfg
baseUrl = cfg.get("Flask", "baseurl")
baseUrl = baseUrl.replace('/', '')
if baseUrl != '':
    baseUrl = '/'+baseUrl

Flask_config.app = Flask(__name__, static_url_path=baseUrl+'/static/')
app = Flask_config.app
app.config['MAX_CONTENT_LENGTH'] = 900 * 1024 * 1024

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
@app.route('/searchbox/')
def searchbox():
    return render_template("searchbox.html")


# ========== INITIAL taxonomies ============
r_serv_tags = redis.StrictRedis(
    host=cfg.get("ARDB_Tags", "host"),
    port=cfg.getint("ARDB_Tags", "port"),
    db=cfg.getint("ARDB_Tags", "db"),
    decode_responses=True)
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
r_serv_db = redis.StrictRedis(
    host=cfg.get("ARDB_DB", "host"),
    port=cfg.getint("ARDB_DB", "port"),
    db=cfg.getint("ARDB_DB", "db"),
    decode_responses=True)
infoleak_tags = taxonomies.get('infoleak').machinetags()
infoleak_automatic_tags = []
for tag in taxonomies.get('infoleak').machinetags():
    if tag.split('=')[0][:] == 'infoleak:automatic-detection':
        r_serv_db.sadd('list_export_tags', tag)

r_serv_db.sadd('list_export_tags', 'infoleak:submission="manual"')
# ============ MAIN ============

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7000, threaded=True)
