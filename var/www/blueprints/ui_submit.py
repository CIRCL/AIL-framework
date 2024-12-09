#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Flask functions and routes for the Item Submit modules page
"""
##################################
# Import External packages
##################################
import re
import os
import sys
import string
import unicodedata
import uuid

from functools import wraps

# Flask
from flask import render_template, jsonify, request, Blueprint, url_for, redirect, abort
from Role_Manager import login_admin, login_user_no_api
from flask_login import login_required


##################################
# Import Project packages
##################################
from lib import Tag

from packages import Import_helper


# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl

r_serv_db = Flask_config.r_serv_db # TODO REMOVE ME
r_serv_log_submit = Flask_config.r_serv_log_submit # TODO REMOVE ME


valid_filename_chars = "-_ %s%s" % (string.ascii_letters, string.digits)

UPLOAD_FOLDER = Flask_config.UPLOAD_FOLDER

text_max_size = int(Flask_config.SUBMIT_PASTE_TEXT_MAX_SIZE) / (1000*1000)
file_max_size = int(Flask_config.SUBMIT_PASTE_FILE_MAX_SIZE) / (1000*1000*1000)
allowed_extensions = ", ". join(Flask_config.SUBMIT_PASTE_FILE_ALLOWED_EXTENSIONS)

PasteSubmit = Blueprint('PasteSubmit', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/submit'))

# ============ Validators ============
def limit_content_length():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cl = request.content_length
            if cl is not None:
                if cl > Flask_config.SUBMIT_PASTE_FILE_MAX_SIZE or ('file' not in request.files and cl > Flask_config.SUBMIT_PASTE_TEXT_MAX_SIZE):
                    abort(413)
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ============ FUNCTIONS ============

def allowed_file(filename):
    if '.' not in filename:
        return True
    else:
        file_ext = filename.rsplit('.', 1)[1].lower()
        return file_ext in Flask_config.SUBMIT_PASTE_FILE_ALLOWED_EXTENSIONS

def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace characters
    for r in replace:
        filename = filename.replace(r, '_')

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    return ''.join(c for c in cleaned_filename if c in whitelist)

# ============= ROUTES ==============

@PasteSubmit.route("/PasteSubmit/", methods=['GET'])
@login_required
@login_user_no_api
def PasteSubmit_page():
    # Get all active tags/galaxy
    active_taxonomies = Tag.get_active_taxonomies()
    active_galaxies = Tag.get_active_galaxies()

    return render_template("submit_items.html",
                            active_taxonomies = active_taxonomies,
                            active_galaxies = active_galaxies,
                            text_max_size = text_max_size,
                            file_max_size = file_max_size,
                            allowed_extensions = allowed_extensions)

@PasteSubmit.route("/PasteSubmit/submit", methods=['POST'])
@login_required
@login_user_no_api
@limit_content_length()
def submit():

    password = request.form['archive_pass']
    ltags = request.form['tags_taxonomies']
    ltagsgalaxies = request.form['tags_galaxies']
    paste_content = request.form['paste_content']
    paste_source = request.form['paste_source']

    if paste_source:
        # limit source length
        paste_source = paste_source.replace('/', '')[:80]
        if paste_source in ['crawled', 'tests']:
            content = 'Invalid source'
            return content, 400

        if not re.match('^[0-9a-zA-Z-_\+@#&\.;=:!]*$', paste_source):
            content = f'Invalid source name: Forbidden character(s)'
            return content, 400

    is_file = False
    if 'file' in request.files:
        file_import = request.files['file']
        if file_import:
            if file_import.filename:
                is_file = True

    submitted_tag = 'infoleak:submission="manual"'

    # active taxonomies
    active_taxonomies = Tag.get_active_taxonomies()
    # active galaxies
    active_galaxies = Tag.get_active_galaxies()

    if ltags or ltagsgalaxies:
        ltags = Tag.unpack_str_tags_list(ltags)
        ltagsgalaxies = Tag.unpack_str_tags_list(ltagsgalaxies)

        if not Tag.is_valid_tags_taxonomies_galaxy(ltags, ltagsgalaxies):
            content = 'INVALID TAGS'
            return content, 400

    # add submitted tags
    if not ltags:
        ltags = []
    ltags.append(submitted_tag)

    if is_file:

        if allowed_file(file_import.filename):

            # get UUID
            UUID = str(uuid.uuid4())

            # create submitted dir
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)

            if '.' not in file_import.filename:
                full_path = os.path.join(UPLOAD_FOLDER, UUID)
            else:
                if file_import.filename[-6:] == 'tar.gz':
                    file_type = 'tar.gz'
                else:
                    file_type = file_import.filename.rsplit('.', 1)[1]
                name = UUID + '.' + file_type
                full_path = os.path.join(UPLOAD_FOLDER, name)

            # Flask verify the file size
            file_import.save(full_path)

            Import_helper.create_import_queue(ltags, ltagsgalaxies, full_path, UUID, password, True)

            return render_template("submit_items.html",
                                   active_taxonomies=active_taxonomies,
                                   active_galaxies=active_galaxies,
                                   UUID=UUID)

        else:
            content = f'wrong file type, allowed_extensions: {allowed_extensions} or remove the extension'
            return content, 400

    elif paste_content != '':
        if sys.getsizeof(paste_content) < Flask_config.SUBMIT_PASTE_TEXT_MAX_SIZE:
            # get id
            UUID = str(uuid.uuid4())
            Import_helper.create_import_queue(ltags, ltagsgalaxies, paste_content, UUID, password, source=paste_source)
            return render_template("submit_items.html",
                                        active_taxonomies = active_taxonomies,
                                        active_galaxies = active_galaxies,
                                        UUID = UUID)

        else:
            content = f'text paste size is over {Flask_config.SUBMIT_PASTE_TEXT_MAX_SIZE} bytes limit'
            return content, 400

        content = 'submit aborded'
        return content, 400

    return PasteSubmit_page()

@PasteSubmit.route("/PasteSubmit/submit_status", methods=['GET'])
@login_required
@login_user_no_api
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

        if (end != None) and (nb_total != None) and (nb_end != None) and (processing != None):

            link = ''
            if paste_submit_link:
                for paste in paste_submit_link:
                    url = url_for('objects_item.showItem') + '?id=' + paste
                    link += '<a target="_blank" href="' + url + '" class="list-group-item">' + paste +'</a>'

            if nb_total == '-1':
                in_progress = nb_sucess + ' / '
            else:
                in_progress = nb_sucess + ' / ' + nb_total

            if int(nb_total) != 0:
                prog = int(int(nb_end) * 100 / int(nb_total))
            else:
                prog = 0

            isError = bool(error)

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

