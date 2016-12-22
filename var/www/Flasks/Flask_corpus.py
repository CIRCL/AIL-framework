#!/usr/bin/env python2
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import datetime
import calendar
import flask
from flask import Flask, render_template, jsonify, request

import Paste

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_corpus = Flask_config.r_serv_corpus
# ============ FUNCTIONS ============

def Corpus_getValueOverRange(word, startDate, num_day):
    passed_days = 0
    oneDay = 60*60*24
    to_return = []
    curr_to_return = 0
    for timestamp in range(startDate, startDate - max(num_day)*oneDay, -oneDay):
        value = r_serv_corpus.hget(timestamp, word)
        curr_to_return += int(value) if value is not None else 0
        for i in num_day:
            if passed_days == i-1:
                to_return.append(curr_to_return)
        passed_days += 1
    return to_return


# ============ ROUTES ============

@app.route("/corpus_management/")
def corpus_management():
    TrackedCorpusSet_Name = "TrackedSetCorpusSet"
    TrackedCorpusDate_Name = "TrackedCorpusDate"
    
    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())

    track_list = []
    track_list_values = []
    track_list_num_of_paste = []
    for tracked_corpus in r_serv_corpus.smembers(TrackedCorpusSet_Name):
        track_list.append(tracked_corpus)
        value_range = Corpus_getValueOverRange(tracked_corpus, today_timestamp, [1, 7, 31])

        corpus_date = r_serv_corpus.hget(TrackedCorpusDate_Name, tracked_corpus)

        set_paste_name = "tracked_" + tracked_corpus
        track_list_num_of_paste.append(r_serv_corpus.scard(set_paste_name))
        corpus_date = datetime.datetime.utcfromtimestamp(int(corpus_date)) if corpus_date is not None else "No date recorded"
        value_range.append(corpus_date)
        track_list_values.append(value_range)


    return render_template("corpus_management.html", black_list=black_list, track_list=track_list, track_list_values=track_list_values,  track_list_num_of_paste=track_list_num_of_paste)


@app.route("/corpus_management_query_paste/")
def corpus_management_query_paste():
    corpus =  request.args.get('corpus')
    TrackedCorpusSet_Name = "TrackedSetCorpusSet"
    paste_info = []

    set_paste_name = "tracked_" + corpus
    track_list_path = r_serv_corpus.smembers(set_paste_name)

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


@app.route("/corpus_management_query/")
def corpus_management_query():
    TrackedCorpusDate_Name = "TrackedCorpusDate"
    corpus =  request.args.get('corpus')

    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())
    value_range = corpus_getValueOverRange(corpus, today_timestamp, [1, 7, 31])

    corpus_date = r_serv_corpus.hget(TrackedCorpusDate_Name, corpus)

    corpus_date = datetime.datetime.utcfromtimestamp(int(corpus_date)) if corpus_date is not None else "No date recorded"
    value_range.append(str(corpus_date))
    return jsonify(value_range)


@app.route("/corpus_management_action/", methods=['GET'])
def corpus_management_action():
    TrackedCorpusSet_Name = "TrackedSetCorpusSet"
    TrackedCorpusDate_Name = "TrackedCorpusDate"

    today = datetime.datetime.now()
    today = today.replace(microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())


    section = request.args.get('section')
    action = request.args.get('action')
    corpus =  request.args.get('corpus')
    if action is None or corpus is None:
        return "None"
    else:
        if section == "followCorpus":
            if action == "add":
                r_serv_corpus.sadd(TrackedCorpusSet_Name, corpus.lower())
                r_serv_corpus.hset(TrackedCorpusDate_Name, corpus, today_timestamp)
            else:
                r_serv_corpus.srem(TrackedCorpusSet_Name, corpus.lower())
        else:
            return "None"

        to_return = {}
        to_return["section"] = section
        to_return["action"] = action
        to_return["corpus"] = corpus
        return jsonify(to_return)



@app.route("/corpus_plot_tool/")
def corpus_plot_tool():
    corpus =  request.args.get('corpus')
    if corpus is not None:
        return render_template("corpus_plot_tool.html", corpus=corpus)
    else:
        return render_template("corpus_plot_tool.html", corpus="")


@app.route("/corpus_plot_tool_data/")
def corpus_plot_tool_data():
    oneDay = 60*60*24
    range_start =  datetime.datetime.utcfromtimestamp(int(float(request.args.get('range_start')))) if request.args.get('range_start') is not None else 0;
    range_start = range_start.replace(hour=0, minute=0, second=0, microsecond=0)
    range_start = calendar.timegm(range_start.timetuple())
    range_end =  datetime.datetime.utcfromtimestamp(int(float(request.args.get('range_end')))) if request.args.get('range_end') is not None else 0;
    range_end = range_end.replace(hour=0, minute=0, second=0, microsecond=0)
    range_end = calendar.timegm(range_end.timetuple())
    corpus =  request.args.get('corpus')

    if corpus is None:
        return "None"
    else:
        value_range = []
        for timestamp in range(range_start, range_end+oneDay, oneDay):
            value = r_serv_corpus.hget(timestamp, corpus)
            curr_value_range = int(value) if value is not None else 0
            value_range.append([timestamp, curr_value_range])
        value_range.insert(0,corpus)
        return jsonify(value_range)


@app.route("/corpus_plot_top/")
def corpus_plot_top():
    return render_template("corpus_plot_top.html")


@app.route("/corpus_plot_top_data/")
def corpus_plot_top_data():
    oneDay = 60*60*24
    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())

    set_day = "TopCorpusFreq_set_day_" + str(today_timestamp)
    set_week = "TopCorpusFreq_set_week";
    set_month = "TopCorpusFreq_set_month";

    the_set = request.args.get('set')
    num_day = int(request.args.get('num_day'))
    if the_set is None:
        return "None"
    else:
        to_return = []
        if the_set == "TopCorpusFreq_set_day":
            the_set += "_" + str(today_timestamp)

        for corpus, tot_value in r_serv_corpus.zrevrangebyscore(the_set, '+inf', '-inf', withscores=True, start=0, num=20):
            position = {}
            position['day'] = r_serv_corpus.zrevrank(set_day, corpus)
            position['day'] = position['day']+1 if position['day'] is not None else "<20"
            position['week'] = r_serv_corpus.zrevrank(set_week, corpus)
            position['week'] = position['week']+1 if position['week'] is not None else "<20"
            position['month'] = r_serv_corpus.zrevrank(set_month, corpus)
            position['month'] = position['month']+1 if position['month'] is not None else "<20"
            value_range = []
            for timestamp in range(today_timestamp, today_timestamp - num_day*oneDay, -oneDay):
                value = r_serv_corpus.hget(timestamp, corpus)
                curr_value_range = int(value) if value is not None else 0
                value_range.append([timestamp, curr_value_range])
                
            to_return.append([corpus, value_range, tot_value, position])
    
        return jsonify(to_return)


