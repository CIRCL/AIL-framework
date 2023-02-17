#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
"""

import os
import json
import random
import sys
import time
from datetime import datetime

from flask import render_template, jsonify, request, Blueprint, redirect, url_for, Response, send_file, abort
from flask_login import login_required, current_user, login_user, logout_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import login_admin, login_analyst, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import crawlers
from lib import Language
from lib.objects import Domains
from lib.objects.Items import Item
from lib import Tag

from packages import Date

# import Config_DB
bootstrap_label = Flask_config.bootstrap_label

# ============ BLUEPRINT ============
crawler_splash = Blueprint('crawler_splash', __name__,
                           template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/crawler/crawler_splash'))


# ============ VARIABLES ============


# ============ FUNCTIONS ============
def api_validator(message, code):
    if message and code:
        return Response(json.dumps(message, indent=2, sort_keys=True), mimetype='application/json'), code


def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code


# ============= ROUTES ==============
@crawler_splash.route("/crawlers/dashboard", methods=['GET'])
@login_required
@login_read_only
def crawlers_dashboard():
    is_manager_connected = crawlers.get_lacus_connection_metadata()
    crawlers_status = crawlers.get_crawler_capture_status()
    print(crawlers_status)
    crawlers_latest_stats = crawlers.get_crawlers_stats()
    print(crawlers_latest_stats)
    date = crawlers.get_current_date()
    return render_template("dashboard_crawler.html", date=date,
                           is_manager_connected=is_manager_connected,
                           crawlers_status=crawlers_status,
                           crawlers_latest_stats=crawlers_latest_stats)


@crawler_splash.route("/crawlers/crawler_dashboard_json", methods=['GET'])
@login_required
@login_read_only
def crawler_dashboard_json():
    crawlers_status = crawlers.get_crawler_capture_status()
    crawlers_latest_stats = crawlers.get_crawlers_stats()

    return jsonify({'crawlers_status': crawlers_status,
                    'stats': crawlers_latest_stats})


@crawler_splash.route("/crawlers/manual", methods=['GET'])
@login_required
@login_read_only
def manual():
    user_id = current_user.get_id()
    l_cookiejar = crawlers.api_get_cookiejars_selector(user_id)
    crawlers_types = crawlers.get_crawler_all_types()
    proxies = []  # TODO HANDLE PROXIES
    return render_template("crawler_manual.html",
                           is_manager_connected=crawlers.get_lacus_connection_metadata(),
                           crawlers_types=crawlers_types,
                           proxies=proxies,
                           l_cookiejar=l_cookiejar)


@crawler_splash.route("/crawlers/send_to_spider", methods=['POST'])
@login_required
@login_analyst
def send_to_spider():
    user_id = current_user.get_id()

    # POST val
    url = request.form.get('url_to_crawl')
    crawler_type = request.form.get('crawler_queue_type')
    proxy = request.form.get('proxy_name')
    auto_crawler = request.form.get('crawler_type')  # TODO Auto Crawler
    crawler_delta = request.form.get('crawler_epoch')  # TODO Auto Crawler
    screenshot = request.form.get('screenshot')
    har = request.form.get('har')
    depth_limit = request.form.get('depth_limit')
    cookiejar_uuid = request.form.get('cookiejar')

    if crawler_type == 'onion':
        proxy = 'force_tor'

    if cookiejar_uuid:
        if cookiejar_uuid == 'None':
            cookiejar_uuid = None
        else:
            cookiejar_uuid = cookiejar_uuid.rsplit(':')
            cookiejar_uuid = cookiejar_uuid[-1].replace(' ', '')

    data = {'url': url, 'depth': depth_limit, 'har': har, 'screenshot': screenshot}
    if proxy:
        data['proxy'] = proxy
    if cookiejar_uuid:
        data['cookiejar'] = cookiejar_uuid
    res = crawlers.api_add_crawler_task(data, user_id=user_id)

    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.manual'))


@crawler_splash.route("/crawlers/last/domains", methods=['GET'])
@login_required
@login_read_only
def crawlers_last_domains():
    domain_type = request.args.get('type')
    if domain_type not in crawlers.get_crawler_all_types():
        return jsonify({'error': 'Invalid domain type'}), 400

    # TODO STAT by EPOCH
    domains = []
    for domain_row in crawlers.get_last_crawled_domains(domain_type):
        domain, epoch = domain_row.split(':', 1)
        dom = Domains.Domain(domain)
        meta = dom.get_meta()
        meta['epoch'] = epoch
        meta['status_epoch'] = dom.is_up_by_epoch(epoch)
        domains.append(meta)
    crawler_stats = crawlers.get_crawlers_stats(domain_type=domain_type)

    now = datetime.now()
    date = now.strftime("%Y%m%d")
    date_string = '{}-{}-{}'.format(date[0:4], date[4:6], date[6:8])
    return render_template("last_crawled.html", domains=domains, type=domain_type,
                           is_manager_connected=crawlers.get_lacus_connection_metadata(),
                           date_from=date_string, date_to=date_string,
                           crawler_stats=crawler_stats)


@crawler_splash.route('/crawlers/last/domains/json')
@login_required
@login_read_only
def crawlers_last_domains_json():
    domain_type = request.args.get('type')
    if domain_type not in crawlers.get_crawler_all_types():
        return jsonify({'error': 'Invalid domain type'}), 400
    stats = []
    for date in Date.get_date_range(7):
        stats.append(crawlers.get_crawlers_stats_by_day(date, domain_type))
    return jsonify(stats)


#### Domains ####

# add route : /crawlers/show_domain
@crawler_splash.route('/crawlers/showDomain', methods=['GET', 'POST'])
@login_required
@login_read_only
def showDomain():
    if request.method == 'POST':
        domain_name = request.form.get('in_show_domain')
        epoch = None
    else:
        domain_name = request.args.get('domain')
        epoch = request.args.get('epoch')
        try:
            epoch = int(epoch)
        except (ValueError, TypeError):
            epoch = None

    domain = Domains.Domain(domain_name)
    if not domain.exists():
        abort(404)

    dict_domain = domain.get_meta(options=['last_origin', 'languages'])
    dict_domain['domain'] = domain.id
    if domain.was_up():
        dict_domain = {**dict_domain, **domain.get_correlations()}
        dict_domain['correlation_nb'] = len(dict_domain['decoded']) + len(dict_domain['username']) + len(
            dict_domain['pgp']) + len(dict_domain['cryptocurrency']) + len(dict_domain['screenshot'])
        dict_domain['tags_safe'] = Tag.is_tags_safe(dict_domain['tags'])
        dict_domain['history'] = domain.get_history(status=True)
        curr_epoch = None
        # Select valid epoch
        if epoch:
            for row in dict_domain['history']:
                if row['epoch'] == epoch:
                    curr_epoch = row['epoch']
                    break
        else:
            curr_epoch = -1
            for row in dict_domain['history']:
                if row['epoch'] > curr_epoch:
                    curr_epoch = row['epoch']
        dict_domain['epoch'] = curr_epoch
        dict_domain["date"] = time.strftime('%Y/%m/%d - %H:%M.%S', time.gmtime(curr_epoch))

        print(dict_domain['epoch'])

        dict_domain['crawler_history_items'] = []
        for item_id in domain.get_crawled_items_by_epoch(epoch):
            dict_domain['crawler_history_items'].append(Item(item_id).get_meta(options=['crawler']))
        if dict_domain['crawler_history_items']:
            dict_domain['random_item'] = random.choice(dict_domain['crawler_history_items'])

    return render_template("showDomain.html",
                           dict_domain=dict_domain, bootstrap_label=bootstrap_label,
                           modal_add_tags=Tag.get_modal_add_tags(dict_domain['domain'], object_type="domain"))


@crawler_splash.route('/crawlers/domain/download', methods=['GET'])
@login_required
@login_read_only
def crawlers_domain_download():
    domain = request.args.get('domain')
    epoch = request.args.get('epoch')
    try:
        epoch = int(epoch)
    except (ValueError, TypeError):
        epoch = None
    dom = Domains.Domain(domain)
    if not dom.exists():
        abort(404)
    zip_file = dom.get_download_zip(epoch=epoch)
    if not zip_file:
        abort(404)
    return send_file(zip_file, download_name=f'{dom.get_id()}.zip', as_attachment=True)


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

    # TODO SEARCH BOTH
    # if domain_onion and domain_regular:
    #     if date_from and date_to:
    #         return redirect(url_for('crawler_splash.domains_explorer_all', date_from=date_from, date_to=date_to))
    #     else:
    #         return redirect(url_for('crawler_splash.domains_explorer_all'))
    if domain_regular:
        if date_from and date_to:
            return redirect(url_for('crawler_splash.domains_explorer_web', date_from=date_from, date_to=date_to))
        else:
            return redirect(url_for('crawler_splash.domains_explorer_web'))
    else:
        if date_from and date_to:
            return redirect(url_for('crawler_splash.domains_explorer_onion', date_from=date_from, date_to=date_to))
        else:
            return redirect(url_for('crawler_splash.domains_explorer_onion'))


# TODO TEMP DISABLE
# @crawler_splash.route('/domains/explorer/all', methods=['GET'])
# @login_required
# @login_read_only
# def domains_explorer_all():
#     page = request.args.get('page')
#     date_from = request.args.get('date_from')
#     date_to = request.args.get('date_to')
#     try:
#         page = int(page)
#     except:
#         page = 1
#
#     dict_data = Domain.get_domains_up_by_filers('all', page=page, date_from=date_from, date_to=date_to)
#     return render_template("domain_explorer.html", dict_data=dict_data, bootstrap_label=bootstrap_label, domain_type='all')
#

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

    dict_data = Domains.get_domains_up_by_filers('onion', page=page, date_from=date_from, date_to=date_to)
    return render_template("domain_explorer.html", dict_data=dict_data, bootstrap_label=bootstrap_label,
                           domain_type='onion')


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

    dict_data = Domains.get_domains_up_by_filers('web', page=page, date_from=date_from, date_to=date_to)
    return render_template("domain_explorer.html", dict_data=dict_data, bootstrap_label=bootstrap_label,
                           domain_type='regular')


@crawler_splash.route('/domains/languages/all/json', methods=['GET'])
@login_required
@login_read_only
def domains_all_languages_json():
    # # TODO: get domain type
    iso = request.args.get('iso')
    domain_types = request.args.getlist('domain_types')
    return jsonify(Language.get_languages_from_iso(Domains.get_all_domains_languages(), sort=True))


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
    domains_types = Domains.sanitize_domains_types(domains_types)

    languages = request.args.getlist('languages')
    if languages:
        languages = languages[0].split(',')
    l_dict_domains = Domains.api_get_domains_by_languages(domains_types, Language.get_iso_from_languages(languages),
                                                          meta=True, page=page)
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
    domains_types = Domains.sanitize_domains_types(domains_types)

    l_dict_domains = Domains.api_search_domains_by_name(name, domains_types, meta=True, page=page)
    return render_template("domains/domains_result_list.html", template_folder='../../',
                           l_dict_domains=l_dict_domains, bootstrap_label=bootstrap_label,
                           domains_types=domains_types)


@crawler_splash.route('/domains/date', methods=['GET'])
@login_required
@login_analyst
def domains_search_date():
    # TODO sanitize type + date
    domain_type = request.args.get('type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    # page = request.args.get('page')

    date = Date.sanitise_date_range(date_from, date_to)
    domains_date = Domains.get_domains_by_daterange(date['date_from'], date['date_to'], domain_type)
    dict_domains = {}
    for d in domains_date:
        dict_domains[d] = Domains.get_domains_meta(domains_date[d])
    date_from = f"{date['date_from'][0:4]}-{date['date_from'][4:6]}-{date['date_from'][6:8]}"
    date_to = f"{date['date_to'][0:4]}-{date['date_to'][4:6]}-{date['date_to'][6:8]}"

    return render_template("domains_daterange.html", date_from=date_from, date_to=date_to,
                           bootstrap_label=bootstrap_label,
                           dict_domains=dict_domains, type=domain_type)


@crawler_splash.route('/domains/date/post', methods=['POST'])
@login_required
@login_analyst
def domains_search_date_post():
    domain_type = request.form.get('type')
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    return redirect(url_for('crawler_splash.domains_search_date', date_from=date_from, date_to=date_to, type=domain_type))


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
            if l_input[0]:  # Cookie Name
                cookie_dict = {'name': l_input[0], 'value': l_input[1]}
                l_manual_cookie.append(cookie_dict)
            elif l_input[1]:  # Cookie Value
                l_invalid_cookie.append({'name': '', 'value': l_input[1]})
    if l_invalid_cookie:
        return create_json_response({'error': 'invalid cookie', 'invalid fields': l_invalid_cookie}, 400)

    # Create Cookiejar
    cookiejar_uuid = crawlers.create_cookiejar(user_id, level=level, description=description)

    # Create Cookies
    if json_cookies: # TODO CHECK Import
        res = crawlers.api_import_cookies_from_json(user_id, cookiejar_uuid, json_cookies)
        if res:
            return create_json_response(res[0], res[1])
    for cookie_dict in l_manual_cookie:
        crawlers.api_create_cookie(user_id, cookiejar_uuid, cookie_dict)

    return redirect(url_for('crawler_splash.crawler_cookiejar_show', uuid=cookiejar_uuid))


@crawler_splash.route('/crawler/cookiejar/all', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_all():
    user_id = current_user.get_id()
    user_cookiejars = crawlers.get_cookiejars_meta_by_iterator(crawlers.get_cookiejars_user(user_id))
    global_cookiejars = crawlers.get_cookiejars_meta_by_iterator(crawlers.get_cookiejars_global())
    return render_template("all_cookiejar.html", user_cookiejar=user_cookiejars, global_cookiejar=global_cookiejars)


@crawler_splash.route('/crawler/cookiejar/show', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_show():
    user_id = current_user.get_id()
    cookiejar_uuid = request.args.get('uuid')

    res = crawlers.api_get_cookiejar(cookiejar_uuid, user_id)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    else:
        cookiejar_meta = res[0]

    return render_template("show_cookiejar.html", cookiejar_metadata=cookiejar_meta)


@crawler_splash.route('/crawler/cookie/delete', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_cookie_delete():
    user_id = current_user.get_id()
    cookie_uuid = request.args.get('uuid')

    res = crawlers.api_delete_cookie(user_id, cookie_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    else:
        cookiejar_uuid = res[0]['cookiejar_uuid']
    return redirect(url_for('crawler_splash.crawler_cookiejar_show', uuid=cookiejar_uuid))


@crawler_splash.route('/crawler/cookiejar/delete', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_delete():
    user_id = current_user.get_id()
    cookiejar_uuid = request.args.get('uuid')

    res = crawlers.api_delete_cookiejar(user_id, cookiejar_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.crawler_cookiejar_all'))


@crawler_splash.route('/crawler/cookiejar/edit', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_edit():
    user_id = current_user.get_id()
    cookiejar_uuid = request.args.get('uuid')
    description = request.args.get('description')

    res = crawlers.api_edit_cookiejar_description(user_id, cookiejar_uuid, description)
    return create_json_response(res[0], res[1])


@crawler_splash.route('/crawler/cookie/edit', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_cookie_edit():
    user_id = current_user.get_id()
    cookie_uuid = request.args.get('uuid')

    cookie_dict = crawlers.api_get_cookie(user_id, cookie_uuid)
    return render_template("edit_cookie.html", cookie_uuid=cookie_uuid, cookie_dict=cookie_dict)


@crawler_splash.route('/crawler/cookie/edit_post', methods=['POST'])
@login_required
@login_read_only
def crawler_cookiejar_cookie_edit_post():
    user_id = current_user.get_id()
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

    res = crawlers.api_edit_cookie(user_id, cookie_uuid, cookie_dict)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    cookie = crawlers.Cookie(cookie_uuid)
    cookiejar_uuid = cookie.get_cookiejar()
    return redirect(url_for('crawler_splash.crawler_cookiejar_show', uuid=cookiejar_uuid))


@crawler_splash.route('/crawler/cookiejar/cookie/add', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_cookie_add():
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

    res = crawlers.api_create_cookie(user_id, cookiejar_uuid, cookie_dict)
    if res[1] != 200:
        return create_json_response(res[0], res[1])

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
            res = crawlers.api_import_cookies_from_json(user_id, cookiejar_uuid, json_cookies)
            if res[1] != 200:
                return create_json_response(res[0], res[1])

            return redirect(url_for('crawler_splash.crawler_cookiejar_show', cookiejar_uuid=cookiejar_uuid))

    return redirect(url_for('crawler_splash.crawler_cookiejar_cookie_add', cookiejar_uuid=cookiejar_uuid))


# --- Cookiejar ---#


@crawler_splash.route('/crawler/settings/crawlers_to_lauch', methods=['GET', 'POST'])
@login_required
@login_admin
def crawler_splash_setings_crawlers_to_lauch():
    if request.method == 'POST':
        dict_splash_name = {}
        for crawler_name in list(request.form):
            dict_splash_name[crawler_name] = request.form.get(crawler_name)
        res = crawlers.api_set_nb_crawlers_to_launch(dict_splash_name)
        if res[1] != 200:
            return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
        else:
            return redirect(url_for('crawler_splash.crawler_splash_setings'))
    else:
        nb_crawlers_to_launch = crawlers.get_nb_crawlers_to_launch_ui()
        return render_template("settings_edit_crawlers_to_launch.html",
                               nb_crawlers_to_launch=nb_crawlers_to_launch)


@crawler_splash.route('/crawler/settings/relaunch_crawler', methods=['GET'])
@login_required
@login_admin
def crawler_splash_setings_relaunch_crawler():
    crawlers.relaunch_crawlers()
    return redirect(url_for('crawler_splash.crawler_splash_setings'))


##  - -  ##

#### LACUS ####

@crawler_splash.route('/crawler/settings', methods=['GET'])
@login_required
@login_analyst
def crawler_settings():
    lacus_url = crawlers.get_lacus_url()
    api_key = crawlers.get_hidden_lacus_api_key()

    is_manager_connected = crawlers.get_lacus_connection_metadata(force_ping=True)
    is_crawler_working = crawlers.is_test_ail_crawlers_successful()
    crawler_error_mess = crawlers.get_test_ail_crawlers_message()

    # TODO REGISTER PROXY
    # all_proxies = crawlers.get_all_proxies_metadata()

    # nb_crawlers_to_launch = crawlers.get_nb_crawlers_to_launch()
    # crawler_full_config = Config_DB.get_full_config_by_section('crawler')

    return render_template("settings_crawler.html",
                           is_manager_connected=is_manager_connected,
                           lacus_url=lacus_url, api_key=api_key,
                           # all_proxies=all_proxies,
                           # nb_crawlers_to_launch=nb_crawlers_to_launch,
                           is_crawler_working=is_crawler_working,
                           crawler_error_mess=crawler_error_mess,
                           )


@crawler_splash.route('/crawler/settings/crawler/manager', methods=['GET', 'POST'])
@login_required
@login_admin
def crawler_lacus_settings_crawler_manager():
    if request.method == 'POST':
        lacus_url = request.form.get('lacus_url')
        api_key = request.form.get('api_key')

        res = crawlers.api_save_lacus_url_key({'url': lacus_url, 'api_key': api_key})
        print(res)
        if res[1] != 200:
            return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
        else:
            return redirect(url_for('crawler_splash.crawler_settings'))
    else:
        lacus_url = crawlers.get_lacus_url()
        api_key = crawlers.get_lacus_api_key()
        return render_template("settings_edit_lacus_crawler.html", lacus_url=lacus_url, api_key=api_key)


@crawler_splash.route('/crawler/settings/crawler/test', methods=['GET'])
@login_required
@login_admin
def crawler_settings_crawler_test():
    crawlers.test_ail_crawlers()
    return redirect(url_for('crawler_splash.crawler_settings'))

# --- LACUS ---#
