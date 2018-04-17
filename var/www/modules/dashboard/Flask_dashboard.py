#!/usr/bin/env python3.5
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the dashboard page
'''
import json

import datetime
import flask
from flask import Flask, render_template, jsonify, request, Blueprint

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv = Flask_config.r_serv
r_serv_log = Flask_config.r_serv_log

dashboard = Blueprint('dashboard', __name__, template_folder='templates')

# ============ FUNCTIONS ============

def event_stream():
    pubsub = r_serv_log.pubsub()
    pubsub.psubscribe("Script" + '.*')
    for msg in pubsub.listen():
        # bytes conversion
        try:
            type = msg['type'].decode('utf8')
        except:
            type = msg['type']
        try:
            pattern = msg['pattern'].decode('utf8')
        except:
            pattern = msg['pattern']
        try:
            channel = msg['channel'].decode('utf8')
        except:
            channel = msg['channel']
        try:
            data = msg['data'].decode('utf8')
        except:
            data = msg['data']

        msg = {'channel': channel, 'type': type, 'pattern': pattern, 'data': data}

        level = (msg['channel']).split('.')[1]
        if msg['type'] == 'pmessage' and level != "DEBUG":
            yield 'data: %s\n\n' % json.dumps(msg)

def get_queues(r):
    # We may want to put the llen in a pipeline to do only one query.
    newData = []
    for queue, card in r.hgetall("queues").items():
        queue = queue.decode('utf8')
        card = card.decode('utf8')
        key = "MODULE_" + queue + "_"
        keySet = "MODULE_TYPE_" + queue

        for moduleNum in r.smembers(keySet):
            moduleNum = moduleNum.decode('utf8')

            value = ( r.get(key + str(moduleNum)) ).decode('utf8')

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

# ============ ROUTES ============

@dashboard.route("/_logs")
def logs():
    return flask.Response(event_stream(), mimetype="text/event-stream")


@dashboard.route("/_stuff", methods=['GET'])
def stuff():
    return jsonify(row1=get_queues(r_serv))


@dashboard.route("/")
def index():
    default_minute = cfg.get("Flask", "minute_processed_paste")
    threshold_stucked_module = cfg.getint("Module_ModuleInformation", "threshold_stucked_module")
    return render_template("index.html", default_minute = default_minute, threshold_stucked_module=threshold_stucked_module)

# ========= REGISTRATION =========
app.register_blueprint(dashboard)
