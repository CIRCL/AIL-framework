#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
from flask import Flask, render_template, jsonify, request, Blueprint, url_for

import unicodedata
import string
import subprocess
import os
import sys
import datetime
import uuid

from pytaxonomies import Taxonomies
from pymispgalaxies import Galaxies, Clusters

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_tags = Flask_config.r_serv_tags
r_serv_metadata = Flask_config.r_serv_metadata
r_serv_db = Flask_config.r_serv_db
r_serv_log_submit = Flask_config.r_serv_log_submit

PasteSubmit = Blueprint('PasteSubmit', __name__, template_folder='templates')

valid_filename_chars = "-_ %s%s" % (string.ascii_letters, string.digits)

ALLOWED_EXTENSIONS = set(['txt', 'zip', 'gz', 'tar.gz'])
UPLOAD_FOLDER = Flask_config.UPLOAD_FOLDER

# ============ FUNCTIONS ============
def one():
    return 1

def allowed_file(filename):
    if not '.' in filename:
        return True
    else:
        return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace characters
    for r in replace:
        filename = filename.replace(r,'_')

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    return ''.join(c for c in cleaned_filename if c in whitelist)

def launch_submit(ltags, ltagsgalaxies, paste_content, UUID,  password, isfile = False):

    print(UUID)

    # save temp value on disk
    r_serv_db.set(UUID + ':ltags', ltags)
    r_serv_db.set(UUID + ':ltagsgalaxies', ltagsgalaxies)
    r_serv_db.set(UUID + ':paste_content', paste_content)
    r_serv_db.set(UUID + ':password', password)
    r_serv_db.set(UUID + ':isfile', isfile)

    r_serv_log_submit.set(UUID + ':end', 0)
    r_serv_log_submit.set(UUID + ':processing', 0)
    r_serv_log_submit.set(UUID + ':nb_total', -1)
    r_serv_log_submit.set(UUID + ':nb_end', 0)
    r_serv_log_submit.set(UUID + ':nb_sucess', 0)
    r_serv_log_submit.set(UUID + ':error', 'error:')
    r_serv_log_submit.sadd(UUID + ':paste_submit_link', '')


    # save UUID on disk
    r_serv_db.sadd('submitted:uuid', UUID)


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

    #paste_name = request.form['paste_name']

    password = request.form['password']
    ltags = request.form['tags_taxonomies']
    ltagsgalaxies = request.form['tags_galaxies']
    paste_content = request.form['paste_content']

    if ltags or ltagsgalaxies:
        if not addTagsVerification(ltags, ltagsgalaxies):
            return 'INVALID TAGS'

    # add submitted tags
    if(ltags != ''):
        ltags = ltags + ',submitted'
    else:
        ltags ='submitted'

    print(request.files)

    if 'file' in request.files:
        print(request.files)

        file = request.files['file']
        if file:

            if file and allowed_file(file.filename):

                # get UUID
                UUID = str(uuid.uuid4())

                '''if paste_name:
                    # clean file name
                    UUID = clean_filename(paste_name)'''

                if not '.' in file.filename:
                    full_path = os.path.join(UPLOAD_FOLDER, UUID)
                else:
                    if file.filename[-6:] == 'tar.gz':
                        file_type = 'tar.gz'
                    else:
                        file_type = file.filename.rsplit('.', 1)[1]
                    name = UUID + '.' + file_type
                    full_path = os.path.join(UPLOAD_FOLDER, name)

                #Flask verify the file size
                file.save(full_path)

                paste_content = full_path

                launch_submit(ltags, ltagsgalaxies, paste_content, UUID, password ,True)

                return render_template("submiting.html",
                                            UUID = UUID)

            else:
                print('wrong file type')


    if paste_content != '':
        if sys.getsizeof(paste_content) < 900000:

            # get id
            UUID = str(uuid.uuid4())
            print(UUID)

            #if paste_name:
                # clean file name
                #id = clean_filename(paste_name)

            launch_submit(ltags, ltagsgalaxies, paste_content, UUID, password)

            return render_template("submiting.html",
                                        UUID = UUID)

        else:
            return 'size error'

        return 'submit'


    return PasteSubmit_page()

@PasteSubmit.route("/PasteSubmit/submit_status", methods=['GET'])
def submit_status():
    UUID = request.args.get('UUID')

    if UUID:
        end = r_serv_log_submit.get(UUID + ':end')
        nb_total = r_serv_log_submit.get(UUID + ':nb_total')
        nb_end = r_serv_log_submit.get(UUID + ':nb_end')
        error = r_serv_log_submit.get(UUID + ':error')
        processing = r_serv_log_submit.get(UUID + ':processing')
        nb_sucess = r_serv_log_submit.get(UUID + ':nb_sucess')
        paste_submit_link = list(r_serv_log_submit.smembers(UUID + ':paste_submit_link'))

        if (end != None) and (nb_total != None) and (nb_end != None) and (error != None) and (processing != None) and (paste_submit_link != None):

            link = ''
            if paste_submit_link:
                for paste in paste_submit_link:
                    url = url_for('showsavedpastes.showsavedpaste') + '?paste=' + paste
                    link += '<a target="_blank" href="' + url + '" class="list-group-item">' + paste +'</a>'

            if nb_total == '-1':
                in_progress = nb_sucess + ' / '
            else:
                in_progress = nb_sucess + ' / ' + nb_total

            if int(nb_total) != 0:
                prog = int(int(nb_end) * 100 / int(nb_total))
            else:
                prog = 0

            if error == 'error:':
                isError = False
            else:
                isError = True

            if end == '0':
                end = False
            else:
                end = True

            if processing == '0':
                processing = False
            else:
                processing = True

            return jsonify(end=end,
                            in_progress=in_progress,
                            prog=prog,
                            link=link,
                            processing=processing,
                            isError=isError,
                            error=error)
        else:
            # FIXME TODO
            print(end)
            print(nb_total)
            print(nb_end)
            print(error)
            print(processing)
            print(nb_sucess)
            return 'to do'
    else:
        return 'INVALID UUID'

# ========= REGISTRATION =========
app.register_blueprint(PasteSubmit)
