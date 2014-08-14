#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis
import ConfigParser
import json
from flask import Flask, render_template, jsonify
import flask

# CONFIG #
cfg = ConfigParser.ConfigParser()
cfg.read('../../bin/packages/config.cfg')

# REDIS #
r_serv = redis.StrictRedis(
    host=cfg.get("Redis_Queues", "host"),
    port=cfg.getint("Redis_Queues", "port"),
    db=cfg.getint("Redis_Queues", "db"))

r_serv_log = redis.StrictRedis(
    host=cfg.get("Redis_Log", "host"),
    port=cfg.getint("Redis_Log", "port"),
    db=cfg.getint("Redis_Log", "db"))


app = Flask(__name__, static_url_path='/static/')


def event_stream():
    pubsub = r_serv_log.pubsub()
    pubsub.psubscribe("Script" + '.*')
    for msg in pubsub.listen():
        level = msg['channel'].split('.')[1]
        if msg['type'] == 'pmessage' and level != "DEBUG":
            yield 'data: %s\n\n' % json.dumps(msg)


@app.route("/_logs")
def logs():
    return flask.Response(event_stream(), mimetype="text/event-stream")


@app.route("/_stuff", methods=['GET'])
def stuff():
    row1 = []
    for queue in r_serv.smembers("queues"):
        row1.append((queue, r_serv.llen(queue)))
    return jsonify(row1=row1)


@app.route("/")
def index():
    row = []
    for queue in r_serv.smembers("queues"):
        row.append((queue, r_serv.llen(queue)))

    return render_template("index.html", queues_name=row)


@app.route("/monitoring/")
def monitoring():
    for queue in r_serv.smembers("queues"):
        return render_template("Queue_live_Monitoring.html", last_value=queue)


@app.route("/wordstrending/")
def wordstrending():
    return render_template("Wordstrending.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7000, threaded=True)
