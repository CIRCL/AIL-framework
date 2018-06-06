#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
from flask import Flask, render_template, jsonify, request, Blueprint

'''import random'''

import unicodedata
import string
import subprocess
import os
import sys
import datetime

from pytaxonomies import Taxonomies
from pymispgalaxies import Galaxies, Clusters

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_tags = Flask_config.r_serv_tags
r_serv_log_submit = Flask_config.r_serv_log_submit

PasteSubmit = Blueprint('PasteSubmit', __name__, template_folder='templates')

valid_filename_chars = "-_ %s%s" % (string.ascii_letters, string.digits)

ALLOWED_EXTENSIONS = set(['txt', 'zip', 'gzip'])

# ============ FUNCTIONS ============
def one():
    return 1

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace characters
    for r in replace:
        filename = filename.replace(r,'_')

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    return ''.join(c for c in cleaned_filename if c in whitelist)

'''@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(400)

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = some_random_string()
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def some_random_string():
    N = 15
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))'''


def addTagsVerification(tags, tagsgalaxies):

    list_tag = tags.split(',')
    list_tag_galaxies = tagsgalaxies.split(',')

    taxonomies = Taxonomies()
    active_taxonomies = r_serv_tags.smembers('active_taxonomies')

    active_galaxies = r_serv_tags.smembers('active_galaxies')

    if list_tag != ['']:
        for tag in list_tag:
            # verify input
            tax = tag.split(':')[0]
            if tax in active_taxonomies:
                if tag in r_serv_tags.smembers('active_tag_' + tax):
                    pass
                else:
                    return False
            else:
                return False

    if list_tag_galaxies != ['']:
        for tag in list_tag_galaxies:
            # verify input
            gal = tag.split(':')[1]
            gal = gal.split('=')[0]

            if gal in active_galaxies:
                if tag in r_serv_tags.smembers('active_tag_galaxies_' + gal):
                    pass
                else:
                    return False
            else:
                return False
    return True
# ============= ROUTES ==============

@PasteSubmit.route("/PasteSubmit/", methods=['GET'])
def PasteSubmit_page():
    #active taxonomies
    active_taxonomies = r_serv_tags.smembers('active_taxonomies')

    #active galaxies
    active_galaxies = r_serv_tags.smembers('active_galaxies')

    return render_template("PasteSubmit.html",
                            active_taxonomies = active_taxonomies,
                            active_galaxies = active_galaxies)

@PasteSubmit.route("/PasteSubmit/submit", methods=['POST'])
def submit():

    paste_name = request.form['paste_name']
    ltags = request.form['tags_taxonomies']
    ltagsgalaxies = request.form['tags_galaxies']
    paste_content = request.form['paste_content']

    if ltags or ltagsgalaxies:
        if not addTagsVerification(ltags, ltagsgalaxies):
            return 'INVALID TAGS'

    if 'file' not in request.files:

        file = request.files['file']

        if file.filename == '':

            if paste_content != '':
                if sys.getsizeof(paste_content) < 900000:

                    to_launch = os.environ['AIL_BIN'] + 'submit_paste.py'
                    # get id
                    id = str(r_serv_tags.get('submit_id'))

                    if paste_name:
                        # clean file name
                        id = clean_filename(paste_name)

                    # create logs
                    r_serv_log_submit.set(id + ':end', 0)
                    r_serv_log_submit.set(id + ':nb_total', 1)
                    r_serv_log_submit.set(id + ':nb_end', 0)
                    r_serv_log_submit.set(id + ':error', 'error:')

                    #incr id
                    r_serv_tags.incr('submit_id')

                    # add submitted tags
                    if(ltags != ''):
                        ltags = ltags + ',submitted'
                    else:
                        ltags ='submitted'

                    # launch process
                    process = subprocess.Popen(["python", to_launch, ltags, ltagsgalaxies, paste_content, paste_name, id],
                                                   stdout=subprocess.PIPE)

                    return render_template("submiting.html",
                                                id = id)

                else:
                    return 'size error'

            return 'submit'

         if file and allowed_file(file.filename):
            print(file.read())

    return 'error'

@PasteSubmit.route("/PasteSubmit/submit_status", methods=['GET'])
def submit_status():
    id = request.args.get('id')

    if id:
        end = r_serv_log_submit.get(id + ':end')
        nb_total = r_serv_log_submit.get(id + ':nb_total')
        nb_end = r_serv_log_submit.get(id + ':nb_end')
        error = r_serv_log_submit.get(id + ':error')
        if (end != None) and (nb_total != None) and (nb_end != None) and (error != None):

            in_progress = nb_end + ' / ' + nb_total
            prog = int(int(nb_end) * 100 / int(nb_total))

            if error == 'error:':
                isError = False
            else:
                isError = True

            if end == '0':
                end = False
            else:
                end = True

            return jsonify(end=end,
                            in_progress=in_progress,
                            prog=prog,
                            isError=isError,
                            error=error)
        else:
            return 'to do'
    else:
        return 'INVALID ID'

# ========= REGISTRATION =========
app.register_blueprint(PasteSubmit)
