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

# Import config
import Flask_config

# CONFIG #
cfg = Flask_config.cfg

Flask_config.app = Flask(__name__, static_url_path='/static/')
app = Flask_config.app

# import routes and functions from modules
import Flask_dashboard
import Flask_trendingcharts
import Flask_trendingmodules
import Flask_browsepastes
import Flask_sentiment
import Flask_terms
import Flask_search
import Flask_showpaste

def list_len(s):
    return len(s)
app.jinja_env.filters['list_len'] = list_len


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

# ============ MAIN ============

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7000, threaded=True)
