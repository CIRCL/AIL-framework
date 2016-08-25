#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis
import ConfigParser
import json
import datetime
import time
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

r_serv_term = redis.StrictRedis(
        host=cfg.get("Redis_Level_DB_TermFreq", "host"),
        port=cfg.getint("Redis_Level_DB_TermFreq", "port"),
        db=cfg.getint("Redis_Level_DB_TermFreq", "db"))

r_serv_pasteName = redis.StrictRedis(
    host=cfg.get("Redis_Paste_Name", "host"),
    port=cfg.getint("Redis_Paste_Name", "port"),
    db=cfg.getint("Redis_Paste_Name", "db"))


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
    data = [(queue, int(card)) for queue, card in r.hgetall("queues").iteritems()]
    newData = []

    curr_range = 50
    for queue, card in data:
        key = "MODULE_" + queue + "_"
        for i in range(1, 50):
            curr_num = r.get("MODULE_"+ queue + "_" + str(i))
            if curr_num is None:
                curr_range = i
                break

        for moduleNum in range(1, curr_range):
            value = r.get(key + str(moduleNum))
            if value is not None:
                timestamp, path = value.split(", ")
                if timestamp is not None:
                    startTime_readable = datetime.datetime.fromtimestamp(int(timestamp))
                    processed_time_readable = str((datetime.datetime.now() - startTime_readable)).split('.')[0]
                    seconds = int((datetime.datetime.now() - startTime_readable).total_seconds())
                    newData.append( (queue, card, seconds, moduleNum) )
                else:
                    newData.append( (queue, cards, 0, moduleNum) )

    return newData


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
    days = 0
    for date in get_date_range(15):
        redis_progression_name_set = 'top_'+ module_name +'_set_' + date
        member_set = server.zrevrangebyscore(redis_progression_name_set, '+inf', '-inf', withscores=True)
        if len(member_set) == 0: #No data for this date
            days += 1
        else:
            member_set.insert(0, ("passed_days", days))
            return member_set


def Term_getValueOverRange(word, startDate, num_day):
    passed_days = 0
    oneDay = 60*60*24
    to_return = []
    curr_to_return = 0
    for timestamp in range(startDate, startDate - max(num_day)*oneDay, -oneDay):
        value = r_serv_term.hget(timestamp, word)
        curr_to_return += int(value) if value is not None else 0
        for i in num_day:
            if passed_days == i-1:
                to_return.append(curr_to_return)
        passed_days += 1
    return to_return


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
            curr_value_size_avg = r_serv_charts.hget(keyword_name+'_'+'avg', date)
            if module_name == "size":
                curr_value = float(curr_value_size_avg if curr_value_size_avg is not None else 0)
            else:
                curr_value = float(curr_value_num if curr_value_num is not None else 0.0)

            bar_values.append([date[0:4]+'/'+date[4:6]+'/'+date[6:8], curr_value])
        bar_values.insert(0, keyword_name)
        return jsonify(bar_values)

    else:
        #redis_provider_name_set = 'top_size_set' if module_name == "size" else 'providers_set'
        redis_provider_name_set = 'top_avg_size_set_' if module_name == "size" else 'providers_set_'
        redis_provider_name_set = redis_provider_name_set + get_date_range(0)[0]
        
        member_set = r_serv_charts.zrevrangebyscore(redis_provider_name_set, '+inf', '-inf', withscores=True, start=0, num=8)
        # Member set is a list of (value, score) pairs
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

    # Search filename
    print r_serv_pasteName.smembers(q[0])
    for path in r_serv_pasteName.smembers(q[0]):
        print path
        r.append(path)
        paste = Paste.Paste(path)
        content = paste.get_p_content().decode('utf8', 'ignore')
        content_range = max_preview_char if len(content)>max_preview_char else len(content)-1
        c.append(content[0:content_range])
        curr_date = str(paste._get_p_date())
        curr_date = curr_date[0:4]+'/'+curr_date[4:6]+'/'+curr_date[6:]
        paste_date.append(curr_date)
        paste_size.append(paste._get_p_size())

    # Search full line
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


@app.route("/sentiment_analysis_getplotdata/", methods=['GET'])
def sentiment_analysis_getplotdata():
    # Get the top providers based on number of pastes
    oneHour = 60*60
    sevenDays = oneHour*24*7
    dateStart = datetime.datetime.now()
    dateStart = dateStart.replace(minute=0, second=0, microsecond=0)
    dateStart_timestamp = calendar.timegm(dateStart.timetuple())

    getAllProviders = request.args.get('getProviders')
    provider = request.args.get('provider')
    allProvider = request.args.get('all')
    if getAllProviders == 'True':
        if allProvider == "True":
            range_providers = r_serv_charts.smembers('all_provider_set')
            return jsonify(list(range_providers))
        else:
            range_providers = r_serv_charts.zrevrangebyscore('providers_set_'+ get_date_range(0)[0], '+inf', '-inf', start=0, num=8)
            # if empty, get yesterday top providers
            range_providers = r_serv_charts.zrevrangebyscore('providers_set_'+ get_date_range(1)[1], '+inf', '-inf', start=0, num=8) if range_providers == [] else range_providers
            # if still empty, takes from all providers
            if range_providers == []:
                print 'today provider empty'
                range_providers = r_serv_charts.smembers('all_provider_set')
            return jsonify(range_providers)

    elif provider is not None:
        to_return = {}

        cur_provider_name = provider + '_'
        list_date = {}
        for cur_timestamp in range(int(dateStart_timestamp), int(dateStart_timestamp)-sevenDays-oneHour, -oneHour):
            cur_set_name = cur_provider_name + str(cur_timestamp)

            list_value = []
            for cur_id in r_serv_sentiment.smembers(cur_set_name):
                cur_value = r_serv_sentiment.get(cur_id)
                list_value.append(cur_value)
            list_date[cur_timestamp] = list_value
        to_return[provider] = list_date

        return jsonify(to_return)
    return "Bad request"



@app.route("/sentiment_analysis_plot_tool/")
def sentiment_analysis_plot_tool():
    return render_template("sentiment_analysis_plot_tool.html")



@app.route("/sentiment_analysis_plot_tool_getdata/", methods=['GET'])
def sentiment_analysis_plot_tool_getdata():
    getProviders = request.args.get('getProviders')

    if getProviders == 'True':
        providers = []
        for cur_provider in r_serv_charts.smembers('all_provider_set'):
            providers.append(cur_provider)
        return jsonify(providers)

    else:
        query = request.args.get('query')
        query = query.split(',')
        Qdate = request.args.get('Qdate')

        date1 = (Qdate.split('-')[0]).split('.')
        date1 = datetime.date(int(date1[2]), int(date1[1]), int(date1[0]))

        date2 = (Qdate.split('-')[1]).split('.')
        date2 = datetime.date(int(date2[2]), int(date2[1]), int(date2[0]))

        timestamp1 = calendar.timegm(date1.timetuple())
        timestamp2 = calendar.timegm(date2.timetuple())

        oneHour = 60*60
        oneDay = oneHour*24

        to_return = {}
        for cur_provider in query:
            list_date = {}
            cur_provider_name = cur_provider + '_'
            for cur_timestamp in range(int(timestamp1), int(timestamp2)+oneDay, oneHour):
                cur_set_name = cur_provider_name + str(cur_timestamp)

                list_value = []
                for cur_id in r_serv_sentiment.smembers(cur_set_name):
                    cur_value = r_serv_sentiment.get(cur_id)
                    list_value.append(cur_value)
                list_date[cur_timestamp] = list_value
            to_return[cur_provider] = list_date

        return jsonify(to_return)


@app.route("/terms_management/")
def terms_management():
    TrackedTermsSet_Name = "TrackedSetTermSet"
    BlackListTermsSet_Name = "BlackListSetTermSet"
    TrackedTermsDate_Name = "TrackedTermDate"
    BlackListTermsDate_Name = "BlackListTermDate"
    
    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())

    track_list = []
    track_list_values = []
    track_list_num_of_paste = []
    for tracked_term in r_serv_term.smembers(TrackedTermsSet_Name):
        track_list.append(tracked_term)
        value_range = Term_getValueOverRange(tracked_term, today_timestamp, [1, 7, 31])

        term_date = r_serv_term.hget(TrackedTermsDate_Name, tracked_term)

        set_paste_name = "tracked_" + tracked_term
        track_list_num_of_paste.append(r_serv_term.scard(set_paste_name))
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        track_list_values.append(value_range)


    black_list = []
    for blacked_term in r_serv_term.smembers(BlackListTermsSet_Name):
        term_date = r_serv_term.hget(BlackListTermsDate_Name, blacked_term)
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        black_list.append([blacked_term, term_date])

    return render_template("terms_management.html", black_list=black_list, track_list=track_list, track_list_values=track_list_values,  track_list_num_of_paste=track_list_num_of_paste)


@app.route("/terms_management_query_paste/")
def terms_management_query_paste():
    term =  request.args.get('term')
    TrackedTermsSet_Name = "TrackedSetTermSet"
    paste_info = []

    set_paste_name = "tracked_" + term
    track_list_path = r_serv_term.smembers(set_paste_name)

    for path in track_list_path:
        paste = Paste.Paste(path)
        p_date = str(paste._get_p_date())
        p_date = p_date[6:]+'/'+p_date[4:6]+'/'+p_date[0:4]
        p_source = paste.p_source
        p_encoding = paste._get_p_encoding()
        p_size = paste.p_size
        p_mime = paste.p_mime
        p_lineinfo = paste.get_lines_info()
        p_content = paste.get_p_content().decode('utf-8', 'ignore')
        if p_content != 0:
            p_content = p_content[0:400]
        paste_info.append({"path": path, "date": p_date, "source": p_source, "encoding": p_encoding, "size": p_size, "mime": p_mime, "lineinfo": p_lineinfo, "content": p_content})

    return jsonify(paste_info)


@app.route("/terms_management_query/")
def terms_management_query():
    TrackedTermsDate_Name = "TrackedTermDate"
    BlackListTermsDate_Name = "BlackListTermDate"
    term =  request.args.get('term')
    section = request.args.get('section')

    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())
    value_range = Term_getValueOverRange(term, today_timestamp, [1, 7, 31])

    if section == "followTerm":
        term_date = r_serv_term.hget(TrackedTermsDate_Name, term)
    elif section == "blacklistTerm":
        term_date = r_serv_term.hget(BlackListTermsDate_Name, term)

    term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
    value_range.append(str(term_date))
    return jsonify(value_range)


@app.route("/terms_management_action/", methods=['GET'])
def terms_management_action():
    TrackedTermsSet_Name = "TrackedSetTermSet"
    TrackedTermsDate_Name = "TrackedTermDate"
    BlackListTermsDate_Name = "BlackListTermDate"
    BlackListTermsSet_Name = "BlackListSetTermSet"

    today = datetime.datetime.now()
    today = today.replace(microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())


    section = request.args.get('section')
    action = request.args.get('action')
    term =  request.args.get('term')
    if action is None or term is None:
        return "None"
    else:
        if section == "followTerm":
            if action == "add":
                r_serv_term.sadd(TrackedTermsSet_Name, term.lower())
                r_serv_term.hset(TrackedTermsDate_Name, term, today_timestamp)
            else:
                r_serv_term.srem(TrackedTermsSet_Name, term.lower())
        elif section == "blacklistTerm":
            if action == "add":
                r_serv_term.sadd(BlackListTermsSet_Name, term.lower())
                r_serv_term.hset(BlackListTermsDate_Name, term, today_timestamp)
            else:
                r_serv_term.srem(BlackListTermsSet_Name, term.lower())
        else:
            return "None"

        to_return = {}
        to_return["section"] = section
        to_return["action"] = action
        to_return["term"] = term
        return jsonify(to_return)



@app.route("/terms_plot_tool/")
def terms_plot_tool():
    term =  request.args.get('term')
    if term is not None:
        return render_template("terms_plot_tool.html", term=term)
    else:
        return render_template("terms_plot_tool.html", term="")


@app.route("/terms_plot_tool_data/")
def terms_plot_tool_data():
    oneDay = 60*60*24
    range_start =  datetime.datetime.utcfromtimestamp(int(float(request.args.get('range_start')))) if request.args.get('range_start') is not None else 0;
    range_start = range_start.replace(hour=0, minute=0, second=0, microsecond=0)
    range_start = calendar.timegm(range_start.timetuple())
    range_end =  datetime.datetime.utcfromtimestamp(int(float(request.args.get('range_end')))) if request.args.get('range_end') is not None else 0;
    range_end = range_end.replace(hour=0, minute=0, second=0, microsecond=0)
    range_end = calendar.timegm(range_end.timetuple())
    term =  request.args.get('term')

    if term is None:
        return "None"
    else:
        value_range = []
        for timestamp in range(range_start, range_end+oneDay, oneDay):
            print timestamp, term
            value = r_serv_term.hget(timestamp, term)
            curr_value_range = int(value) if value is not None else 0
            value_range.append([timestamp, curr_value_range])
        return jsonify(value_range)


@app.route("/terms_plot_top/")
def terms_plot_top():
    return render_template("terms_plot_top.html")


@app.route("/terms_plot_top_data/")
def terms_plot_top_data():
    oneDay = 60*60*24
    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())

    set_day = "TopTermFreq_set_day_" + str(today_timestamp)
    set_week = "TopTermFreq_set_week";
    set_month = "TopTermFreq_set_month";

    the_set = request.args.get('set')
    num_day = int(request.args.get('num_day'))
    if the_set is None:
        return "None"
    else:
        to_return = []
        if the_set == "TopTermFreq_set_day":
            the_set += "_" + str(today_timestamp)

        for term, tot_value in r_serv_term.zrevrangebyscore(the_set, '+inf', '-inf', withscores=True, start=0, num=20):
            position = {}
            position['day'] = r_serv_term.zrevrank(set_day, term)
            position['day'] = position['day']+1 if position['day'] is not None else "<20"
            position['week'] = r_serv_term.zrevrank(set_week, term)
            position['week'] = position['week']+1 if position['week'] is not None else "<20"
            position['month'] = r_serv_term.zrevrank(set_month, term)
            position['month'] = position['month']+1 if position['month'] is not None else "<20"
            value_range = []
            for timestamp in range(today_timestamp, today_timestamp - num_day*oneDay, -oneDay):
                value = r_serv_term.hget(timestamp, term)
                curr_value_range = int(value) if value is not None else 0
                value_range.append([timestamp, curr_value_range])
                
            to_return.append([term, value_range, tot_value, position])
    
        return jsonify(to_return)



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
