#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import datetime
import sys
import os
from flask import Flask, render_template, jsonify, request, Blueprint

from Date import Date
from HiddenServices import HiddenServices

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_onion = Flask_config.r_serv_onion

hiddenServices = Blueprint('hiddenServices', __name__, template_folder='templates')

# ============ FUNCTIONS ============
def one():
    return 1

def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date( '{}{}{}'.format(str(curr_date.year), str(curr_date.month).zfill(2), str(curr_date.day).zfill(2)) )
    date_list = []

    for i in range(0, num_day):
        date_list.append(date.substract_day(i))

    return list(reversed(date_list))

def get_onion_status(domain, date):
    if r_serv_onion.sismember('onion_up:'+date , domain):
        return True
    else:
        return False
# ============= ROUTES ==============

@hiddenServices.route("/hiddenServices/", methods=['GET'])
def hiddenServices_page():
    last_onions = r_serv_onion.lrange('last_onion', 0 ,-1)
    list_onion = []

    for onion in last_onions:
        metadata_onion = {}
        metadata_onion['domain'] = onion
        metadata_onion['last_check'] = r_serv_onion.hget('onion_metadata:{}'.format(onion), 'last_check')
        metadata_onion['first_seen'] = r_serv_onion.hget('onion_metadata:{}'.format(onion), 'first_seen')
        if get_onion_status(onion, metadata_onion['last_check']):
            metadata_onion['status_text'] = 'UP'
            metadata_onion['status_color'] = 'Green'
            metadata_onion['status_icon'] = 'fa-check-circle'
        else:
            metadata_onion['status_text'] = 'DOWN'
            metadata_onion['status_color'] = 'Red'
            metadata_onion['status_icon'] = 'fa-times-circle'
        list_onion.append(metadata_onion)

    return render_template("hiddenServices.html", last_onions=list_onion)

@hiddenServices.route("/hiddenServices/onion_domain", methods=['GET'])
def onion_domain():
    onion_domain = request.args.get('onion_domain')
    if onion_domain is None or not r_serv_onion.exists('onion_metadata:{}'.format(onion_domain)):
        pass
        # # TODO: FIXME return 404

    last_check = r_serv_onion.hget('onion_metadata:{}'.format(onion_domain), 'last_check')
    first_seen = r_serv_onion.hget('onion_metadata:{}'.format(onion_domain), 'first_seen')
    domain_paste = r_serv_onion.hget('onion_metadata:{}'.format(onion_domain), 'paste_parent')
    date_crawled = r_serv_onion.smembers('onion_history:{}'.format(onion_domain))

    h = HiddenServices(onion_domain, 'onion')
    l_pastes = h.get_last_crawled_pastes()
    screenshot = h.get_domain_random_screenshot(l_pastes)[0]

    return render_template("showDomain.html", domain=onion_domain, last_check=last_check, first_seen=first_seen,
                            domain_paste=domain_paste, screenshot=screenshot)

# ============= JSON ==============
@hiddenServices.route("/hiddenServices/domain_crawled_7days_json", methods=['GET'])
def domain_crawled_7days_json():
    type = 'onion'
        ## TODO: # FIXME: 404 error

    date_range = get_date_range(7)
    json_domain_stats = []
    #try:
    for date in date_range:
        nb_domain_up = r_serv_onion.scard('{}_up:{}'.format(type, date))
        nb_domain_down = r_serv_onion.scard('{}_up:{}'.format(type, date))
        date = date[0:4] + '-' + date[4:6] + '-' + date[6:8]
        json_domain_stats.append({ 'date': date, 'value': int( nb_domain_up ), 'nb_domain_down': int( nb_domain_down )})
    #except:
        #return jsonify()

    return jsonify(json_domain_stats)

# ========= REGISTRATION =========
app.register_blueprint(hiddenServices)
