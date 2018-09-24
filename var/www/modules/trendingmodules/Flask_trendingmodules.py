#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import datetime
from Date import Date
import flask
from flask import Flask, render_template, jsonify, request, Blueprint

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_serv_charts = Flask_config.r_serv_charts

trendingmodules = Blueprint('trendingmodules', __name__, template_folder='templates')

# ============ FUNCTIONS ============

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


def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return date_list

# ============ ROUTES ============

@trendingmodules.route("/_moduleCharts", methods=['GET'])
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
        member_set = member_set if member_set is not None else []
        if len(member_set) == 0:
            member_set.append(("No relevant data", int(100)))
        return jsonify(member_set)


@trendingmodules.route("/_providersChart", methods=['GET'])
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
            curr_value_size = ( r_serv_charts.hget(keyword_name+'_'+'size', date) )
            if curr_value_size is not None:
                curr_value_size = curr_value_size

            curr_value_num = r_serv_charts.hget(keyword_name+'_'+'num', date)

            curr_value_size_avg = r_serv_charts.hget(keyword_name+'_'+'avg', date)
            if curr_value_size_avg is not None:
                curr_value_size_avg = curr_value_size_avg


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


@trendingmodules.route("/moduletrending/")
def moduletrending():
    return render_template("Moduletrending.html")


# ========= REGISTRATION =========
app.register_blueprint(trendingmodules, url_prefix=baseUrl)
