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
from Role_Manager import login_admin, login_analyst
from flask_login import login_required


##################################
# Import Project packages
##################################
from export import Export
from lib import Tag
from lib.objects.Items import Item

from packages import Import_helper

from pytaxonomies import Taxonomies # TODO REMOVE ME


# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl

r_serv_db = Flask_config.r_serv_db # TODO REMOVE ME
r_serv_log_submit = Flask_config.r_serv_log_submit # TODO REMOVE ME

logger = Flask_config.redis_logger


valid_filename_chars = "-_ %s%s" % (string.ascii_letters, string.digits)

UPLOAD_FOLDER = Flask_config.UPLOAD_FOLDER

text_max_size = int(Flask_config.SUBMIT_PASTE_TEXT_MAX_SIZE) / (1000*1000)
file_max_size = int(Flask_config.SUBMIT_PASTE_FILE_MAX_SIZE) / (1000*1000*1000)
allowed_extensions = ", ". join(Flask_config.SUBMIT_PASTE_FILE_ALLOWED_EXTENSIONS)

PasteSubmit = Blueprint('PasteSubmit', __name__, template_folder='templates')

# ============ Validators ============
def limit_content_length():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger.debug('decorator')
            cl = request.content_length
            if cl is not None:
                if cl > Flask_config.SUBMIT_PASTE_FILE_MAX_SIZE or ('file' not in request.files and cl > Flask_config.SUBMIT_PASTE_TEXT_MAX_SIZE):
                    logger.debug('abort')
                    abort(413)
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ============ FUNCTIONS ============

def allowed_file(filename):
    if not '.' in filename:
        return True
    else:
        file_ext = filename.rsplit('.', 1)[1].lower()
        logger.debug(file_ext)
        logger.debug(Flask_config.SUBMIT_PASTE_FILE_ALLOWED_EXTENSIONS)
        return file_ext in Flask_config.SUBMIT_PASTE_FILE_ALLOWED_EXTENSIONS

def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace characters
    for r in replace:
        filename = filename.replace(r,'_')

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    return ''.join(c for c in cleaned_filename if c in whitelist)

# ============= ROUTES ==============

@PasteSubmit.route("/PasteSubmit/", methods=['GET'])
@login_required
@login_analyst
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
@login_analyst
@limit_content_length()
def submit():

    #paste_name = request.form['paste_name']
    logger.debug('submit')

    password = request.form['archive_pass']
    ltags = request.form['tags_taxonomies']
    ltagsgalaxies = request.form['tags_galaxies']
    paste_content = request.form['paste_content']
    paste_source = request.form['paste_source']

    if paste_source:
    # limit source length
        paste_source = paste_source.replace('/', '')[:80]
        if paste_source in ['crawled', 'tests']:
            content = f'Invalid source'
            logger.info(paste_source)
            return content, 400

        if not re.match('^[0-9a-zA-Z-_\+@#&\.;=:!]*$', paste_source):
            content = f'Invalid source name: Forbidden character(s)'
            logger.info(content)
            return content, 400

    is_file = False
    if 'file' in request.files:
        file_import = request.files['file']
        if file_import:
            if file_import.filename:
                is_file = True

    logger.debug(f'is file ? {is_file}')

    submitted_tag = 'infoleak:submission="manual"'

    #active taxonomies
    active_taxonomies = Tag.get_active_taxonomies()
    #active galaxies
    active_galaxies = Tag.get_active_galaxies()

    if ltags or ltagsgalaxies:
        logger.debug(f'ltags ? {ltags} {ltagsgalaxies}')
        ltags = Tag.unpack_str_tags_list(ltags)
        ltagsgalaxies = Tag.unpack_str_tags_list(ltagsgalaxies)

        if not Tag.is_valid_tags_taxonomies_galaxy(ltags, ltagsgalaxies):
            content = 'INVALID TAGS'
            logger.info(content)
            return content, 400

    # add submitted tags
    if not ltags:
        ltags = []
    ltags.append(submitted_tag)

    if is_file:
        logger.debug('file management')

        if allowed_file(file_import.filename):
            logger.debug('file extension allowed')

            # get UUID
            UUID = str(uuid.uuid4())

            '''if paste_name:
                # clean file name
                UUID = clean_filename(paste_name)'''

            # create submitted dir
            if not os.path.exists(UPLOAD_FOLDER):
                logger.debug('create folder')
                os.makedirs(UPLOAD_FOLDER)

            if not '.' in file_import.filename:
                logger.debug('add UUID to path')
                full_path = os.path.join(UPLOAD_FOLDER, UUID)
            else:
                if file_import.filename[-6:] == 'tar.gz':
                    logger.debug('file extension is tar.gz')
                    file_type = 'tar.gz'
                else:
                    file_type = file_import.filename.rsplit('.', 1)[1]
                    logger.debug(f'file type {file_type}')
                name = UUID + '.' + file_type
                full_path = os.path.join(UPLOAD_FOLDER, name)
                logger.debug(f'full path {full_path}')

            #Flask verify the file size
            file_import.save(full_path)
            logger.debug('file saved')

            Import_helper.create_import_queue(ltags, ltagsgalaxies, full_path, UUID, password, True)

            return render_template("submit_items.html",
                                        active_taxonomies = active_taxonomies,
                                        active_galaxies = active_galaxies,
                                        UUID = UUID)

        else:
            content = f'wrong file type, allowed_extensions: {allowed_extensions} or remove the extension'
            logger.info(content)
            return content, 400


    elif paste_content != '':
        logger.debug(f'entering text paste management')
        if sys.getsizeof(paste_content) < Flask_config.SUBMIT_PASTE_TEXT_MAX_SIZE:
            logger.debug(f'size {sys.getsizeof(paste_content)}')
            # get id
            UUID = str(uuid.uuid4())
            logger.debug('create import')
            Import_helper.create_import_queue(ltags, ltagsgalaxies, paste_content, UUID, password, source=paste_source)
            logger.debug('import OK')
            return render_template("submit_items.html",
                                        active_taxonomies = active_taxonomies,
                                        active_galaxies = active_galaxies,
                                        UUID = UUID)

        else:
            content = f'text paste size is over {Flask_config.SUBMIT_PASTE_TEXT_MAX_SIZE} bytes limit'
            logger.info(content)
            return content, 400

        content = 'submit aborded'
        logger.error(content)
        return content, 400


    return PasteSubmit_page()

@PasteSubmit.route("/PasteSubmit/submit_status", methods=['GET'])
@login_required
@login_analyst
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

            if error:
                isError = True
            else:
                isError = False

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


######################################################################################################
######################################################################################################
######################################################################################################
######################################################################################################

# TODO MIGRATE TAGS PUSH

# TEMPORARY: 2 SET OF CUSTOM + infoleak tags ?????????


@PasteSubmit.route("/PasteSubmit/edit_tag_export")
@login_required
@login_analyst
def edit_tag_export():
    misp_auto_events = r_serv_db.get('misp:auto-events')
    hive_auto_alerts = r_serv_db.get('hive:auto-alerts')

    whitelist_misp = r_serv_db.scard('whitelist_misp')
    whitelist_hive = r_serv_db.scard('whitelist_hive')

    list_export_tags = list(r_serv_db.smembers('list_export_tags'))
    status_misp = []
    status_hive = []

    infoleak_tags = Taxonomies().get('infoleak').machinetags()
    is_infoleak_tag = []

    for tag in list_export_tags:
        if r_serv_db.sismember('whitelist_misp', tag):
            status_misp.append(True)
        else:
            status_misp.append(False)

    for tag in list_export_tags:
        if r_serv_db.sismember('whitelist_hive', tag):
            status_hive.append(True)
        else:
            status_hive.append(False)

        if tag in infoleak_tags:
            is_infoleak_tag.append(True)
        else:
            is_infoleak_tag.append(False)

    if misp_auto_events is not None:
        if int(misp_auto_events) == 1:
            misp_active = True
        else:
            misp_active = False
    else:
        misp_active = False

    if hive_auto_alerts is not None:
        if int(hive_auto_alerts)  == 1:
            hive_active = True
        else:
            hive_active = False
    else:
        hive_active = False

    nb_tags = str(r_serv_db.scard('list_export_tags'))
    nb_tags_whitelist_misp = str(r_serv_db.scard('whitelist_misp')) + ' / ' + nb_tags
    nb_tags_whitelist_hive = str(r_serv_db.scard('whitelist_hive')) + ' / ' + nb_tags

    return render_template("edit_tag_export.html",
                            misp_active=misp_active,
                            hive_active=hive_active,
                            list_export_tags=list_export_tags,
                            is_infoleak_tag=is_infoleak_tag,
                            status_misp=status_misp,
                            status_hive=status_hive,
                            nb_tags_whitelist_misp=nb_tags_whitelist_misp,
                            nb_tags_whitelist_hive=nb_tags_whitelist_hive,
                            flag_misp=True,
                            flag_hive=True)

@PasteSubmit.route("/PasteSubmit/tag_export_edited", methods=['POST'])
@login_required
@login_analyst
def tag_export_edited():
    tag_enabled_misp = request.form.getlist('tag_enabled_misp')
    tag_enabled_hive = request.form.getlist('tag_enabled_hive')

    list_export_tags = list(r_serv_db.smembers('list_export_tags'))

    r_serv_db.delete('whitelist_misp')
    r_serv_db.delete('whitelist_hive')

    for tag in tag_enabled_misp:
        if r_serv_db.sismember('list_export_tags', tag):
            r_serv_db.sadd('whitelist_misp', tag)
        else:
            return 'invalid input'

    for tag in tag_enabled_hive:
        if r_serv_db.sismember('list_export_tags', tag):
            r_serv_db.sadd('whitelist_hive', tag)
        else:
            return 'invalid input'

    return redirect(url_for('PasteSubmit.edit_tag_export'))

@PasteSubmit.route("/PasteSubmit/enable_misp_auto_event")
@login_required
@login_analyst
def enable_misp_auto_event():
    r_serv_db.set('misp:auto-events', 1)
    return edit_tag_export()

@PasteSubmit.route("/PasteSubmit/disable_misp_auto_event")
@login_required
@login_analyst
def disable_misp_auto_event():
    r_serv_db.set('misp:auto-events', 0)
    return edit_tag_export()

@PasteSubmit.route("/PasteSubmit/enable_hive_auto_alert")
@login_required
@login_analyst
def enable_hive_auto_alert():
    r_serv_db.set('hive:auto-alerts', 1)
    return edit_tag_export()

@PasteSubmit.route("/PasteSubmit/disable_hive_auto_alert")
@login_required
@login_analyst
def disable_hive_auto_alert():
    r_serv_db.set('hive:auto-alerts', 0)
    return edit_tag_export()

@PasteSubmit.route("/PasteSubmit/add_push_tag")
@login_required
@login_analyst
def add_push_tag():
    tag = request.args.get('tag')
    if tag is not None:

        #limit tag length
        if len(tag) > 49:
            tag = tag[0:48]

        r_serv_db.sadd('list_export_tags', tag)

        to_return = {}
        to_return["tag"] = tag
        return jsonify(to_return)
    else:
        return 'None args', 400

@PasteSubmit.route("/PasteSubmit/delete_push_tag")
@login_required
@login_analyst
def delete_push_tag():
    tag = request.args.get('tag')

    infoleak_tags = Taxonomies().get('infoleak').machinetags()
    if tag not in infoleak_tags and r_serv_db.sismember('list_export_tags', tag):
        r_serv_db.srem('list_export_tags', tag)
        r_serv_db.srem('whitelist_misp', tag)
        r_serv_db.srem('whitelist_hive', tag)
        to_return = {}
        to_return["tag"] = tag
        return jsonify(to_return)
    else:
        return 'this tag can\'t be removed', 400

# ========= REGISTRATION =========
app.register_blueprint(PasteSubmit, url_prefix=baseUrl)
