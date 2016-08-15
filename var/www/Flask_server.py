#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis
import ConfigParser
import json
import datetime
import calendar
from flask import Flask, render_template, jsonify, request
import flask
import os
import sys
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Paste
from Date import Date

# CONFIG #
tlsh_to_percent = 1000.0 #Use to display the estimated percentage instead of a raw value

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

r_serv_db = redis.StrictRedis(
    host=cfg.get("Redis_Level_DB", "host"),
    port=cfg.getint("Redis_Level_DB", "port"),
    db=cfg.getint("Redis_Level_DB", "db"))

r_serv_sentiment = redis.StrictRedis(
        host=cfg.get("Redis_Level_DB_Sentiment", "host"),
        port=cfg.getint("Redis_Level_DB_Sentiment", "port"),
        db=cfg.getint("Redis_Level_DB_Sentiment", "db"))

 
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
            if len(the_list) == 3:
               elemList = elemList + the_list
            elif len(the_list) == 2:
               elemList.append(the_list)
            elif len(the_list) > 1:
               elemList.append(the_list[1:])
            strList = ""
    return elemList

def parseStringToList2(the_string):
    if the_string == []:
        return []
    else:
        res = []
        tab_str = the_string.split('], [')
        tab_str[0] = tab_str[0][1:]+']'
        tab_str[len(tab_str)-1] = '['+tab_str[len(tab_str)-1][:-1]
        res.append(parseStringToList(tab_str[0]))
        for i in range(1, len(tab_str)-2):
            tab_str[i] = '['+tab_str[i]+']'
            res.append(parseStringToList(tab_str[i]))
        if len(tab_str) > 1:
            res.append(parseStringToList(tab_str[len(tab_str)-1]))
        return res


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
    p_duplicate_full_list = parseStringToList2(paste._get_p_duplicate())
    p_duplicate_list = []
    p_simil_list = []
    p_hashtype_list = []


    for dup_list in p_duplicate_full_list:
        if dup_list[0] == "tlsh":
            dup_list[2] = int(((tlsh_to_percent - float(dup_list[2])) / tlsh_to_percent)*100)
        else:
            dup_list[2] = int(dup_list[2])
            
    p_duplicate_full_list.sort(lambda x,y: cmp(x[2], y[2]), reverse=True)

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
        new_dup_list.append([hash_types.replace("'", ""), p_duplicate_full_list[dup_list_index][1], comp_vals])

    # Create the list to pass to the webpage
    for dup_list in new_dup_list:
        hash_type, path, simil_percent = dup_list
        p_duplicate_list.append(path)
        p_simil_list.append(simil_percent)
        p_hashtype_list.append(hash_type)

    if content_range != 0:
       p_content = p_content[0:content_range] 

    return render_template("show_saved_paste.html", date=p_date, source=p_source, encoding=p_encoding, language=p_language, size=p_size, mime=p_mime, lineinfo=p_lineinfo, content=p_content, initsize=len(p_content), duplicate_list = p_duplicate_list, simil_list = p_simil_list, hashtype_list = p_hashtype_list)

def getPastebyType(server, module_name):
    all_path = []
    for path in server.smembers('WARNING_'+module_name):
        all_path.append(path)
    return all_path


def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return date_list

# Iterate over elements in the module provided and return the today data or the last data
# return format: [('passed_days', num_of_passed_days), ('elem_name1', elem_value1), ('elem_name2', elem_value2)]]
def get_top_relevant_data(server, module_name):
    redis_progression_name_set = 'top_'+ module_name +'_set'
    days = 0 
    for date in get_date_range(15):
        member_set = []
        for keyw in server.smembers(redis_progression_name_set):
            redis_progression_name = module_name+'-'+keyw
            keyw_value = server.hget(date ,redis_progression_name)
            keyw_value = keyw_value if keyw_value is not None else 0
            member_set.append((keyw, int(keyw_value)))
        member_set.sort(key=lambda tup: tup[1], reverse=True)
        if member_set[0][1] == 0: #No data for this date
            days += 1
            continue
        else:
            member_set.insert(0, ("passed_days", days))
            return member_set

# ========= CACHE CONTROL ========
@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

# ============ ROUTES ============

@app.route("/_logs")
def logs():
    return flask.Response(event_stream(), mimetype="text/event-stream")


@app.route("/_stuff", methods=['GET'])
def stuff():
    return jsonify(row1=get_queues(r_serv))

@app.route("/_progressionCharts", methods=['GET'])
def progressionCharts():
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
        bar_values.insert(0, attribute_name)
        return jsonify(bar_values)
 
    else:
        redis_progression_name = 'top_progression_'+trending_name
        redis_progression_name_set = 'top_progression_'+trending_name+'_set'

        # Iterate over element in top_x_set and retreive their value
        member_set = []
        for keyw in r_serv_charts.smembers(redis_progression_name_set):
            keyw_value = r_serv_charts.hget(redis_progression_name, keyw)
            keyw_value = keyw_value if keyw_value is not None else 0
            member_set.append((keyw, int(keyw_value)))
        member_set.sort(key=lambda tup: tup[1], reverse=True)
        if len(member_set) == 0:
            member_set.append(("No relevant data", int(100)))
        return jsonify(member_set)
    
@app.route("/_moduleCharts", methods=['GET'])
def modulesCharts():
    keyword_name = request.args.get('keywordName')
    module_name = request.args.get('moduleName')
    bar_requested = True if request.args.get('bar') == "true" else False
    
    if (bar_requested):
        num_day = int(request.args.get('days'))
        bar_values = []

	date_range = get_date_range(num_day) 
        # Retreive all data from the last num_day
        for date in date_range:
            curr_value = r_serv_charts.hget(date, module_name+'-'+keyword_name)
            bar_values.append([date[0:4]+'/'+date[4:6]+'/'+date[6:8], int(curr_value if curr_value is not None else 0)])
        bar_values.insert(0, keyword_name)
        return jsonify(bar_values)
 
    else:
        member_set = get_top_relevant_data(r_serv_charts, module_name)
        if len(member_set) == 0:
            member_set.append(("No relevant data", int(100)))
        return jsonify(member_set)


@app.route("/_providersChart", methods=['GET'])
def providersChart():
    keyword_name = request.args.get('keywordName')
    module_name = request.args.get('moduleName')
    bar_requested = True if request.args.get('bar') == "true" else False
    
    if (bar_requested):
        num_day = int(request.args.get('days'))
        bar_values = []

	date_range = get_date_range(num_day) 
        # Retreive all data from the last num_day
        for date in date_range:
            curr_value_size = r_serv_charts.hget(keyword_name+'_'+'size', date)
            curr_value_num = r_serv_charts.hget(keyword_name+'_'+'num', date)
            if module_name == "size":
                curr_value_num = curr_value_num if curr_value_num is not None else 0
                curr_value_num = curr_value_num if int(curr_value_num) != 0 else 10000000000
                curr_value = float(curr_value_size if curr_value_size is not None else 0.0) / float(curr_value_num)
            else:
                curr_value = float(curr_value_num if curr_value_num is not None else 0.0)

            bar_values.append([date[0:4]+'/'+date[4:6]+'/'+date[6:8], curr_value])
        bar_values.insert(0, keyword_name)
        return jsonify(bar_values)
 
    else:
        redis_provider_name_set = 'top_size_set' if module_name == "size" else 'providers_set'

        # Iterate over element in top_x_set and retreive their value
        member_set = []
        for keyw in r_serv_charts.smembers(redis_provider_name_set):
            redis_provider_name_size = keyw+'_'+'size'
            redis_provider_name_num = keyw+'_'+'num'
            keyw_value_size = r_serv_charts.hget(redis_provider_name_size, get_date_range(0)[0])
            keyw_value_size = keyw_value_size if keyw_value_size is not None else 0.0
            keyw_value_num = r_serv_charts.hget(redis_provider_name_num, get_date_range(0)[0])
            
            if keyw_value_num is not None:
                keyw_value_num = int(keyw_value_num)
            else:
                if module_name == "size":
                    keyw_value_num = 10000000000
                else:
                    keyw_value_num = 0
            if module_name == "size":
                member_set.append((keyw, float(keyw_value_size)/float(keyw_value_num)))
            else:
                member_set.append((keyw, float(keyw_value_num)))

        member_set.sort(key=lambda tup: tup[1], reverse=True)
        if len(member_set) == 0:
            member_set.append(("No relevant data", float(100)))
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

@app.route("/browseImportantPaste/", methods=['GET'])
def browseImportantPaste():
    module_name = request.args.get('moduleName')
    return render_template("browse_important_paste.html")


@app.route("/importantPasteByModule/", methods=['GET'])
def importantPasteByModule():
    module_name = request.args.get('moduleName')

    all_content = []
    paste_date = []
    paste_linenum = []
    all_path = []

    for path in getPastebyType(r_serv_db, module_name):
        all_path.append(path)
        paste = Paste.Paste(path)
        content = paste.get_p_content().decode('utf8', 'ignore')
        content_range = max_preview_char if len(content)>max_preview_char else len(content)-1
        all_content.append(content[0:content_range]) 
        curr_date = str(paste._get_p_date())
        curr_date = curr_date[0:4]+'/'+curr_date[4:6]+'/'+curr_date[6:]
        paste_date.append(curr_date) 
        paste_linenum.append(paste.get_lines_info()[0]) 

    return render_template("important_paste_by_module.html", all_path=all_path, content=all_content, paste_date=paste_date, paste_linenum=paste_linenum, char_to_display=max_preview_modal)

@app.route("/moduletrending/")
def moduletrending():
    return render_template("Moduletrending.html")

@app.route("/sentiment_analysis_trending/")
def sentiment_analysis_trending():
    return render_template("sentiment_analysis_trending.html")


@app.route("/sentiment_analysis_getplotdata/")
def sentiment_analysis_getplotdata():
    # Get the top providers based on number of pastes
    oneHour = 60*60
    sevenDays = oneHour*24*7
    dateStart = datetime.datetime.now()
    dateStart = dateStart.replace(minute=0, second=0, microsecond=0)
    dateStart_timestamp = calendar.timegm(dateStart.timetuple())

    to_return = {}
    for cur_provider in r_serv_charts.smembers('providers_set'):
       cur_provider_name = cur_provider + '_' 
       list_date = {}
       for cur_timestamp in range(int(dateStart_timestamp), int(dateStart_timestamp)-sevenDays-oneHour, -oneHour):
           cur_set_name = cur_provider_name + str(cur_timestamp)
           
           list_value = []
           for cur_id in r_serv_sentiment.smembers(cur_set_name):
               cur_value = r_serv_sentiment.get(cur_id)
               list_value.append(cur_value)
           list_date[cur_timestamp] = list_value
       to_return[cur_provider] = list_date

    return jsonify(to_return)



@app.route("/sentiment_analysis_plot_tool/")
def sentiment_analysis_plot_tool():
    return render_template("sentiment_analysis_plot_tool.html")



@app.route("/sentiment_analysis_plot_tool_getdata/", methods=['GET'])
def sentiment_analysis_plot_tool_getdata():
    getProviders = request.args.get('getProviders')

    if getProviders == 'True':
        providers = []
        for cur_provider in r_serv_charts.smembers('providers_set'):
            providers.append(cur_provider)
        return jsonify(providers)

    else:
        query = request.args.get('query')
        Qdate = request.args.get('Qdate')
        print query
        print Qdate
        data = [[1,12], [2,32], [3,11]]
        return jsonify(data)



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
