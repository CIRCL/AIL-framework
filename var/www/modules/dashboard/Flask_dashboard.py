#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the dashboard page
'''
import json
import os
import datetime
import time
import flask

from Date import Date

from flask import Flask, render_template, jsonify, request, Blueprint, url_for

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_serv = Flask_config.r_serv
r_serv_log = Flask_config.r_serv_log

max_dashboard_logs = Flask_config.max_dashboard_logs

dashboard = Blueprint('dashboard', __name__, template_folder='templates')

# ============ FUNCTIONS ============

def event_stream():
    pubsub = r_serv_log.pubsub()
    pubsub.psubscribe("Script" + '.*')
    for msg in pubsub.listen():

        type = msg['type']
        pattern = msg['pattern']
        channel = msg['channel']
        data = msg['data']

        msg = {'channel': channel, 'type': type, 'pattern': pattern, 'data': data}

        level = (msg['channel']).split('.')[1]
        if msg['type'] == 'pmessage' and level != "DEBUG":
            yield 'data: %s\n\n' % json.dumps(msg)

def get_queues(r):
    # We may want to put the llen in a pipeline to do only one query.
    newData = []
    for queue, card in r.hgetall("queues").items():

        key = "MODULE_" + queue + "_"
        keySet = "MODULE_TYPE_" + queue

        for moduleNum in r.smembers(keySet):

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

def get_date_range(date_from, num_day):
    date = Date(str(date_from[0:4])+str(date_from[4:6]).zfill(2)+str(date_from[6:8]).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        new_date = date.substract_day(i)
        date_list.append(new_date[0:4] +'-'+ new_date[4:6] +'-'+ new_date[6:8])

    return date_list

def dashboard_alert(log):
    # check if we need to display this log
    if len(log)>50:
        date = log[1:5]+log[6:8]+log[9:11]
        utc_str = log[1:20]
        log = log[46:].split(';')
        if len(log) == 6:
            time = datetime_from_utc_to_local(utc_str)
            path = url_for('showsavedpastes.showsavedpaste',paste=log[5])

            res = {'date': date, 'time': time, 'script': log[0], 'domain': log[1], 'date_paste': log[2],
                  'paste': log[3], 'message': log[4], 'path': path}
            return res
        else:
            return False
    else:
        return False

def datetime_from_utc_to_local(utc_str):
    utc_datetime = datetime.datetime.strptime(utc_str, '%Y-%m-%d %H:%M:%S')
    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
    local_time_str = (utc_datetime + offset).strftime('%H:%M:%S')
    return local_time_str

# ============ ROUTES ============

@dashboard.route("/_logs")
def logs():
    return flask.Response(event_stream(), mimetype="text/event-stream")

@dashboard.route("/_get_last_logs_json")
def get_last_logs_json():
    date = datetime.datetime.now().strftime("%Y%m%d")

    max_day_search = 6
    day_search = 0
    warning_found = 0
    warning_to_found = max_dashboard_logs

    last_logs = []

    date_range = get_date_range(date, max_day_search)
    while max_day_search != day_search and warning_found != warning_to_found:

        filename_warning_log = 'logs/Script_warn-'+ date_range[day_search] +'.log'
        filename_log = os.path.join(os.environ['AIL_HOME'], filename_warning_log)

        try:
            with open(filename_log, 'r') as f:
                lines = f.read().splitlines()
                curr_index = -1
                while warning_found != warning_to_found:
                    try:
                        # get lasts warning logs
                        log_warn = dashboard_alert(lines[curr_index])
                        if log_warn != False:
                            last_logs.append(log_warn)
                            warning_found = warning_found + 1
                        curr_index = curr_index - 1

                    except IndexError:
                        # check previous warning log file
                        day_search = day_search + 1
                        break
        except FileNotFoundError:
            # check previous warning log file
            day_search = day_search + 1

    return jsonify(list(reversed(last_logs)))


@dashboard.route("/_stuff", methods=['GET'])
def stuff():
    return jsonify(row1=get_queues(r_serv))


@dashboard.route("/")
def index():
    default_minute = cfg.get("Flask", "minute_processed_paste")
    threshold_stucked_module = cfg.getint("Module_ModuleInformation", "threshold_stucked_module")
    log_select = {10, 25, 50, 100}
    log_select.add(max_dashboard_logs)
    log_select = list(log_select)
    log_select.sort()
    return render_template("index.html", default_minute = default_minute, threshold_stucked_module=threshold_stucked_module,
                            log_select=log_select, selected=max_dashboard_logs)

# ========= REGISTRATION =========
app.register_blueprint(dashboard, url_prefix=baseUrl)
