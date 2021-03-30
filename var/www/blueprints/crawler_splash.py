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
import crawlers
import Domain
import Language

import Config_DB

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
@crawler_splash.route("/crawlers/dashboard", methods=['GET'])
@login_required
@login_read_only
def crawlers_dashboard():
    # # TODO:  get splash manager status
    is_manager_connected = crawlers.get_splash_manager_connection_metadata()
    all_splash_crawler_status = crawlers.get_all_spash_crawler_status()
    splash_crawlers_latest_stats = crawlers.get_splash_crawler_latest_stats()
    date = crawlers.get_current_date()

    return render_template("dashboard_splash_crawler.html", all_splash_crawler_status = all_splash_crawler_status,
                                is_manager_connected=is_manager_connected, date=date,
                                splash_crawlers_latest_stats=splash_crawlers_latest_stats)

@crawler_splash.route("/crawlers/crawler_dashboard_json", methods=['GET'])
@login_required
@login_read_only
def crawler_dashboard_json():

    all_splash_crawler_status = crawlers.get_all_spash_crawler_status()
    splash_crawlers_latest_stats = crawlers.get_splash_crawler_latest_stats()

    return jsonify({'all_splash_crawler_status': all_splash_crawler_status,
                        'splash_crawlers_latest_stats':splash_crawlers_latest_stats})

@crawler_splash.route("/crawlers/manual", methods=['GET'])
@login_required
@login_read_only
def manual():
    user_id = current_user.get_id()
    l_cookiejar = crawlers.api_get_cookies_list_select(user_id)
    all_crawlers_types = crawlers.get_all_crawlers_queues_types()
    all_splash_name = crawlers.get_all_crawlers_to_launch_splash_name()
    return render_template("crawler_manual.html",
                                is_manager_connected=crawlers.get_splash_manager_connection_metadata(),
                                all_crawlers_types=all_crawlers_types,
                                all_splash_name=all_splash_name,
                                l_cookiejar=l_cookiejar)

@crawler_splash.route("/crawlers/send_to_spider", methods=['POST'])
@login_required
@login_analyst
def send_to_spider():
    user_id = current_user.get_id()

    # POST val
    url = request.form.get('url_to_crawl')
    crawler_type = request.form.get('crawler_queue_type')
    splash_name = request.form.get('splash_name')
    auto_crawler = request.form.get('crawler_type')
    crawler_delta = request.form.get('crawler_epoch')
    screenshot = request.form.get('screenshot')
    har = request.form.get('har')
    depth_limit = request.form.get('depth_limit')
    max_pages = request.form.get('max_pages')
    cookiejar_uuid = request.form.get('cookiejar')

    if splash_name:
        crawler_type = splash_name

    if cookiejar_uuid:
        if cookiejar_uuid == 'None':
            cookiejar_uuid = None
        else:
            cookiejar_uuid = cookiejar_uuid.rsplit(':')
            cookiejar_uuid = cookiejar_uuid[-1].replace(' ', '')

    res = crawlers.api_create_crawler_task(user_id, url, screenshot=screenshot, har=har, depth_limit=depth_limit, max_pages=max_pages,
                                                    crawler_type=crawler_type,
                                                    auto_crawler=auto_crawler, crawler_delta=crawler_delta, cookiejar_uuid=cookiejar_uuid)
    if res:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.manual'))


#### Domains ####

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
        dict_domain['father'] = domain.get_domain_father()
        dict_domain['languages'] = Language.get_languages_from_iso(domain.get_domain_languages(), sort=True)
        dict_domain['tags'] = domain.get_domain_tags()
        dict_domain['tags_safe'] = Tag.is_tags_safe(dict_domain['tags'])
        dict_domain['history'] = domain.get_domain_history_with_status()
        dict_domain['crawler_history'] = domain.get_domain_items_crawled(items_link=True, epoch=epoch, item_screenshot=True, item_tag=True) # # TODO: handle multiple port
        if dict_domain['crawler_history'].get('items', []):
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

@crawler_splash.route('/domains/languages/all/json', methods=['GET'])
@login_required
@login_read_only
def domains_all_languages_json():
    # # TODO: get domain type
    iso = request.args.get('iso')
    domain_types = request.args.getlist('domain_types')
    return jsonify(Language.get_languages_from_iso(Domain.get_all_domains_languages(), sort=True))

@crawler_splash.route('/domains/languages/search_get', methods=['GET'])
@login_required
@login_read_only
def domains_search_languages_get():
    page = request.args.get('page')
    try:
        page = int(page)
    except:
        page = 1
    domains_types = request.args.getlist('domain_types')
    if domains_types:
        domains_types = domains_types[0].split(',')
    languages = request.args.getlist('languages')
    if languages:
        languages = languages[0].split(',')
    l_dict_domains = Domain.api_get_domains_by_languages(domains_types, Language.get_iso_from_languages(languages), domains_metadata=True, page=page)
    return render_template("domains/domains_filter_languages.html", template_folder='../../',
                                l_dict_domains=l_dict_domains, bootstrap_label=bootstrap_label,
                                current_languages=languages, domains_types=domains_types)

@crawler_splash.route('/domains/name/search', methods=['GET'])
@login_required
@login_analyst
def domains_search_name():
    name = request.args.get('name')
    page = request.args.get('page')
    try:
        page = int(page)
    except:
        page = 1
    domains_types = request.args.getlist('domain_types')
    if domains_types:
        domains_types = domains_types[0].split(',')

    l_dict_domains = Domain.api_search_domains_by_name(name, domains_types, domains_metadata=True, page=page)
    return render_template("domains/domains_result_list.html", template_folder='../../',
                                l_dict_domains=l_dict_domains, bootstrap_label=bootstrap_label,
                                domains_types=domains_types)

##--  --##


## Cookiejar ##
@crawler_splash.route('/crawler/cookiejar/add', methods=['GET'])
@login_required
@login_analyst
def crawler_cookiejar_add():
    return render_template("add_cookiejar.html")

@crawler_splash.route('/crawler/cookiejar/add_post', methods=['POST'])
@login_required
@login_analyst
def crawler_cookiejar_add_post():
    user_id = current_user.get_id()

    description = request.form.get('description')
    level = request.form.get('level')
    if level:
        level = 1
    else:
        level = 0

    if 'file' in request.files:
        file = request.files['file']
        json_cookies = file.read().decode()
    else:
        json_cookies = None

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

    cookiejar_uuid = crawlers.create_cookiejar(user_id, level=level, description=description)
    if json_cookies:
        res = crawlers.api_import_cookies_from_json(json_cookies, cookiejar_uuid)
        if res:
            return create_json_response(res[0], res[1])
    if l_manual_cookie:
        crawlers.add_cookies_to_cookiejar(cookiejar_uuid, l_manual_cookie)

    return redirect(url_for('crawler_splash.crawler_cookiejar_show', cookiejar_uuid=cookiejar_uuid))

@crawler_splash.route('/crawler/cookiejar/all', methods=['GET'])
#@login_required
#@login_read_only
def crawler_cookiejar_all():
    user_id = current_user.get_id()
    user_cookiejar = crawlers.get_cookiejar_metadata_by_iterator(crawlers.get_user_cookiejar(user_id))
    global_cookiejar = crawlers.get_cookiejar_metadata_by_iterator(crawlers.get_global_cookiejar())
    return render_template("all_cookiejar.html", user_cookiejar=user_cookiejar, global_cookiejar=global_cookiejar)

@crawler_splash.route('/crawler/cookiejar/show', methods=['GET'])
#@login_required
#@login_read_only
def crawler_cookiejar_show():
    user_id = current_user.get_id()
    cookiejar_uuid = request.args.get('cookiejar_uuid')

    res = crawlers.api_get_cookiejar_cookies_with_uuid(cookiejar_uuid, user_id)
    if res[1] !=200:
        return create_json_response(res[0], res[1])

    cookiejar_metadata = crawlers.get_cookiejar_metadata(cookiejar_uuid, level=False)

    l_cookies = []
    l_cookie_uuid = []
    for cookie in res[0]:
        l_cookies.append(json.dumps(cookie[0], indent=4, sort_keys=True))
        l_cookie_uuid.append(cookie[1])
    return render_template("show_cookiejar.html", cookiejar_uuid=cookiejar_uuid, cookiejar_metadata=cookiejar_metadata,
                                        l_cookies=l_cookies, l_cookie_uuid=l_cookie_uuid)

@crawler_splash.route('/crawler/cookiejar/cookie/delete', methods=['GET'])
#@login_required
#@login_read_only
def crawler_cookiejar_cookie_delete():
    user_id = current_user.get_id()
    cookiejar_uuid = request.args.get('cookiejar_uuid')
    cookie_uuid = request.args.get('cookie_uuid')

    res = crawlers.api_delete_cookie_from_cookiejar(user_id, cookiejar_uuid, cookie_uuid)
    if res[1] !=200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.crawler_cookiejar_show', cookiejar_uuid=cookiejar_uuid))

@crawler_splash.route('/crawler/cookiejar/delete', methods=['GET'])
#@login_required
#@login_read_only
def crawler_cookiejar_delete():
    user_id = current_user.get_id()
    cookiejar_uuid = request.args.get('cookiejar_uuid')

    res = crawlers.api_delete_cookie_jar(user_id, cookiejar_uuid)
    if res[1] !=200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.crawler_cookiejar_all'))

@crawler_splash.route('/crawler/cookiejar/edit', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_edit():
    user_id = current_user.get_id()
    cookiejar_uuid = request.args.get('cookiejar_uuid')
    description = request.args.get('description')

    res = crawlers.api_edit_cookiejar_description(user_id, cookiejar_uuid, description)
    return create_json_response(res[0], res[1])

@crawler_splash.route('/crawler/cookiejar/cookie/edit', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_cookie_edit():
    user_id = current_user.get_id()
    cookiejar_uuid = request.args.get('cookiejar_uuid')
    cookie_uuid = request.args.get('cookie_uuid')

    cookie_dict = crawlers.get_cookie_dict(cookie_uuid)
    return render_template("edit_cookie.html", cookiejar_uuid=cookiejar_uuid, cookie_uuid=cookie_uuid, cookie_dict=cookie_dict)

@crawler_splash.route('/crawler/cookiejar/cookie/edit_post', methods=['POST'])
@login_required
@login_read_only
def crawler_cookiejar_cookie_edit_post():
    user_id = current_user.get_id()
    cookiejar_uuid = request.form.get('cookiejar_uuid')
    cookie_uuid = request.form.get('cookie_uuid')
    name = request.form.get('name')
    value = request.form.get('value')
    domain = request.form.get('domain')
    path = request.form.get('path')
    httpOnly = request.form.get('httpOnly')
    secure = request.form.get('secure')

    cookie_dict = {'name': name, 'value': value}
    if domain:
        cookie_dict['domain'] = domain
    if path:
        cookie_dict['path'] = path
    if httpOnly:
        cookie_dict['httpOnly'] = True
    if secure:
        cookie_dict['secure'] = True

    res = crawlers.api_edit_cookie(user_id, cookiejar_uuid, cookie_uuid, cookie_dict)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.crawler_cookiejar_show', cookiejar_uuid=cookiejar_uuid))

@crawler_splash.route('/crawler/cookiejar/cookie/add', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_cookie_add():
    user_id = current_user.get_id()
    cookiejar_uuid = request.args.get('cookiejar_uuid')
    return render_template("add_cookie.html", cookiejar_uuid=cookiejar_uuid)

@crawler_splash.route('/crawler/cookiejar/cookie/manual_add_post', methods=['POST'])
@login_required
@login_read_only
def crawler_cookiejar_cookie_manual_add_post():
    user_id = current_user.get_id()
    cookiejar_uuid = request.form.get('cookiejar_uuid')
    name = request.form.get('name')
    value = request.form.get('value')
    domain = request.form.get('domain')
    path = request.form.get('path')
    httpOnly = request.form.get('httpOnly')
    secure = request.form.get('secure')

    cookie_dict = {'name': name, 'value': value}
    if domain:
        cookie_dict['domain'] = domain
    if path:
        cookie_dict['path'] = path
    if httpOnly:
        cookie_dict['httpOnly'] = True
    if secure:
        cookie_dict['secure'] = True

    return redirect(url_for('crawler_splash.crawler_cookiejar_show', cookiejar_uuid=cookiejar_uuid))

@crawler_splash.route('/crawler/cookiejar/cookie/json_add_post', methods=['POST'])
@login_required
@login_read_only
def crawler_cookiejar_cookie_json_add_post():
    user_id = current_user.get_id()
    cookiejar_uuid = request.form.get('cookiejar_uuid')

    if 'file' in request.files:
        file = request.files['file']
        json_cookies = file.read().decode()
        if json_cookies:
            res = crawlers.api_import_cookies_from_json(json_cookies, cookiejar_uuid)
            return redirect(url_for('crawler_splash.crawler_cookiejar_show', cookiejar_uuid=cookiejar_uuid))

    return redirect(url_for('crawler_splash.crawler_cookiejar_cookie_add', cookiejar_uuid=cookiejar_uuid))

@crawler_splash.route('/crawler/settings', methods=['GET'])
@login_required
@login_analyst
def crawler_splash_setings():
    all_proxies = crawlers.get_all_proxies_metadata()
    all_splash = crawlers.get_all_splash_crawler_metadata()
    splash_manager_url = crawlers.get_splash_manager_url()
    api_key = crawlers.get_hidden_splash_api_key()
    is_manager_connected = crawlers.get_splash_manager_connection_metadata(force_ping=True)

    nb_crawlers_to_launch = crawlers.get_nb_crawlers_to_launch()
    #crawler_full_config = Config_DB.get_full_config_by_section('crawler')
    is_crawler_working = crawlers.is_test_ail_crawlers_successful()
    crawler_error_mess = crawlers.get_test_ail_crawlers_message()

    return render_template("settings_splash_crawler.html",
                                is_manager_connected=is_manager_connected,
                                splash_manager_url=splash_manager_url, api_key=api_key,
                                all_splash=all_splash, all_proxies=all_proxies,
                                nb_crawlers_to_launch=nb_crawlers_to_launch,
                                is_crawler_working=is_crawler_working,
                                crawler_error_mess=crawler_error_mess,
                                #crawler_full_config=crawler_full_config
                                )

@crawler_splash.route('/crawler/settings/crawler_manager', methods=['GET', 'POST'])
@login_required
@login_admin
def crawler_splash_setings_crawler_manager():
    if request.method == 'POST':
        splash_manager_url = request.form.get('splash_manager_url')
        api_key = request.form.get('api_key')

        res = crawlers.api_save_splash_manager_url_api({'url':splash_manager_url, 'api_key':api_key})
        if res[1] != 200:
            return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
        else:
            return redirect(url_for('crawler_splash.crawler_splash_setings'))
    else:
        splash_manager_url = crawlers.get_splash_manager_url()
        api_key = crawlers.get_splash_api_key()
        return render_template("settings_edit_splash_crawler_manager.html",
                                    splash_manager_url=splash_manager_url, api_key=api_key)

@crawler_splash.route('/crawler/settings/crawlers_to_lauch', methods=['GET', 'POST'])
@login_required
@login_admin
def crawler_splash_setings_crawlers_to_lauch():
    if request.method == 'POST':
        dict_splash_name = {}
        for crawler_name in list(request.form):
            dict_splash_name[crawler_name]= request.form.get(crawler_name)
        res = crawlers.api_set_nb_crawlers_to_launch(dict_splash_name)
        if res[1] != 200:
            return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
        else:
            return redirect(url_for('crawler_splash.crawler_splash_setings'))
    else:
        nb_crawlers_to_launch = crawlers.get_nb_crawlers_to_launch_ui()
        return render_template("settings_edit_crawlers_to_launch.html",
                                    nb_crawlers_to_launch=nb_crawlers_to_launch)

@crawler_splash.route('/crawler/settings/test_crawler', methods=['GET'])
@login_required
@login_admin
def crawler_splash_setings_test_crawler():
    crawlers.test_ail_crawlers()
    return redirect(url_for('crawler_splash.crawler_splash_setings'))

@crawler_splash.route('/crawler/settings/relaunch_crawler', methods=['GET'])
@login_required
@login_admin
def crawler_splash_setings_relaunch_crawler():
    crawlers.relaunch_crawlers()
    return redirect(url_for('crawler_splash.crawler_splash_setings'))

##  - -  ##
