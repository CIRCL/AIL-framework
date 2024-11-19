#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file, stream_with_context
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import ail_objects
from lib import ail_stats



# ============ BLUEPRINT ============
objects_objs = Blueprint('objects_objs', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects'))


# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============
@objects_objs.route("/objects", methods=['GET'])
@login_required
@login_read_only
def objects():
    nb_objects = ail_stats.get_nb_objs_dashboard()
    print(nb_objects)
    feeders_dashboard = ail_stats.get_feeders_dashboard_full()
    return render_template("objs_dashboard.html", feeders_dashboard=feeders_dashboard, nb_objects=nb_objects)



# ============= ROUTES ==============

