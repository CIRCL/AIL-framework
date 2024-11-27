#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import time

import json # TODO REMOVE ME

from flask import render_template, Response, request, Blueprint
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_admin, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_stats

# TODO STATS
# from lib import ail_updates

# ============ BLUEPRINT ============
dashboard = Blueprint('dashboard', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/dashboard'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

# ============ FUNCTIONS ============

# ============= ROUTES ==============

@dashboard.route("/", methods=['GET'])
@login_required
@login_read_only
def index():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    nb_objects = ail_stats.get_nb_objs_dashboard()
    feeders_dashboard = ail_stats.get_feeders_dashboard_full()
    crawlers_stats = ail_stats.get_crawlers_stats()
    trackers = ail_stats.get_tracked_objs_dashboard(user_org, user_id)
    tagged_objs = ail_stats.get_tagged_objs_dashboard()
    return render_template("dashboard.html", feeders_dashboard=feeders_dashboard,
                           nb_objects=nb_objects, trackers=trackers, tagged_objs=tagged_objs,
                           bootstrap_label=bootstrap_label, crawlers_stats=crawlers_stats)
