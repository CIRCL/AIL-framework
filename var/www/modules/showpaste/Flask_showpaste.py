#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import os
import json
import os
import flask
<<<<<<< HEAD
from flask import Flask, render_template, jsonify, request, Blueprint, make_response, Response, send_from_directory
=======
from flask import Flask, render_template, jsonify, request, Blueprint, make_response, redirect, url_for, Response, send_from_directory
>>>>>>> master
import difflib
import ssdeep

import Paste
import requests

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_pasteName = Flask_config.r_serv_pasteName
r_serv_metadata = Flask_config.r_serv_metadata
r_serv_tags = Flask_config.r_serv_tags
r_serv_statistics = Flask_config.r_serv_statistics
r_serv_onion = Flask_config.r_serv_onion
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal
DiffMaxLineLength = Flask_config.DiffMaxLineLength
bootstrap_label = Flask_config.bootstrap_label
misp_event_url = Flask_config.misp_event_url
hive_case_url = Flask_config.hive_case_url
vt_enabled = Flask_config.vt_enabled
SCREENSHOT_FOLDER = Flask_config.SCREENSHOT_FOLDER

showsavedpastes = Blueprint('showsavedpastes', __name__, template_folder='templates')

# ============ FUNCTIONS ============

def showpaste(content_range, requested_path):
    vt_enabled = Flask_config.vt_enabled

    paste = Paste.Paste(requested_path)
    p_date = str(paste._get_p_date())
    p_date = p_date[6:]+'/'+p_date[4:6]+'/'+p_date[0:4]
    p_source = paste.p_source
    p_encoding = paste._get_p_encoding()
    p_language = paste._get_p_language()
    p_size = paste.p_size
    p_mime = paste.p_mime
    p_lineinfo = paste.get_lines_info()
    p_content = paste.get_p_content()
    p_duplicate_str_full_list = paste._get_p_duplicate()

    p_duplicate_full_list = []
    p_duplicate_list = []
    p_simil_list = []
    p_date_list = []
    p_hashtype_list = []


    for dup_list in p_duplicate_str_full_list:
        dup_list = dup_list[1:-1].replace('\'', '').replace(' ', '').split(',')
        if dup_list[0] == "tlsh":
            dup_list[2] = 100 - int(dup_list[2])
        else:
            dup_list[2] = int(dup_list[2])
        p_duplicate_full_list.append(dup_list)

    #p_duplicate_full_list.sort(lambda x,y: cmp(x[2], y[2]), reverse=True)

    # Combine multiple duplicate paste name and format for display
    new_dup_list = []
    dup_list_removed = []
    for dup_list_index in range(0, len(p_duplicate_full_list)):
        if dup_list_index in dup_list_removed:
            continue
        indices = [i for i, x in enumerate(p_duplicate_full_list) if x[1] == p_duplicate_full_list[dup_list_index][1]]
        hash_types = []
        comp_vals = []
        for i in indices:
            hash_types.append(p_duplicate_full_list[i][0])
            comp_vals.append(p_duplicate_full_list[i][2])
            dup_list_removed.append(i)

        #hash_types = str(hash_types).replace("[","").replace("]","") if len(hash_types)==1 else str(hash_types)
        #comp_vals = str(comp_vals).replace("[","").replace("]","") if len(comp_vals)==1 else str(comp_vals)

        if len(p_duplicate_full_list[dup_list_index]) > 3:
            try:
                date_paste = str(int(p_duplicate_full_list[dup_list_index][3]))
                date_paste = date_paste[0:4]+"-"+date_paste[4:6]+"-"+date_paste[6:8]
            except ValueError:
                date_paste = str(p_duplicate_full_list[dup_list_index][3])
        else:
            date_paste = "No date available"
        new_dup_list.append([hash_types, p_duplicate_full_list[dup_list_index][1], comp_vals, date_paste])

    # Create the list to pass to the webpage
    for dup_list in new_dup_list:
        hash_type, path, simil_percent, date_paste = dup_list
        p_duplicate_list.append(path)
        p_simil_list.append(simil_percent)
        p_hashtype_list.append(hash_type)
        p_date_list.append(date_paste)

    if content_range != 0:
       p_content = p_content[0:content_range]

    #active taxonomies
    active_taxonomies = r_serv_tags.smembers('active_taxonomies')

    l_tags = r_serv_metadata.smembers('tag:'+requested_path)

    #active galaxies
    active_galaxies = r_serv_tags.smembers('active_galaxies')

    list_tags = []

    for tag in l_tags:
        if(tag[9:28] == 'automatic-detection'):
            automatic = True
        else:
            automatic = False

        if r_serv_statistics.sismember('tp:'+tag, requested_path):
            tag_status_tp = True
        else:
            tag_status_tp = False
        if r_serv_statistics.sismember('fp:'+tag, requested_path):
            tag_status_fp = True
        else:
            tag_status_fp = False

        list_tags.append( (tag, automatic, tag_status_tp, tag_status_fp) )

    l_64 = []
    # load hash files
    if r_serv_metadata.scard('hash_paste:'+requested_path) > 0:
        set_b64 = r_serv_metadata.smembers('hash_paste:'+requested_path)
        for hash in set_b64:
            nb_in_file = int(r_serv_metadata.zscore('nb_seen_hash:'+hash, requested_path))
            estimated_type = r_serv_metadata.hget('metadata_hash:'+hash, 'estimated_type')
            file_type = estimated_type.split('/')[0]
            # set file icon
            if file_type == 'application':
                file_icon = 'fa-file-o '
            elif file_type == 'audio':
                file_icon = 'fa-file-video-o '
            elif file_type == 'image':
                file_icon = 'fa-file-image-o'
            elif file_type == 'text':
                file_icon = 'fa-file-text-o'
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
        crawler_metadata['paste_father'] = r_serv_metadata.hget('paste_metadata:'+requested_path, 'father')
        crawler_metadata['real_link'] = r_serv_metadata.hget('paste_metadata:'+requested_path,'real_link')
        crawler_metadata['external_links'] =r_serv_metadata.scard('paste_onion_external_links:'+requested_path)
        crawler_metadata['screenshot'] = paste.get_p_rel_path()
    else:
        crawler_metadata['get_metadata'] = False

    if Flask_config.pymisp is False:
        misp = False
    else:
        misp = True

    if Flask_config.HiveApi is False:
        hive = False
    else:
        hive = True

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

    return render_template("show_saved_paste.html", date=p_date, bootstrap_label=bootstrap_label, active_taxonomies=active_taxonomies, active_galaxies=active_galaxies, list_tags=list_tags, source=p_source, encoding=p_encoding, language=p_language, size=p_size, mime=p_mime, lineinfo=p_lineinfo, content=p_content, initsize=len(p_content), duplicate_list = p_duplicate_list, simil_list = p_simil_list, hashtype_list = p_hashtype_list, date_list=p_date_list,
                            crawler_metadata=crawler_metadata,
                            l_64=l_64, vt_enabled=vt_enabled, misp=misp, hive=hive, misp_eventid=misp_eventid, misp_url=misp_url, hive_caseid=hive_caseid, hive_url=hive_url)

# ============ ROUTES ============

@showsavedpastes.route("/showsavedpaste/") #completely shows the paste in a new tab
def showsavedpaste():
    requested_path = request.args.get('paste', '')
    print(requested_path)
    return showpaste(0, requested_path)

@showsavedpastes.route("/showsavedrawpaste/") #shows raw
def showsavedrawpaste():
    requested_path = request.args.get('paste', '')
    paste = Paste.Paste(requested_path)
    content = paste.get_p_content()
    return Response(content, mimetype='text/plain')

@showsavedpastes.route("/showpreviewpaste/")
def showpreviewpaste():
    num = request.args.get('num', '')
    requested_path = request.args.get('paste', '')
    return "|num|"+num+"|num|"+showpaste(max_preview_modal, requested_path)


@showsavedpastes.route("/getmoredata/")
def getmoredata():
    requested_path = request.args.get('paste', '')
    paste = Paste.Paste(requested_path)
    p_content = paste.get_p_content()
    to_return = p_content[max_preview_modal-1:]
    return to_return

@showsavedpastes.route("/showDiff/")
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
def screenshot(filename):
    return send_from_directory(SCREENSHOT_FOLDER, filename+'.png', as_attachment=True)

@showsavedpastes.route('/send_file_to_vt/', methods=['POST'])
def send_file_to_vt():
    b64_path = request.form['b64_path']
    paste = request.form['paste']
    hash = request.form['hash']

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
app.register_blueprint(showsavedpastes)
