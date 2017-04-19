#!/usr/bin/env python2
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

skeleton = Blueprint('skeleton', __name__, template_folder='templates')

# ============ FUNCTIONS ============
def one():
    return 1

# ============= ROUTES ==============

@skeleton.route("/skeleton/", methods=['GET'])
def skeleton_page():
    return render_template("skeleton.html")


# ========= REGISTRATION =========
app.register_blueprint(skeleton)
