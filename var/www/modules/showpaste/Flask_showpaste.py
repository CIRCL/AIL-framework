#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import json
import flask
from flask import Flask, render_template, jsonify, request, Blueprint, make_response
import difflib

import Paste

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_pasteName = Flask_config.r_serv_pasteName
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal
DiffMaxLineLength = Flask_config.DiffMaxLineLength

showsavedpastes = Blueprint('showsavedpastes', __name__, template_folder='templates')

# ============ FUNCTIONS ============

def showpaste(content_range):
    requested_path = request.args.get('paste', '')
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
    p_duplicate_full_list = json.loads(paste._get_p_duplicate())
    p_duplicate_list = []
    p_simil_list = []
    p_date_list = []
    p_hashtype_list = []


    for dup_list in p_duplicate_full_list:
        if dup_list[0] == "tlsh":
            dup_list[2] = 100 - int(dup_list[2])
        else:
            print('dup_list')
            print(dup_list)
            dup_list[2] = int(dup_list[2])

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

        hash_types = str(hash_types).replace("[","").replace("]","") if len(hash_types)==1 else str(hash_types)
        comp_vals = str(comp_vals).replace("[","").replace("]","") if len(comp_vals)==1 else str(comp_vals)

        if len(p_duplicate_full_list[dup_list_index]) > 3:
            try:
                date_paste = str(int(p_duplicate_full_list[dup_list_index][3]))
                date_paste = date_paste[0:4]+"-"+date_paste[4:6]+"-"+date_paste[6:8]
            except ValueError:
                date_paste = str(p_duplicate_full_list[dup_list_index][3])
        else:
            date_paste = "No date available"
        new_dup_list.append([hash_types.replace("'", ""), p_duplicate_full_list[dup_list_index][1], comp_vals, date_paste])

    # Create the list to pass to the webpage
    for dup_list in new_dup_list:
        hash_type, path, simil_percent, date_paste = dup_list
        p_duplicate_list.append(path)
        p_simil_list.append(simil_percent)
        p_hashtype_list.append(hash_type)
        p_date_list.append(date_paste)

    if content_range != 0:
       p_content = p_content[0:content_range]

    return render_template("show_saved_paste.html", date=p_date, source=p_source, encoding=p_encoding, language=p_language, size=p_size, mime=p_mime, lineinfo=p_lineinfo, content=p_content, initsize=len(p_content), duplicate_list = p_duplicate_list, simil_list = p_simil_list, hashtype_list = p_hashtype_list, date_list=p_date_list)

# ============ ROUTES ============

@showsavedpastes.route("/showsavedpaste/") #completely shows the paste in a new tab
def showsavedpaste():
    return showpaste(0)


@showsavedpastes.route("/showpreviewpaste/")
def showpreviewpaste():
    num = request.args.get('num', '')
    return "|num|"+num+"|num|"+showpaste(max_preview_modal)


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

# ========= REGISTRATION =========
app.register_blueprint(showsavedpastes)
