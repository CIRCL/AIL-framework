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
r_serv_term = Flask_config.r_serv_term
# ============ FUNCTIONS ============

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


# ============ ROUTES ============

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
            value = r_serv_term.hget(timestamp, term)
            curr_value_range = int(value) if value is not None else 0
            value_range.append([timestamp, curr_value_range])
        value_range.insert(0,term)
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


