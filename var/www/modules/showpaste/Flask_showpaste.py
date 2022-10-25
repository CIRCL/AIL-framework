#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import json
import os
import sys
import flask
from flask import Flask, render_template, jsonify, request, Blueprint, make_response, Response, send_from_directory, redirect, url_for, abort

from Role_Manager import login_admin, login_analyst, login_read_only, no_cache
from flask_login import login_required

import difflib

import Paste
import requests

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Item

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl
r_serv_metadata = Flask_config.r_serv_metadata
r_serv_tags = Flask_config.r_serv_tags
r_serv_statistics = Flask_config.r_serv_statistics
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal
DiffMaxLineLength = Flask_config.DiffMaxLineLength
bootstrap_label = Flask_config.bootstrap_label
misp_event_url = Flask_config.misp_event_url
hive_case_url = Flask_config.hive_case_url
vt_enabled = Flask_config.vt_enabled
PASTES_FOLDER = Flask_config.PASTES_FOLDER
SCREENSHOT_FOLDER = Flask_config.SCREENSHOT_FOLDER

showsavedpastes = Blueprint('showsavedpastes', __name__, template_folder='templates')

# ============ FUNCTIONS ============

def get_item_screenshot_path(item):
    screenshot = r_serv_metadata.hget('paste_metadata:{}'.format(item), 'screenshot')
    if screenshot:
        screenshot = os.path.join(screenshot[0:2], screenshot[2:4], screenshot[4:6], screenshot[6:8], screenshot[8:10], screenshot[10:12], screenshot[12:])
    else:
        screenshot = ''
    return screenshot

def get_item_basic_info(item):
    item_basic_info = {}
    item_basic_info['date'] = str(item.get_p_date())
    item_basic_info['date'] = '{}/{}/{}'.format(item_basic_info['date'][0:4], item_basic_info['date'][4:6], item_basic_info['date'][6:8])
    item_basic_info['source'] = item.get_item_source()
    item_basic_info['size'] = item.get_item_size()

    ## TODO: FIXME ##performance
    item_basic_info['encoding'] = item._get_p_encoding()
    ## TODO: FIXME ##performance
    #item_basic_info['language'] = item._get_p_language()
    ## TODO: FIXME ##performance
    info_line = item.get_lines_info()
    item_basic_info['nb_lines'] = info_line[0]
    item_basic_info['max_length_line'] = info_line[1]

    return item_basic_info

def show_item_min(requested_path , content_range=0):
    relative_path = None
    if PASTES_FOLDER not in requested_path:
        relative_path = requested_path
        requested_path = os.path.join(PASTES_FOLDER, requested_path)
    else:
        relative_path = requested_path.replace(PASTES_FOLDER, '', 1)
    # remove old full path
    # requested_path = requested_path.replace(PASTES_FOLDER, '')
    # escape directory transversal
    if os.path.commonprefix((os.path.realpath(requested_path),PASTES_FOLDER)) != PASTES_FOLDER:
        return 'path transversal detected'

    item_info ={}

    paste = Paste.Paste(requested_path)
    item_basic_info = get_item_basic_info(paste)
    item_info['nb_duplictates'] = paste.get_nb_duplicate()

    ## TODO: use this for fix ?
    item_content = paste.get_p_content()
    char_to_display = len(item_content)
    if content_range != 0:
       item_content = item_content[0:content_range]

    vt_enabled = Flask_config.vt_enabled


    p_hashtype_list = []

    print(requested_path)
    l_tags = r_serv_metadata.smembers('tag:'+relative_path)
    if relative_path is not None:
        l_tags.union( r_serv_metadata.smembers('tag:'+relative_path) )
    item_info['tags'] = l_tags
    item_info['name'] = relative_path.replace('/', ' / ')


    l_64 = []
    # load hash files
    if r_serv_metadata.scard('hash_paste:'+relative_path) > 0:
        set_b64 = r_serv_metadata.smembers('hash_paste:'+relative_path)
        for hash in set_b64:
            nb_in_file = r_serv_metadata.zscore('nb_seen_hash:'+hash, relative_path)
            # item list not updated
            if nb_in_file is None:
                l_pastes = r_serv_metadata.zrange('nb_seen_hash:'+hash, 0, -1)
                for paste_name in l_pastes:
                    # dynamic update
                    if PASTES_FOLDER in paste_name:
                        score = r_serv_metadata.zscore('nb_seen_hash:{}'.format(hash), paste_name)
                        r_serv_metadata.zrem('nb_seen_hash:{}'.format(hash), paste_name)
                        paste_name = paste_name.replace(PASTES_FOLDER, '', 1)
                        r_serv_metadata.zadd('nb_seen_hash:{}'.format(hash), score, paste_name)
                nb_in_file = r_serv_metadata.zscore('nb_seen_hash:{}'.format(hash), relative_path)
            nb_in_file = int(nb_in_file)
            estimated_type = r_serv_metadata.hget('metadata_hash:'+hash, 'estimated_type')
            file_type = estimated_type.split('/')[0]
            # set file icon
            if file_type == 'application':
                file_icon = 'fa-file '
            elif file_type == 'audio':
                file_icon = 'fa-file-video '
            elif file_type == 'image':
                file_icon = 'fa-file-image'
            elif file_type == 'text':
                file_icon = 'fa-file-alt'
            else:
                file_icon =  'fa-file'
            saved_path = r_serv_metadata.hget('metadata_hash:'+hash, 'saved_path')
            if r_serv_metadata.hexists('metadata_hash:'+hash, 'vt_link'):
                b64_vt = True
                b64_vt_link = r_serv_metadata.hget('metadata_hash:'+hash, 'vt_link')
                b64_vt_report = r_serv_metadata.hget('metadata_hash:'+hash, 'vt_report')
            else:
                b64_vt = False
                b64_vt_link = ''
                b64_vt_report = r_serv_metadata.hget('metadata_hash:'+hash, 'vt_report')
                # hash never refreshed
                if b64_vt_report is None:
                    b64_vt_report = ''

            l_64.append( (file_icon, estimated_type, hash, saved_path, nb_in_file, b64_vt, b64_vt_link, b64_vt_report) )

    crawler_metadata = {}
    if 'infoleak:submission="crawler"' in l_tags:
        crawler_metadata['get_metadata'] = True
        crawler_metadata['domain'] = r_serv_metadata.hget('paste_metadata:'+relative_path, 'domain')
        crawler_metadata['domain'] = crawler_metadata['domain'].rsplit(':', 1)[0]
        crawler_metadata['paste_father'] = r_serv_metadata.hget('paste_metadata:'+relative_path, 'father')
        crawler_metadata['real_link'] = r_serv_metadata.hget('paste_metadata:'+relative_path,'real_link')
        crawler_metadata['screenshot'] = get_item_screenshot_path(relative_path)
        # crawler_metadata['har_file'] = Item.get_item_har(relative_path)
    else:
        crawler_metadata['get_metadata'] = False

    item_parent = Item.get_item_parent(requested_path)

    misp_event = r_serv_metadata.get('misp_events:' + requested_path)
    if misp_event is None:
        misp_eventid = False
        misp_url = ''
    else:
        misp_eventid = True
        misp_url = misp_event_url + misp_event

    hive_case = r_serv_metadata.get('hive_cases:' + requested_path)
    if hive_case is None:
        hive_caseid = False
        hive_url = ''
    else:
        hive_caseid = True
        hive_url = hive_case_url.replace('id_here', hive_case)

    return render_template("show_saved_item_min.html", bootstrap_label=bootstrap_label, content=item_content,
                            item_basic_info=item_basic_info, item_info=item_info,
                            item_parent=item_parent,
                            initsize=len(item_content),
                            hashtype_list = p_hashtype_list,
                            crawler_metadata=crawler_metadata,
                            l_64=l_64, vt_enabled=vt_enabled, misp_eventid=misp_eventid, misp_url=misp_url, hive_caseid=hive_caseid, hive_url=hive_url)

# ============ ROUTES ============

@showsavedpastes.route("/showsaveditem_min/") #completely shows the paste in a new tab
@login_required
@login_read_only
def showsaveditem_min():
    requested_path = request.args.get('paste', '')
    return show_item_min(requested_path)

@showsavedpastes.route("/showsavedrawpaste/") #shows raw
@login_required
@login_read_only
def showsavedrawpaste():
    requested_path = request.args.get('paste', '')
    paste = Paste.Paste(requested_path)
    content = paste.get_p_content()
    return Response(content, mimetype='text/plain')

@showsavedpastes.route("/showpreviewpaste/")
@login_required
@login_read_only
def showpreviewpaste():
    num = request.args.get('num', '')
    requested_path = request.args.get('paste', '')
    return "|num|"+num+"|num|"+show_item_min(requested_path, content_range=max_preview_modal)


@showsavedpastes.route("/getmoredata/")
@login_required
@login_read_only
def getmoredata():
    requested_path = request.args.get('paste', '')
    paste = Paste.Paste(requested_path)
    p_content = paste.get_p_content()
    to_return = p_content[max_preview_modal-1:]
    return to_return

@showsavedpastes.route("/showDiff/")
@login_required
@login_analyst
def showDiff():
    s1 = request.args.get('s1', '')
    s2 = request.args.get('s2', '')
    p1 = Paste.Paste(s1)
    p2 = Paste.Paste(s2)
    maxLengthLine1 = p1.get_lines_info()[1]
    maxLengthLine2 = p2.get_lines_info()[1]
    if maxLengthLine1 > DiffMaxLineLength or maxLengthLine2 > DiffMaxLineLength:
        return "Can't make the difference as the lines are too long."
    htmlD = difflib.HtmlDiff()
    lines1 = p1.get_p_content().splitlines()
    lines2 = p2.get_p_content().splitlines()
    the_html = htmlD.make_file(lines1, lines2)
    return the_html

@showsavedpastes.route('/screenshot/<path:filename>')
@login_required
@login_read_only
@no_cache
def screenshot(filename):
    return send_from_directory(SCREENSHOT_FOLDER, filename+'.png', as_attachment=True)

@showsavedpastes.route('/send_file_to_vt/', methods=['POST'])
@login_required
@login_analyst
def send_file_to_vt():
    b64_path = request.form['b64_path']
    paste = request.form['paste']
    hash = request.form['hash']

    ## TODO:  # FIXME:  path transversal
    b64_full_path = os.path.join(os.environ['AIL_HOME'], b64_path)
    b64_content = ''
    with open(b64_full_path, 'rb') as f:
        b64_content = f.read()

    files = {'file': (hash, b64_content)}
    response = requests.post('https://www.virustotal.com/vtapi/v2/file/scan', files=files, params=vt_auth)
    json_response = response.json()
    print(json_response)

    vt_b64_link = json_response['permalink'].split('analysis')[0] + 'analysis/'
    r_serv_metadata.hset('metadata_hash:'+hash, 'vt_link', vt_b64_link)

    return redirect(url_for('showsavedpastes.showsavedpaste', paste=paste))

# ========= REGISTRATION =========
app.register_blueprint(showsavedpastes, url_prefix=baseUrl)
