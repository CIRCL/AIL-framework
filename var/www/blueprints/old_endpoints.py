#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only

# ============ BLUEPRINT ============
old_endpoints = Blueprint('old_endpoints', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates'))

# ============ VARIABLES ============



# ============ FUNCTIONS ============


# ============= ROUTES ==============
@old_endpoints.route("/showsavedpaste/")
@login_required
@login_read_only
def showsavedpaste():
    item_id = request.args.get('paste', '')
    return redirect(url_for('objects_item.showItem', id=item_id))
