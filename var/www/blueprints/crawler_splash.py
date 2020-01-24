#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys
import json
import random

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response
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

# ============= ROUTES ==============
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

    dict_data = Domain.domains_up_by_page('regular', page=page)
    return render_template("domain_explorer.html", dict_data=dict_data, bootstrap_label=bootstrap_label, domain_type='regular')
