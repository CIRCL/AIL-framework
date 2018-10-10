#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
from flask import Flask, render_template, jsonify, request, Blueprint

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl

MODULENAME = Blueprint('MODULENAME', __name__, template_folder='templates')

# ============ FUNCTIONS ============
def one():
    return 1

# ============= ROUTES ==============

@MODULENAME.route("/MODULENAME/", methods=['GET'])
def MODULENAME_page():
    return render_template("MODULENAME.html")


# ========= REGISTRATION =========
app.register_blueprint(MODULENAME, url_prefix=baseUrl)
