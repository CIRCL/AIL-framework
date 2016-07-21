#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis
import ConfigParser
import json
import datetime
from flask import Flask, render_template, jsonify, request
import flask
import os
import sys
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Paste
from Date import Date

# CONFIG #
configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
if not os.path.exists(configfile):
    raise Exception('Unable to find the configuration file. \
                    Did you set environment variables? \
                    Or activate the virtualenv.')

cfg = ConfigParser.ConfigParser()
cfg.read(configfile)

max_preview_char = int(cfg.get("Flask", "max_preview_char")) # Maximum number of character to display in the tooltip
max_preview_modal = int(cfg.get("Flask", "max_preview_modal")) # Maximum number of character to display in the modal

# REDIS #
r_serv = redis.StrictRedis(
    host=cfg.get("Redis_Queues", "host"),
    port=cfg.getint("Redis_Queues", "port"),
    db=cfg.getint("Redis_Queues", "db"))

r_serv_log = redis.StrictRedis(
    host=cfg.get("Redis_Log", "host"),
    port=cfg.getint("Redis_Log", "port"),
    db=cfg.getint("Redis_Log", "db"))

r_serv_charts = redis.StrictRedis(
    host=cfg.get("Redis_Level_DB_Trending", "host"),
    port=cfg.getint("Redis_Level_DB_Trending", "port"),
    db=cfg.getint("Redis_Level_DB_Trending", "db"))


app = Flask(__name__, static_url_path='/static/')


def event_stream():
    pubsub = r_serv_log.pubsub()
    pubsub.psubscribe("Script" + '.*')
    for msg in pubsub.listen():
        level = msg['channel'].split('.')[1]
        if msg['type'] == 'pmessage' and level != "DEBUG":
            yield 'data: %s\n\n' % json.dumps(msg)


def get_queues(r):
    # We may want to put the llen in a pipeline to do only one query.
    return [(queue, int(card)) for queue, card in
            r.hgetall("queues").iteritems()]


def list_len(s):
    return len(s)
app.jinja_env.filters['list_len'] = list_len

def parseStringToList(the_string):
    strList = ""
    elemList = []
    for c in the_string:
        if c != ']':
            if c != '[' and c !=' ' and c != '"':
                strList += c
        else:
            the_list = strList.split(',')
            if len(the_list) == 2:
               elemList.append(the_list)
            elif len(the_list) > 1:
               elemList.append(the_list[1:])
            strList = ""
    return elemList

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
    p_content = paste.get_p_content().decode('utf-8', 'ignore')
    p_duplicate_full_list = parseStringToList(paste._get_p_duplicate())
    p_duplicate_list = []
    p_simil_list = []

    for dup_list in p_duplicate_full_list:
        path, simil_percent = dup_list
        p_duplicate_list.append(path)
        p_simil_list.append(simil_percent)

    if content_range != 0:
       p_content = p_content[0:content_range] 

    return render_template("show_saved_paste.html", date=p_date, source=p_source, encoding=p_encoding, language=p_language, size=p_size, mime=p_mime, lineinfo=p_lineinfo, content=p_content, initsize=len(p_content), duplicate_list = p_duplicate_list, simil_list = p_simil_list)

def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return date_list





# ============ ROUTES ============

@app.route("/_logs")
def logs():
    return flask.Response(event_stream(), mimetype="text/event-stream")


@app.route("/_stuff", methods=['GET'])
def stuff():
    return jsonify(row1=get_queues(r_serv))

@app.route("/_progressionCharts", methods=['GET'])
def progressionCharts():
    #To be used later
    attribute_name = request.args.get('attributeName')
    trending_name = request.args.get('trendingName')
    bar_requested = True if request.args.get('bar') == "true" else False
    
    if (bar_requested):
        num_day = int(request.args.get('days'))
        bar_values = []

	date_range = get_date_range(num_day) 
        # Retreive all data from the last num_day
        for date in date_range:
            curr_value = r_serv_charts.hget(attribute_name, date)
            bar_values.append([date[0:4]+'/'+date[4:6]+'/'+date[6:8], int(curr_value if curr_value is not None else 0)])
        return jsonify(bar_values)
 
    else:
        redis_progression_name = 'top_progression_'+trending_name
        redis_progression_name_set = 'top_progression_'+trending_name+'_set'

        member_set = []
        for keyw in r_serv_charts.smembers(redis_progression_name_set):
            keyw_value = r_serv_charts.hget(redis_progression_name, keyw)
            keyw_value = keyw_value if keyw_value is not None else 0
            member_set.append((keyw, int(keyw_value)))
        member_set.sort(key=lambda tup: tup[1], reverse=True)
        if len(member_set) == 0:
            member_set.append(("No relevant data", int(100)))
        return jsonify(member_set)
    

@app.route("/search", methods=['POST'])
def search():
    query = request.form['query']
    q = []
    q.append(query)
    r = [] #complete path
    c = [] #preview of the paste content
    paste_date = []
    paste_size = []
    # Search
    from whoosh import index
    from whoosh.fields import Schema, TEXT, ID
    schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)

    indexpath = os.path.join(os.environ['AIL_HOME'], cfg.get("Indexer", "path"))
    ix = index.open_dir(indexpath)
    from whoosh.qparser import QueryParser
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse(" ".join(q))
        results = searcher.search(query, limit=None)
        for x in results:
            r.append(x.items()[0][1])
            paste = Paste.Paste(x.items()[0][1])
            content = paste.get_p_content().decode('utf8', 'ignore')
            content_range = max_preview_char if len(content)>max_preview_char else len(content)-1
            c.append(content[0:content_range]) 
            curr_date = str(paste._get_p_date())
            curr_date = curr_date[0:4]+'/'+curr_date[4:6]+'/'+curr_date[6:]
            paste_date.append(curr_date) 
            paste_size.append(paste._get_p_size()) 
    return render_template("search.html", r=r, c=c, query=request.form['query'], paste_date=paste_date, paste_size=paste_size, char_to_display=max_preview_modal)


@app.route("/")
def index():
    default_minute = cfg.get("Flask", "minute_processed_paste")
    return render_template("index.html", default_minute = default_minute)


@app.route("/monitoring/")
def monitoring():
    for queue in r_serv.smembers("queues"):
        return render_template("Queue_live_Monitoring.html", last_value=queue)


@app.route("/wordstrending/")
def wordstrending():
    default_display = cfg.get("Flask", "default_display")
    return render_template("Wordstrending.html", default_display = default_display)


@app.route("/protocolstrending/")
def protocolstrending():
    default_display = cfg.get("Flask", "default_display")
    return render_template("Protocolstrending.html", default_display = default_display)


@app.route("/trending/")
def trending():
    default_display = cfg.get("Flask", "default_display")
    return render_template("Trending.html", default_display = default_display)


@app.route("/showsavedpaste/") #completely shows the paste in a new tab
def showsavedpaste():
    return showpaste(0)


@app.route("/showpreviewpaste/")
def showpreviewpaste():
    return showpaste(max_preview_modal)


@app.route("/getmoredata/")
def getmoredata():
    requested_path = request.args.get('paste', '')
    paste = Paste.Paste(requested_path)
    p_content = paste.get_p_content().decode('utf-8', 'ignore')
    to_return = p_content[max_preview_modal-1:]
    return to_return 


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7000, threaded=True)
