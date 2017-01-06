#!/usr/bin/env python2
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending charts page
'''
import redis
import datetime
from Date import Date
import flask
from flask import Flask, render_template, jsonify, request

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_charts = Flask_config.r_serv_charts
# ============ FUNCTIONS ============

def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return date_list


# ============ ROUTES ============

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
        redis_progression_name = "z_top_progression_" + trending_name
        keyw_value = r_serv_charts.zrevrangebyscore(redis_progression_name, '+inf', '-inf', withscores=True, start=0, num=10)
        return jsonify(keyw_value)

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


