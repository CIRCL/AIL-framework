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
r_serv_metadata = Flask_config.r_serv_metadata
bootstrap_label = Flask_config.bootstrap_label
PASTES_FOLDER = Flask_config.PASTES_FOLDER

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

def unpack_paste_tags(p_tags):
    l_tags = []
    for tag in p_tags:
        complete_tag = tag
        tag = tag.split('=')
        if len(tag) > 1:
            if tag[1] != '':
                tag = tag[1][1:-1]
            # no value
            else:
                tag = tag[0][1:-1]
        # use for custom tags
        else:
            tag = tag[0]
        l_tags.append( (tag, complete_tag) )
    return l_tags

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
        return '404'
        # # TODO: FIXME return 404

    last_check = r_serv_onion.hget('onion_metadata:{}'.format(onion_domain), 'last_check')
    last_check = '{}/{}/{}'.format(last_check[0:4], last_check[4:6], last_check[6:8])
    first_seen = r_serv_onion.hget('onion_metadata:{}'.format(onion_domain), 'first_seen')
    first_seen = '{}/{}/{}'.format(first_seen[0:4], first_seen[4:6], first_seen[6:8])
    origin_paste = r_serv_onion.hget('onion_metadata:{}'.format(onion_domain), 'paste_parent')

    h = HiddenServices(onion_domain, 'onion')
    l_pastes = h.get_last_crawled_pastes()
    if l_pastes:
        status = True
    else:
        status = False
    screenshot = h.get_domain_random_screenshot(l_pastes)
    if screenshot:
        screenshot = screenshot[0]
    else:
        screenshot = 'None'

    domain_tags = h.get_domain_tags()

    origin_paste_name = h.get_origin_paste_name()
    origin_paste_tags = unpack_paste_tags(r_serv_metadata.smembers('tag:{}'.format(origin_paste)))
    paste_tags = []
    path_name = []
    for path in l_pastes:
        path_name.append(path.replace(PASTES_FOLDER+'/', ''))
        p_tags = r_serv_metadata.smembers('tag:'+path)
        paste_tags.append(unpack_paste_tags(p_tags))

    return render_template("showDomain.html", domain=onion_domain, last_check=last_check, first_seen=first_seen,
                            l_pastes=l_pastes, paste_tags=paste_tags, bootstrap_label=bootstrap_label,
                            path_name=path_name, origin_paste_tags=origin_paste_tags, status=status,
                            origin_paste=origin_paste, origin_paste_name=origin_paste_name,
                            domain_tags=domain_tags, screenshot=screenshot)

@hiddenServices.route("/hiddenServices/onion_son", methods=['GET'])
def onion_son():
    onion_domain = request.args.get('onion_domain')

    h = HiddenServices(onion_domain, 'onion')
    l_pastes = h.get_last_crawled_pastes()
    l_son = h.get_domain_son(l_pastes)
    print(l_son)
    return 'l_son'

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
