#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis
import ConfigParser
import json
from flask import Flask, render_template, jsonify, request
import flask
import os


# CONFIG #
configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
if not os.path.exists(configfile):
    raise Exception('Unable to find the configuration file. \
                    Did you set environment variables? \
                    Or activate the virtualenv.')

cfg = ConfigParser.ConfigParser()
cfg.read(configfile)

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


def get_queues(r):
    # We may want to put the llen in a pipeline to do only one query.
    return [(queue, int(card)) for queue, card in
            r.hgetall("queues").iteritems()]


@app.route("/_logs")
def logs():
    return flask.Response(event_stream(), mimetype="text/event-stream")


@app.route("/_stuff", methods=['GET'])
def stuff():
    return jsonify(row1=get_queues(r_serv))


@app.route("/search", methods=['POST'])
def search():
    query = request.form['query']
    q = []
    q.append(query)
    r = []
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
    return render_template("search.html", r=r)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/monitoring/")
def monitoring():
    for queue in r_serv.smembers("queues"):
        return render_template("Queue_live_Monitoring.html", last_value=queue)


@app.route("/wordstrending/")
def wordstrending():
    return render_template("Wordstrending.html")


@app.route("/protocolstrending/")
def protocolstrending():
    return render_template("Protocolstrending.html")

@app.route("/tldstrending/")
def tldstrending():
    return render_template("Tldstrending.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7000, threaded=True)
