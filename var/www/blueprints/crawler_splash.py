#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json
import random

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, make_response
from flask_login import login_required, current_user, login_user, logout_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import create_user_db, check_password_strength, check_user_role_integrity
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Tag

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import Domain
import crawlers

r_cache = Flask_config.r_cache
r_serv_db = Flask_config.r_serv_db
r_serv_tags = Flask_config.r_serv_tags
bootstrap_label = Flask_config.bootstrap_label

# ============ BLUEPRINT ============
crawler_splash = Blueprint('crawler_splash', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/crawler/crawler_splash'))

# ============ VARIABLES ============



# ============ FUNCTIONS ============
def api_validator(api_response):
    if api_response:
        return Response(json.dumps(api_response[0], indent=2, sort_keys=True), mimetype='application/json'), api_response[1]

def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============
@crawler_splash.route("/crawlers/manual", methods=['GET'])
#@login_required
#@login_read_only
def manual():
    user_id = current_user.get_id()
    l_cookies = crawlers.api_get_cookies_list(user_id)
    return render_template("crawler_manual.html", crawler_enabled=True, l_cookies=l_cookies)


# add route : /crawlers/show_domain
@crawler_splash.route('/crawlers/showDomain', methods=['GET', 'POST'])
@login_required
@login_read_only
def showDomain():
    if request.method == 'POST':
        domain_name = request.form.get('in_show_domain')
        epoch = None
        port = None
    else:
        domain_name = request.args.get('domain')
        epoch = request.args.get('epoch')
        port = request.args.get('port')

    res = api_validator(Domain.api_verify_if_domain_exist(domain_name))
    if res:
        return res

    domain = Domain.Domain(domain_name, port=port)

    dict_domain = domain.get_domain_metadata()
    dict_domain['domain'] = domain_name
    if domain.domain_was_up():
        dict_domain = {**dict_domain, **domain.get_domain_correlation()}
        dict_domain['correlation_nb'] = Domain.get_domain_total_nb_correlation(dict_domain)
        dict_domain['origin_item'] = domain.get_domain_last_origin()
        dict_domain['tags'] = domain.get_domain_tags()
        dict_domain['tags_safe'] = Tag.is_tags_safe(dict_domain['tags'])
        dict_domain['history'] = domain.get_domain_history_with_status()
        dict_domain['crawler_history'] = domain.get_domain_items_crawled(items_link=True, epoch=epoch, item_screenshot=True, item_tag=True) # # TODO: handle multiple port
        if dict_domain['crawler_history']['items']:
            dict_domain['crawler_history']['random_item'] = random.choice(dict_domain['crawler_history']['items'])

    return render_template("showDomain.html", dict_domain=dict_domain, bootstrap_label=bootstrap_label,
                                modal_add_tags=Tag.get_modal_add_tags(dict_domain['domain'], object_type="domain"))

@crawler_splash.route('/domains/explorer/domain_type_post', methods=['POST'])
@login_required
@login_read_only
def domains_explorer_post_filter():
    domain_onion = request.form.get('domain_onion_switch')
    domain_regular = request.form.get('domain_regular_switch')
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')

    if date_from and date_to:
        date_from = date_from.replace('-', '')
        date_to = date_to.replace('-', '')
    else:
        date_from = None
        date_to = None

    if domain_onion and domain_regular:
        if date_from and date_to:
            return redirect(url_for('crawler_splash.domains_explorer_all', date_from=date_from, date_to=date_to))
        else:
            return redirect(url_for('crawler_splash.domains_explorer_all'))
    elif domain_regular:
        if date_from and date_to:
            return redirect(url_for('crawler_splash.domains_explorer_web', date_from=date_from, date_to=date_to))
        else:
            return redirect(url_for('crawler_splash.domains_explorer_web'))
    else:
        if date_from and date_to:
            return redirect(url_for('crawler_splash.domains_explorer_onion', date_from=date_from, date_to=date_to))
        else:
            return redirect(url_for('crawler_splash.domains_explorer_onion'))

@crawler_splash.route('/domains/explorer/all', methods=['GET'])
@login_required
@login_read_only
def domains_explorer_all():
    page = request.args.get('page')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    try:
        page = int(page)
    except:
        page = 1

    dict_data = Domain.get_domains_up_by_filers('all', page=page, date_from=date_from, date_to=date_to)
    return render_template("domain_explorer.html", dict_data=dict_data, bootstrap_label=bootstrap_label, domain_type='all')

@crawler_splash.route('/domains/explorer/onion', methods=['GET'])
@login_required
@login_read_only
def domains_explorer_onion():
    page = request.args.get('page')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    try:
        page = int(page)
    except:
        page = 1

    dict_data = Domain.get_domains_up_by_filers('onion', page=page, date_from=date_from, date_to=date_to)
    return render_template("domain_explorer.html", dict_data=dict_data, bootstrap_label=bootstrap_label, domain_type='onion')

@crawler_splash.route('/domains/explorer/web', methods=['GET'])
@login_required
@login_read_only
def domains_explorer_web():
    page = request.args.get('page')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    try:
        page = int(page)
    except:
        page = 1

    dict_data = Domain.get_domains_up_by_filers('regular', page=page, date_from=date_from, date_to=date_to)
    return render_template("domain_explorer.html", dict_data=dict_data, bootstrap_label=bootstrap_label, domain_type='regular')

@crawler_splash.route('/crawler/cookies/add', methods=['GET'])
#@login_required
#@login_analyst
def crawler_cookies_add():
    return render_template("add_cookies.html")

@crawler_splash.route('/crawler/cookies/add_post', methods=['POST'])
#@login_required
#@login_analyst
def crawler_cookies_add_post():
    user_id = current_user.get_id()

    description = request.form.get('description')
    level = request.form.get('level')
    if level:
        level = 1
    else:
        level = 0

    if 'file' in request.files:
        file = request.files['file']
        json_file = file.read().decode()
    else:
        json_file = '[]'

    # Get cookies to add
    l_manual_cookie = []
    l_invalid_cookie = []
    for obj_tuple in list(request.form):
        l_input = request.form.getlist(obj_tuple)
        if len(l_input) == 2:
            if l_input[0]: # cookie_name
                cookie_dict = {'name': l_input[0], 'value': l_input[1]}
                l_manual_cookie.append(cookie_dict)
            elif l_input[1]: # cookie_value
                    l_invalid_cookie.append({'name': '', 'value': l_input[1]})
    if l_invalid_cookie:
        return create_json_response({'error': 'invalid cookie', 'invalid fileds': l_invalid_cookie}, 400)

    cookies_uuid = crawler_splash.save_cookies(user_id, json_cookies=json_file, l_cookies=l_manual_cookie, level=level, description=description)
    return redirect(url_for('crawler_splash.crawler_cookies_all', cookies_uuid=cookies_uuid))

@crawler_splash.route('/crawler/cookies/all', methods=['GET'])
#@login_required
#@login_read_only
def crawler_cookies_all():
    user_id = current_user.get_id()
    user_cookies = crawlers.get_all_user_cookies_metadata(user_id)
    global_cookies = crawlers.get_all_global_cookies_metadata()
    return render_template("all_cookies.html", user_cookies=user_cookies, global_cookies=global_cookies)

@crawler_splash.route('/crawler/cookies/show', methods=['GET'])
#@login_required
#@login_read_only
def crawler_cookies_show():
    user_id = current_user.get_id()
    cookies_uuid = request.args.get('cookies_uuid')
    res = crawlers.api_get_cookies(cookies_uuid, user_id)
    if res[1] !=200:
        return create_json_response(res[0], res[1])
    cookies_json = json.dumps(res[0]['json_cookies'], indent=4, sort_keys=True)
    cookie_metadata = crawlers.get_cookies_metadata(cookies_uuid)
    return render_template("edit_cookies.html", cookie_metadata=cookie_metadata, cookies_json=cookies_json, manual_cookies=res[0]['manual_cookies'])
