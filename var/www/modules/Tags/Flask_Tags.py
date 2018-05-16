#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
from flask import Flask, render_template, jsonify, request, Blueprint

import json

import Paste

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_tags = Flask_config.r_serv_tags
r_serv_metadata = Flask_config.r_serv_metadata
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal

Tags = Blueprint('Tags', __name__, template_folder='templates')

# ============ FUNCTIONS ============
def one():
    return 1

# ============= ROUTES ==============

@Tags.route("/Tags/", methods=['GET'])
def Tags_page():
    return render_template("Tags.html")

@Tags.route("/Tags/get_all_tags")
def get_all_tags():

    all_tags = r_serv_tags.smembers('list_tags')

    list_tags = []
    id = 0
    for tag in all_tags:
        list_tags.append( tag )
        id += 1

    return jsonify(list_tags)

@Tags.route("/Tags/get_tagged_paste")
def get_tagged_paste():

    tags = request.args.get('ltags')[1:-1]
    tags = tags.replace('\\','')

    list_tags = tags.split(',')
    tmp_list_tags = []

    # remove " char
    for tag in list_tags:
        tmp_list_tags.append(tag[1:-1])
    list_tags = tmp_list_tags

    # TODO verify input

    if(type(list_tags) is list):
        # no tag
        if list_tags is False:
            print('empty')
        # 1 tag
        elif len(list_tags) < 2:
            tagged_pastes = r_serv_tags.smembers(list_tags[0])

        # 2 tags or more
        else:
            tagged_pastes = r_serv_tags.sinter(list_tags[0], *list_tags[1:])

    else :
        return 'INCORRECT INPUT'

    #currentSelectYear = int(datetime.now().year)
    currentSelectYear = 2018

    bootstrap_label = []
    bootstrap_label.append('primary')
    bootstrap_label.append('success')
    bootstrap_label.append('danger')
    bootstrap_label.append('warning')
    bootstrap_label.append('info')
    bootstrap_label.append('dark')

    all_content = []
    paste_date = []
    paste_linenum = []
    all_path = []
    allPastes = list(tagged_pastes)
    paste_tags = []

    for path in allPastes[0:50]: ######################moduleName
        all_path.append(path)
        paste = Paste.Paste(path)
        content = paste.get_p_content()
        content_range = max_preview_char if len(content)>max_preview_char else len(content)-1
        all_content.append(content[0:content_range].replace("\"", "\'").replace("\r", " ").replace("\n", " "))
        curr_date = str(paste._get_p_date())
        curr_date = curr_date[0:4]+'/'+curr_date[4:6]+'/'+curr_date[6:]
        paste_date.append(curr_date)
        paste_linenum.append(paste.get_lines_info()[0])
        p_tags = r_serv_metadata.smembers('tag:'+path)
        l_tags = []
        for tag in p_tags:
            tag = tag.split('=')
            if len(tag) > 1:
                if tag[1] != '':
                    tag = tag[1][1:-1]
                # no value
                else:
                    tag = tag[0][1:-1]
            # use for custom tags
            else:
                tag = tag[0]

            l_tags.append(tag)

        paste_tags.append(l_tags)

    if len(allPastes) > 10:
        finished = False
    else:
        finished = True

    return render_template("tagged.html",
            year=currentSelectYear,
            all_path=all_path,
            paste_tags=paste_tags,
            bootstrap_label=bootstrap_label,
            content=all_content,
            paste_date=paste_date,
            paste_linenum=paste_linenum,
            char_to_display=max_preview_modal,
            finished=finished)

    return 'OK'

@Tags.route("/Tags/res")
def get_tagged_paste_res():

    return render_template("res.html")

# ========= REGISTRATION =========
app.register_blueprint(Tags)
