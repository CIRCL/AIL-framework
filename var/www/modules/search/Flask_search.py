#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import json
import os
import datetime
import flask
from flask import Flask, render_template, jsonify, request, Blueprint

from Role_Manager import login_admin, login_analyst
from flask_login import login_required

import Paste
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

import time

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
config_loader = Flask_config.config_loader
baseUrl = Flask_config.baseUrl
r_serv_metadata = Flask_config.r_serv_metadata
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal
bootstrap_label = Flask_config.bootstrap_label
PASTES_FOLDER = Flask_config.PASTES_FOLDER

baseindexpath = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Indexer", "path"))
indexRegister_path = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Indexer", "register"))

searches = Blueprint('searches', __name__, template_folder='templates')

# ============ FUNCTIONS ============
def get_current_index():
    with open(indexRegister_path, "r") as f:
        allIndex = f.read()
        allIndex = allIndex.split() # format [time1\ntime2]
        allIndex.sort()
        try:
            indexname = allIndex[-1].strip('\n\r')
        except IndexError as e:
            indexname = "no-index"
        indexpath = os.path.join(baseindexpath, indexname)
    return indexpath

def get_index_list(selected_index=""):
    temp = []
    index_list = []
    for dirs in os.listdir(baseindexpath):
        if os.path.isdir(os.path.join(baseindexpath, dirs)):
            value = dirs
            name = to_iso_date(dirs) + " - " + \
                    str(get_dir_size(dirs) / (1000*1000)) + " Mb " #+ \
                    #"(" + str(get_item_count(dirs))''' + " Items" + ")"
            flag = dirs==selected_index.split('/')[-1]
            if dirs == "old_index":
                temp = [value, name, flag]
            else:
                index_list.append([value, name, flag])

    index_list.sort(reverse=True, key=lambda x: x[0])
    if len(temp) != 0:
        index_list.append(temp)

    return index_list

def get_dir_size(directory):
    cur_sum = 0
    for directory, subdirs, files in os.walk(os.path.join(baseindexpath,directory)):
        try:
            cur_sum += sum(os.path.getsize(os.path.join(directory, name)) for name in files)
        except OSError as e: #File disappeared
            pass
    return cur_sum

def get_item_count(dirs):
    ix = index.open_dir(os.path.join(baseindexpath, dirs))
    return ix.doc_count_all()

def to_iso_date(timestamp):
    if timestamp == "old_index":
        return "old_index"
    return str(datetime.datetime.fromtimestamp(int(timestamp))).split()[0]


# ============ ROUTES ============

@searches.route("/search", methods=['POST'])
@login_required
@login_analyst
def search():
    query = request.form['query']
    q = []
    q.append(query)
    r = [] #complete path
    c = [] #preview of the paste content
    paste_date = []
    paste_size = []
    paste_tags = []
    index_name = request.form['index_name']
    num_elem_to_get = 50

    # select correct index
    if index_name is None or index_name == "0":
        selected_index = get_current_index()
    else:
        selected_index = os.path.join(baseindexpath, index_name)

    ''' temporary disabled
    # # TODO: search by filename/item id
    '''

    # Search full line
    schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)

    ix = index.open_dir(selected_index)
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse("".join(q))
        results = searcher.search_page(query, 1, pagelen=num_elem_to_get)
        for x in results:
            r.append(x.items()[0][1].replace(PASTES_FOLDER, '', 1))
            path = x.items()[0][1].replace(PASTES_FOLDER, '', 1)
            paste = Paste.Paste(path)
            content = paste.get_p_content()
            content_range = max_preview_char if len(content)>max_preview_char else len(content)-1
            c.append(content[0:content_range])
            curr_date = str(paste._get_p_date())
            curr_date = curr_date[0:4]+'/'+curr_date[4:6]+'/'+curr_date[6:]
            paste_date.append(curr_date)
            paste_size.append(paste._get_p_size())
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
        results = searcher.search(query)
        num_res = len(results)

    index_list = get_index_list()

    index_min = 1
    index_max = len(index_list)

    return render_template("search.html", r=r, c=c,
            query=request.form['query'], paste_date=paste_date,
            paste_size=paste_size, char_to_display=max_preview_modal,
            num_res=num_res, index_min=index_min, index_max=index_max,
            bootstrap_label=bootstrap_label,
            paste_tags=paste_tags,
            index_list=index_list
           )


@searches.route("/get_more_search_result", methods=['POST'])
@login_required
@login_analyst
def get_more_search_result():
    query = request.form['query']
    q = []
    q.append(query)
    page_offset = int(request.form['page_offset'])
    index_name = request.form['index_name']
    num_elem_to_get = 50

    # select correct index
    if index_name is None or index_name == "0":
        selected_index = get_current_index()
    else:
        selected_index = os.path.join(baseindexpath, index_name)

    path_array = []
    preview_array = []
    date_array = []
    size_array = []
    list_tags = []

    schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)

    ix = index.open_dir(selected_index)
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse(" ".join(q))
        results = searcher.search_page(query, page_offset, num_elem_to_get)
        for x in results:
            path = x.items()[0][1]
            path = path.replace(PASTES_FOLDER, '', 1)
            path_array.append(path)
            paste = Paste.Paste(path)
            content = paste.get_p_content()
            content_range = max_preview_char if len(content)>max_preview_char else len(content)-1
            preview_array.append(content[0:content_range])
            curr_date = str(paste._get_p_date())
            curr_date = curr_date[0:4]+'/'+curr_date[4:6]+'/'+curr_date[6:]
            date_array.append(curr_date)
            size_array.append(paste._get_p_size())
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
            list_tags.append(l_tags)

        to_return = {}
        to_return["path_array"] = path_array
        to_return["preview_array"] = preview_array
        to_return["date_array"] = date_array
        to_return["size_array"] = size_array
        to_return["list_tags"] = list_tags
        to_return["bootstrap_label"] = bootstrap_label
        if len(path_array) < num_elem_to_get: #pagelength
            to_return["moreData"] = False
        else:
            to_return["moreData"] = True

    return jsonify(to_return)


# ========= REGISTRATION =========
app.register_blueprint(searches, url_prefix=baseUrl)
