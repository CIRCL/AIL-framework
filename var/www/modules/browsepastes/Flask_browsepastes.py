#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import json
import flask
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Blueprint

import Paste

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal
r_serv_metadata = Flask_config.r_serv_metadata
bootstrap_label = Flask_config.bootstrap_label

#init all lvlDB servers
curYear = datetime.now().year
int_year = int(curYear)
r_serv_db = {}
# port generated automatically depending on available levelDB date
yearList = []

for x in range(0, (int_year - 2018) + 1):

    intYear = int_year - x

    yearList.append([str(intYear), intYear, int(curYear) == intYear])
    r_serv_db[intYear] = redis.StrictRedis(
        host=cfg.get("ARDB_DB", "host"),
        port=cfg.getint("ARDB_DB", "port"),
        db=intYear,
        decode_responses=True)

yearList.sort(reverse=True)

browsepastes = Blueprint('browsepastes', __name__, template_folder='templates')

# ============ FUNCTIONS ============

def getPastebyType(server, module_name):
    all_path = []
    for path in server.smembers('WARNING_'+module_name):
        all_path.append(path)

    return all_path


def event_stream_getImportantPasteByModule(module_name, year):
    index = 0
    all_pastes_list = getPastebyType(r_serv_db[year], module_name)
    paste_tags = []

    for path in all_pastes_list:
        index += 1
        paste = Paste.Paste(path)
        content = paste.get_p_content()
        content_range = max_preview_char if len(content)>max_preview_char else len(content)-1
        curr_date = str(paste._get_p_date())
        curr_date = curr_date[0:4]+'/'+curr_date[4:6]+'/'+curr_date[6:]
        p_tags = r_serv_metadata.smembers('tag:'+path)
        l_tags = []
        for tag in p_tags:
            complete_tag = tag.replace('"', '&quot;')
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

            l_tags.append( (tag, complete_tag) )

        data = {}
        data["module"] = module_name
        data["index"] = index
        data["path"] = path
        data["content"] = content[0:content_range]
        data["linenum"] = paste.get_lines_info()[0]
        data["date"] = curr_date
        data["l_tags"] = l_tags
        data["bootstrap_label"] = bootstrap_label
        data["char_to_display"] = max_preview_modal
        data["finished"] = True if index == len(all_pastes_list) else False
        yield 'retry: 100000\ndata: %s\n\n' % json.dumps(data) #retry to avoid reconnection of the browser

# ============ ROUTES ============

@browsepastes.route("/browseImportantPaste/", methods=['GET'])
def browseImportantPaste():
    module_name = request.args.get('moduleName')
    return render_template("browse_important_paste.html", year_list=yearList, selected_year=curYear)


@browsepastes.route("/importantPasteByModule/", methods=['GET'])
def importantPasteByModule():
    module_name = request.args.get('moduleName')

    # # TODO: VERIFY YEAR VALIDITY
    try:
        currentSelectYear = int(request.args.get('year'))
    except:
        print('Invalid year input')
        currentSelectYear = int(datetime.now().year)

    all_content = []
    paste_date = []
    paste_linenum = []
    all_path = []
    paste_tags = []
    allPastes = getPastebyType(r_serv_db[currentSelectYear], module_name)

    for path in allPastes[0:10]:
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
            complete_tag = tag
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

            l_tags.append( (tag, complete_tag) )

        paste_tags.append(l_tags)

    if len(allPastes) > 10:
        finished = False
    else:
        finished = True

    return render_template("important_paste_by_module.html",
            moduleName=module_name,
            year=currentSelectYear,
            all_path=all_path,
            content=all_content,
            paste_date=paste_date,
            paste_linenum=paste_linenum,
            char_to_display=max_preview_modal,
            paste_tags=paste_tags,
            bootstrap_label=bootstrap_label,
            finished=finished)

@browsepastes.route("/_getImportantPasteByModule", methods=['GET'])
def getImportantPasteByModule():
    module_name = request.args.get('moduleName')
    currentSelectYear = int(request.args.get('year'))
    return flask.Response(event_stream_getImportantPasteByModule(module_name, currentSelectYear), mimetype="text/event-stream")


# ========= REGISTRATION =========
app.register_blueprint(browsepastes)
