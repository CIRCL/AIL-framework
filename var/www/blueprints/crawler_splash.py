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
from Role_Manager import login_admin, login_analyst

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
from Tag import get_modal_add_tags

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
@crawler_splash.route('/crawlers/showDomain')
#@login_required
#@login_analyst
def showDomain():
    domain_name = request.args.get('domain')
    epoch = request.args.get('epoch')
    port = request.args.get('port')

    res = api_validator(Domain.api_verify_if_domain_exist(domain_name))
    if res:
        return res

    domain = Domain.Domain(domain_name, port=port)

    dict_domain = domain.get_domain_metadata()
    dict_domain['domain'] = domain_name
    if domain.is_domain_up():
        dict_domain = {**dict_domain, **domain.get_domain_correlation()}
        dict_domain['tags'] = domain.get_domain_tags()
        dict_domain['history'] = domain.get_domain_history_with_status()
        dict_domain['crawler_history'] = domain.get_domain_items_crawled(items_link=True, epoch=epoch, item_screenshot=True, item_tag=True) # # TODO: handle multiple port
        dict_domain['crawler_history']['random_item'] = random.choice(dict_domain['crawler_history']['items'])

    return render_template("showDomain.html", dict_domain=dict_domain, bootstrap_label=bootstrap_label,
                                modal_add_tags=get_modal_add_tags(dict_domain['domain'], tag_type="domain"))
