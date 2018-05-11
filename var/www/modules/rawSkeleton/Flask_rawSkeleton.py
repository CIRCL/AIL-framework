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

rawSkeleton = Blueprint('rawSkeleton', __name__, template_folder='templates')

# ============ FUNCTIONS ============
def one():
    return 1

# ============= ROUTES ==============

@rawSkeleton.route("/rawSkeleton/", methods=['GET'])
def skeleton_page():
    return render_template("rawSkeleton.html")


# ========= REGISTRATION =========
app.register_blueprint(rawSkeleton)
