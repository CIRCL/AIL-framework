#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import datetime
import calendar
from Date import Date
import flask
from flask import Flask, render_template, jsonify, request, Blueprint

import Paste

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_serv_charts = Flask_config.r_serv_charts
r_serv_sentiment = Flask_config.r_serv_sentiment

sentiments = Blueprint('sentiments', __name__, template_folder='templates')

# ============ FUNCTIONS ============

def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return date_list


# ============ ROUTES ============

@sentiments.route("/sentiment_analysis_trending/")
def sentiment_analysis_trending():
    return render_template("sentiment_analysis_trending.html")


@sentiments.route("/sentiment_analysis_getplotdata/", methods=['GET'])
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
                print('today provider empty')
                range_providers = r_serv_charts.smembers('all_provider_set')

            return jsonify(list(range_providers))

    elif provider is not None:
        to_return = {}

        cur_provider_name = provider + '_'
        list_date = {}
        for cur_timestamp in range(int(dateStart_timestamp), int(dateStart_timestamp)-sevenDays-oneHour, -oneHour):
            cur_set_name = cur_provider_name + str(cur_timestamp)

            list_value = []
            for cur_id in r_serv_sentiment.smembers(cur_set_name):
                cur_value = (r_serv_sentiment.get(cur_id))
                list_value.append(cur_value)
            list_date[cur_timestamp] = list_value
        to_return[provider] = list_date

        return jsonify(to_return)
    return "Bad request"



@sentiments.route("/sentiment_analysis_plot_tool/")
def sentiment_analysis_plot_tool():
    return render_template("sentiment_analysis_plot_tool.html")



@sentiments.route("/sentiment_analysis_plot_tool_getdata/", methods=['GET'])
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

        date1 = (Qdate.split('-')[0]).split('/')
        date1 = datetime.date(int(date1[2]), int(date1[0]), int(date1[1]))

        date2 = (Qdate.split('-')[1]).split('/')
        date2 = datetime.date(int(date2[2]), int(date2[0]), int(date2[1]))

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
                    cur_value = (r_serv_sentiment.get(cur_id))
                    list_value.append(cur_value)
                list_date[cur_timestamp] = list_value
            to_return[cur_provider] = list_date

        return jsonify(to_return)

# ========= REGISTRATION =========
app.register_blueprint(sentiments, url_prefix=baseUrl)
