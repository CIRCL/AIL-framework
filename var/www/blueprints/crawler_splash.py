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
from flask_login import login_required, current_user

sys.path.append('modules')
import Flask_config

# Import Role_Manager
from Role_Manager import login_admin, login_user, login_user_no_api, login_read_only

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import crawlers
from lib import Language
from lib.objects import Domains
from lib.objects.Items import Item
from lib.objects.Titles import Title
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
    if status_code == 403:
        abort(403)
    elif status_code == 404:
        abort(404)
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code


# ============= ROUTES ==============
@crawler_splash.route("/crawlers/dashboard", methods=['GET'])
@login_required
@login_read_only
def crawlers_dashboard():
    is_manager_connected = crawlers.get_lacus_connection_metadata()
    crawlers_status = crawlers.get_captures_status()
    crawlers_latest_stats = crawlers.get_crawlers_stats()
    # print(crawlers_status)
    # print(crawlers_latest_stats)
    date = crawlers.get_current_date()
    return render_template("dashboard_crawler.html", date=date,
                           is_manager_connected=is_manager_connected,
                           crawlers_status=crawlers_status,
                           filter_up=True,
                           crawlers_latest_stats=crawlers_latest_stats)


@crawler_splash.route("/crawlers/crawler_dashboard_json", methods=['GET'])
@login_required
@login_read_only
def crawler_dashboard_json():
    crawlers_status = crawlers.get_captures_status()
    crawlers_latest_stats = crawlers.get_crawlers_stats()
    # print(crawlers_status)

    return jsonify({'crawlers_status': crawlers_status,
                    'stats': crawlers_latest_stats})

@crawler_splash.route("/crawlers/dashboard/captures/delete", methods=['GET'])
@login_required
@login_admin
def crawlers_dashboard_captures_delete():
    crawlers.delete_captures()
    return redirect(url_for('crawler_splash.crawlers_dashboard'))


@crawler_splash.route("/crawlers/manual", methods=['GET'])
@login_required
@login_read_only
def manual():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    l_cookiejar = crawlers.api_get_cookiejars_selector(user_org, user_id)
    crawlers_types = crawlers.get_crawler_all_types()
    proxies = []  # TODO HANDLE PROXIES
    return render_template("crawler_manual.html",
                           is_manager_connected=crawlers.get_lacus_connection_metadata(),
                           crawlers_types=crawlers_types,
                           proxies=proxies,
                           l_cookiejar=l_cookiejar,
                           tags_selector_data=Tag.get_tags_selector_data())


@crawler_splash.route("/crawlers/send_to_spider", methods=['POST'])
@login_required
@login_user_no_api
def send_to_spider():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()

    # POST val
    url = request.form.get('url_to_crawl')
    urls = request.form.get('urls_to_crawl')
    if urls:
        urls = crawlers.extract_url_from_text(urls)
        l_cookiejar = crawlers.api_get_cookiejars_selector(user_org, user_id)
        crawlers_types = crawlers.get_crawler_all_types()
        proxies = []  # TODO HANDLE PROXIES
        return render_template("crawler_manual.html", urls=urls,
                               is_manager_connected=crawlers.get_lacus_connection_metadata(),
                               crawlers_types=crawlers_types,
                               proxies=proxies,
                               l_cookiejar=l_cookiejar,
                               tags_selector_data=Tag.get_tags_selector_data())

    urls = request.form.getlist('urls')
    crawler_type = request.form.get('crawler_queue_type')
    screenshot = request.form.get('screenshot')
    har = request.form.get('har')
    depth_limit = request.form.get('depth_limit')
    cookiejar_uuid = request.form.get('cookiejar')

    # TAGS
    tags = request.form.get("tags", [])
    taxonomies_tags = request.form.get('taxonomies_tags')
    if taxonomies_tags:
        try:
            taxonomies_tags = json.loads(taxonomies_tags)
        except:
            taxonomies_tags = []
    else:
        taxonomies_tags = []
    galaxies_tags = request.form.get('galaxies_tags')
    if galaxies_tags:
        try:
            galaxies_tags = json.loads(galaxies_tags)
        except:
            galaxies_tags = []
    else:
        galaxies_tags = []
    # custom tags
    if tags:
        tags = tags.split()
    else:
        tags = []
    escaped = []
    for tag in tags:
        escaped.append(tag)
    tags = escaped + taxonomies_tags + galaxies_tags

    # Frequency
    if request.form.get('crawler_scheduler'):
        frequency = request.form.get('frequency')
        if frequency == 'custom':
            months = request.form.get('frequency_months', 0)
            weeks = request.form.get('frequency_weeks', 0)
            days = request.form.get('frequency_days', 0)
            hours = request.form.get('frequency_hours', 0)
            minutes = request.form.get('frequency_minutes', 0)
            frequency = {'months': months, 'weeks': weeks, 'days': days, 'hours': hours, 'minutes': minutes}
    else:
        frequency = None

    # PROXY
    proxy = request.form.get('proxy_name')
    if proxy:
        res = crawlers.api_verify_proxy(proxy)
        if res[1] != 200:
            return create_json_response(res[0], res[1])
    elif crawler_type == 'onion':
        proxy = 'force_tor'

    if cookiejar_uuid:
        if cookiejar_uuid == 'None':
            cookiejar_uuid = None
        else:
            cookiejar_uuid = cookiejar_uuid.rsplit(':')
            cookiejar_uuid = cookiejar_uuid[-1].replace(' ', '')

    data = {'depth': depth_limit, 'har': har, 'screenshot': screenshot, 'frequency': frequency}
    if url:
        data['url']= url
    if urls:
        data['urls'] = urls
    if proxy:
        data['proxy'] = proxy
    if cookiejar_uuid:
        data['cookiejar'] = cookiejar_uuid
    if tags:
        data['tags'] = tags
    # print(data)
    res = crawlers.api_add_crawler_task(data, user_org, user_id=user_id)

    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.manual'))

@crawler_splash.route("/crawlers/domain_discovery", methods=['GET'])
@login_required
@login_user_no_api
def domain_discovery():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    domain = request.args.get('domain')
    if not crawlers.is_valid_onion_domain(domain):
        return create_json_response({'status': 'error', 'reason': 'Invalid onion domain'}, 400)

    data = {'depth': 1, 'har': True, 'screenshot': True, 'url': f'http://{domain}', 'proxy': 'force_tor'}
    res = crawlers.api_add_crawler_task(data, user_org, user_id=user_id)

    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.crawlers_dashboard'))

@crawler_splash.route("/crawlers/scheduler", methods=['GET'])
@login_required
@login_read_only
def scheduler_dashboard():
    schedulers = crawlers.get_schedulers_metas()
    # print(schedulers)
    # TODO list currently queued ?
    return render_template("crawler_scheduler_dashboard.html",
                           bootstrap_label=bootstrap_label,
                           schedulers=schedulers,
                           is_manager_connected=crawlers.get_lacus_connection_metadata())

@crawler_splash.route("/crawlers/schedule", methods=['GET'])
@login_required
@login_read_only
def schedule_show():
    schedule_uuid = request.args.get('uuid')
    schedule = crawlers.CrawlerSchedule(schedule_uuid)
    if not schedule.exists():
        abort(404)
    meta = schedule.get_meta(ui=True)
    return render_template("crawler_schedule_uuid.html",
                           bootstrap_label=bootstrap_label,
                           meta=meta)

@crawler_splash.route("/crawlers/schedule/delete", methods=['GET'])
@login_required
@login_admin
def schedule_delete():
    schedule_uuid = request.args.get('uuid')
    schedule = crawlers.CrawlerSchedule(schedule_uuid)
    if not schedule.exists():
        abort(404)
    res = crawlers.api_delete_schedule({'uuid': schedule_uuid})
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.scheduler_dashboard'))

@crawler_splash.route("/crawlers/blacklist", methods=['GET'])
@login_required
@login_admin
def crawler_blacklist():
    domain = request.args.get('domain')
    if domain:
        res = crawlers.api_blacklist_domain({'domain': domain})
        if res[1] != 200:
            if res[0].get('error') == 'domain already blacklisted':
                error_code = 2
            else:
                error_code = 1
        else:
            error_code = 0
            domain = None
    else:
        domain = None
        error_code = None
    blacklist = crawlers.get_blacklist()
    return render_template("crawler_blacklist.html", blacklist=blacklist,
                           domain=domain, error_code=error_code,
                           is_manager_connected=crawlers.get_lacus_connection_metadata())

@crawler_splash.route("/crawlers/blacklist/delete", methods=['GET'])
@login_required
@login_admin
def crawler_blacklist_delete():
    domain = request.args.get('domain')
    res = crawlers.api_unblacklist_domain({'domain': domain})
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.crawler_blacklist'))


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
        meta['last'] = datetime.fromtimestamp(int(epoch)).strftime("%Y/%m/%d %H:%M.%S")
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

@crawler_splash.route('/crawlers/last/domains/month/json')
@login_required
@login_read_only
def crawlers_last_domains_month_json():
    domain_type = request.args.get('type')
    if domain_type not in crawlers.get_crawler_all_types():
        return jsonify({'error': 'Invalid domain type'}), 400
    stats = crawlers.get_crawlers_stats_by_month(domain_type)
    return jsonify(stats)

@crawler_splash.route('/crawlers/last/domains/month/previous/json')
@login_required
@login_read_only
def crawlers_last_domains_previous_month_json():
    domain_type = request.args.get('type')
    if domain_type not in crawlers.get_crawler_all_types():
        return jsonify({'error': 'Invalid domain type'}), 400
    date = Date.get_previous_month_date()
    stats = crawlers.get_crawlers_stats_by_month(domain_type, date=date)
    return jsonify(stats)

@crawler_splash.route('/crawlers/last/domains/status/month/json')
@login_required
@login_read_only
def crawlers_last_domains_status_month_json():
    domain_type = request.args.get('type')
    if domain_type not in crawlers.get_crawler_all_types():
        return jsonify({'error': 'Invalid domain type'}), 400
    stats = crawlers.get_crawlers_stats_up_down_by_month(domain_type)
    data = []
    for key in stats:
        data.append({'name': key, 'value': stats[key]})
    return jsonify(data)


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
        dict_domain = {**dict_domain, **domain.get_correlations(filter_types=['cryptocurrency', 'decoded', 'pgp', 'screenshot', 'title'], unpack=True)}

        titles = []
        # for t in domain.get_correlation('title').get('title', []):
        #     title = Title(t[1:])
        #     titles.append(title.get_content())
        for t in dict_domain['title']:
            title = Title(t[1])
            titles.append({'id': title.id, 'content': title.get_content()})
        dict_domain['title'] = titles

        dict_domain['correlations_nb'] = domain.get_nb_correlations()
        nb = 0
        for correl_type in dict_domain['correlations_nb']:
            nb += dict_domain['correlations_nb'][correl_type]
        dict_domain['correlation_nb'] = nb
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

        # print(dict_domain['epoch'])

        dict_domain['crawler_history_items'] = []
        for item_id in domain.get_crawled_items_by_epoch(epoch):
            dict_domain['crawler_history_items'].append(Item(item_id).get_meta(options={'crawler'}))
        if dict_domain['crawler_history_items']:
            dict_domain['random_item'] = random.choice(dict_domain['crawler_history_items'])
    else:
        dict_domain['tags_safe'] = True

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

    if domain_onion and domain_regular:
        if date_from and date_to:
            return redirect(url_for('crawler_splash.domains_explorer_all', date_from=date_from, date_to=date_to))
        else:
            return redirect(url_for('crawler_splash.domains_explorer_all'))
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

    dict_data = Domains.get_domains_up_by_filers(['onion', 'web'], page=page, date_from=date_from, date_to=date_to)
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

    dict_data = Domains.get_domains_up_by_filers(['onion'], page=page, date_from=date_from, date_to=date_to)
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

    dict_data = Domains.get_domains_up_by_filers(['web'], page=page, date_from=date_from, date_to=date_to)
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
@login_user
def domains_search_name():
    name = request.args.get('name')
    page = request.args.get('page')
    try:
        page = int(page)
    except:
        page = 1

    if not name:
        return create_json_response({'error': 'Mandatory args name not provided'}, 400)
    name = crawlers.api_get_domain_from_url(name)

    domains_types = request.args.getlist('domain_types')
    if domains_types:
        domains_types = domains_types[0].split(',')
    domains_types = Domains.sanitize_domains_types(domains_types)

    dom = Domains.Domain(name)
    if dom.exists():
        return redirect(url_for('crawler_splash.showDomain', domain=dom.get_id()))
    else:
        if name.endswith('.onion') and len(name) == 62:
            send_to_crawler = True
        else:
            send_to_crawler = False

    l_dict_domains = Domains.api_search_domains_by_name(name, domains_types, meta=True, page=page)
    return render_template("domains/domains_result_list.html", template_folder='../../',
                           l_dict_domains=l_dict_domains, bootstrap_label=bootstrap_label,
                           send_to_crawler=send_to_crawler,
                           domains_types=domains_types)

@crawler_splash.route('/domains/today', methods=['GET'])
@login_required
@login_read_only
def domains_search_today():
    dom_types = request.args.get('type')
    down = bool(request.args.get('down', False))
    up = bool(request.args.get('up'))
    # page = request.args.get('page')

    all_types = Domains.get_all_domains_types()
    if dom_types == 'all':
        domain_types = all_types
    elif dom_types in Domains.get_all_domains_types():
        domain_types = [dom_types]
    else:
        dom_types = 'all'
        domain_types = all_types

    date = Date.get_today_date_str()
    domains_date = Domains.get_domains_dates_by_daterange(date, date, domain_types, up=up, down=down)
    dict_domains = {}
    for d in domains_date:
        dict_domains[d] = Domains.get_domains_meta(domains_date[d])
    date_from = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
    date_to = date_from

    return render_template("domains_daterange.html", date_from=date_from, date_to=date_to,
                           bootstrap_label=bootstrap_label,
                           filter_down=down, filter_up=up,
                           dict_domains=dict_domains, type=dom_types)

@crawler_splash.route('/domains/date', methods=['GET'])
@login_required
@login_read_only
def domains_search_date():
    # TODO sanitize type + date
    dom_types = request.args.get('type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    down = bool(request.args.get('down', False))
    up = bool(request.args.get('up'))
    # page = request.args.get('page')

    all_types = Domains.get_all_domains_types()
    if dom_types == 'all':
        domain_types = all_types
    elif dom_types in Domains.get_all_domains_types():
        domain_types = [dom_types]
    else:
        dom_types = 'all'
        domain_types = all_types

    date = Date.sanitise_date_range(date_from, date_to)
    domains_date = Domains.get_domains_dates_by_daterange(date['date_from'], date['date_to'], domain_types,
                                                          up=up, down=down)
    dict_domains = {}
    for d in domains_date:
        dict_domains[d] = Domains.get_domains_meta(domains_date[d])
    date_from = f"{date['date_from'][0:4]}-{date['date_from'][4:6]}-{date['date_from'][6:8]}"
    date_to = f"{date['date_to'][0:4]}-{date['date_to'][4:6]}-{date['date_to'][6:8]}"

    return render_template("domains_daterange.html", date_from=date_from, date_to=date_to,
                           bootstrap_label=bootstrap_label,
                           filter_down=down, filter_up=up,
                           dict_domains=dict_domains, type=dom_types)


@crawler_splash.route('/domains/date/post', methods=['POST'])
@login_required
@login_read_only
def domains_search_date_post():
    domain_type = request.form.get('type')
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    down = request.form.get('down')
    up = request.form.get('up')
    return redirect(url_for('crawler_splash.domains_search_date', date_from=date_from, date_to=date_to,
                            type=domain_type, down=down, up=up))


@crawler_splash.route('/domains/explorer/vanity', methods=['GET'])
@login_required
@login_read_only
def domains_explorer_vanity_clusters():
    nb_min = request.args.get('min', 4)
    if int(nb_min) < 0:
        nb_min = 4
    vanity_clusters = Domains.get_vanity_clusters(nb_min=nb_min)
    return render_template("explorer_vanity_clusters.html", vanity_clusters=vanity_clusters,
                           length=4)

@crawler_splash.route('/domains/explorer/vanity/explore', methods=['GET'])
@login_required
@login_read_only
def domains_explorer_vanity_explore():
    vanity = request.args.get('vanity')
    nb_min = request.args.get('min', 2)   # TODO SHOW DOMAINS OPTIONS + HARD CODED DOMAINS LIMIT FOR RENDER
    length = len(vanity)
    if int(nb_min) < 0:
        nb_min = 4
    vanity_clusters = Domains.get_vanity_cluster(vanity, len_vanity=length+1, nb_min=nb_min)
    vanity_domains = Domains.get_vanity_domains(vanity, len_vanity=length, meta=True)
    vanities_tree = []
    for i in range(4, length):
        vanities_tree.append(vanity[:i])
    if length == len(vanity):
        vanities_tree.append(vanity)
    return render_template("explorer_vanity_domains.html", vanity_clusters=vanity_clusters,
                           bootstrap_label=bootstrap_label, vanity=vanity, vanities_tree=vanities_tree,
                           vanity_domains=vanity_domains, length=length)

##--  --##


## Cookiejar ##
@crawler_splash.route('/crawler/cookiejar/add', methods=['GET'])
@login_required
@login_user_no_api
def crawler_cookiejar_add():
    return render_template("add_cookiejar.html")


@crawler_splash.route('/crawler/cookiejar/add_post', methods=['POST'])
@login_required
@login_user_no_api
def crawler_cookiejar_add_post():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()

    description = request.form.get('description')
    level = request.form.get('level')

    try:
        level = int(level)
    except TypeError:
        level = 1
    if level not in range(0, 3):
        level = 1

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
    cookiejar_uuid = crawlers.create_cookiejar(user_org, user_id, level=level, description=description)

    # Create Cookies
    if json_cookies: # TODO CHECK Import
        res = crawlers.api_import_cookies_from_json(user_org, user_id, user_role, cookiejar_uuid, json_cookies)
        if res:
            return create_json_response(res[0], res[1])
    for cookie_dict in l_manual_cookie:
        crawlers.api_create_cookie(user_org, user_id, user_role, cookiejar_uuid, cookie_dict)

    return redirect(url_for('crawler_splash.crawler_cookiejar_show', uuid=cookiejar_uuid))


@crawler_splash.route('/crawler/cookiejar/all', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_all():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_cookiejars = crawlers.get_cookiejars_meta_by_iterator(crawlers.get_cookiejars_user(user_id))
    org_cookiejars = crawlers.get_cookiejars_meta_by_iterator(crawlers.get_cookiejars_org(user_org))
    global_cookiejars = crawlers.get_cookiejars_meta_by_iterator(crawlers.get_cookiejars_global())
    return render_template("all_cookiejar.html", user_cookiejar=user_cookiejars,
                           org_cookiejar=org_cookiejars, global_cookiejar=global_cookiejars)

@crawler_splash.route('/crawler/cookiejar/all/admin', methods=['GET'])
@login_required
@login_admin
def crawler_cookiejar_all_admin():
    user_cookiejars = crawlers.get_cookiejars_meta_by_iterator(crawlers.get_cookiejars_users())
    org_cookiejars = crawlers.get_cookiejars_meta_by_iterator(crawlers.get_cookiejars_orgs())
    global_cookiejars = []
    return render_template("all_cookiejar.html", user_cookiejar=user_cookiejars,
                           org_cookiejar=org_cookiejars, global_cookiejar=global_cookiejars)


@crawler_splash.route('/crawler/cookiejar/show', methods=['GET'])
@login_required
@login_read_only
def crawler_cookiejar_show():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    cookiejar_uuid = request.args.get('uuid')

    res = crawlers.api_get_cookiejar(user_org, user_id, user_role, cookiejar_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    else:
        cookiejar_meta = res[0]

    return render_template("show_cookiejar.html", cookiejar_metadata=cookiejar_meta)


@crawler_splash.route('/crawler/cookie/delete', methods=['GET'])
@login_required
@login_user_no_api
def crawler_cookiejar_cookie_delete():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    cookie_uuid = request.args.get('uuid')

    res = crawlers.api_delete_cookie(user_org, user_id, user_role, cookie_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    else:
        cookiejar_uuid = res[0]['cookiejar_uuid']
    return redirect(url_for('crawler_splash.crawler_cookiejar_show', uuid=cookiejar_uuid))


@crawler_splash.route('/crawler/cookiejar/delete', methods=['GET'])
@login_required
@login_user_no_api
def crawler_cookiejar_delete():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    cookiejar_uuid = request.args.get('uuid')

    res = crawlers.api_delete_cookiejar(user_org, user_id, user_role, cookiejar_uuid)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('crawler_splash.crawler_cookiejar_all'))


@crawler_splash.route('/crawler/cookiejar/edit', methods=['GET'])
@login_required
@login_user_no_api
def crawler_cookiejar_edit():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    cookiejar_uuid = request.args.get('uuid')
    description = request.args.get('description')

    res = crawlers.api_edit_cookiejar_description(user_org, user_id, user_role, cookiejar_uuid, description)
    return create_json_response(res[0], res[1])


@crawler_splash.route('/crawler/cookie/edit', methods=['GET'])
@login_required
@login_user_no_api
def crawler_cookiejar_cookie_edit():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    cookie_uuid = request.args.get('uuid')

    cookie_dict = crawlers.api_get_cookie(user_org, user_id, user_role, cookie_uuid)
    return render_template("edit_cookie.html", cookie_uuid=cookie_uuid, cookie_dict=cookie_dict)


@crawler_splash.route('/crawler/cookie/edit_post', methods=['POST'])
@login_required
@login_user_no_api
def crawler_cookiejar_cookie_edit_post():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
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

    res = crawlers.api_edit_cookie(user_org, user_id, user_role, cookie_uuid, cookie_dict)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    cookie = crawlers.Cookie(cookie_uuid)
    cookiejar_uuid = cookie.get_cookiejar()
    return redirect(url_for('crawler_splash.crawler_cookiejar_show', uuid=cookiejar_uuid))


@crawler_splash.route('/crawler/cookiejar/cookie/add', methods=['GET'])
@login_required
@login_user_no_api
def crawler_cookiejar_cookie_add():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    user_role = current_user.get_role()
    cookiejar_uuid = request.args.get('uuid')
    res = crawlers.api_check_cookiejar_access_acl(cookiejar_uuid, user_org, user_id, user_role, action='edit')
    if res:
        return create_json_response(res[0], res[1])
    return render_template("add_cookie.html", cookiejar_uuid=cookiejar_uuid)


@crawler_splash.route('/crawler/cookiejar/cookie/manual_add_post', methods=['POST'])
@login_required
@login_user_no_api
def crawler_cookiejar_cookie_manual_add_post():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    is_admin = current_user.is_admin()
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

    res = crawlers.api_create_cookie(user_org, user_id, is_admin, cookiejar_uuid, cookie_dict)
    if res[1] != 200:
        return create_json_response(res[0], res[1])

    return redirect(url_for('crawler_splash.crawler_cookiejar_show', uuid=cookiejar_uuid))


@crawler_splash.route('/crawler/cookiejar/cookie/json_add_post', methods=['POST'])
@login_required
@login_user_no_api
def crawler_cookiejar_cookie_json_add_post():
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    is_admin = current_user.is_admin()
    cookiejar_uuid = request.form.get('cookiejar_uuid')

    if 'file' in request.files:
        file = request.files['file']
        json_cookies = file.read().decode()
        if json_cookies:
            res = crawlers.api_import_cookies_from_json(user_org, user_id, is_admin, cookiejar_uuid, json_cookies)
            if res[1] != 200:
                return create_json_response(res[0], res[1])

            return redirect(url_for('crawler_splash.crawler_cookiejar_show', cookiejar_uuid=cookiejar_uuid))

    return redirect(url_for('crawler_splash.crawler_cookiejar_cookie_add', cookiejar_uuid=cookiejar_uuid))


# --- Cookiejar ---#

#### LACUS ####

@crawler_splash.route('/crawler/settings', methods=['GET'])
@login_required
@login_admin
def crawler_settings():
    lacus_url = crawlers.get_lacus_url()
    api_key = crawlers.get_hidden_lacus_api_key()
    nb_captures = crawlers.get_crawler_max_captures()

    is_manager_connected = crawlers.get_lacus_connection_metadata(force_ping=True)
    is_crawler_working = crawlers.is_test_ail_crawlers_successful()
    crawler_error_mess = crawlers.get_test_ail_crawlers_message()

    is_onion_filter_enabled = crawlers.is_onion_filter_enabled(cache=False)
    is_onion_filter_unknown = crawlers.is_onion_filter_unknown(cache=False)

    # TODO REGISTER PROXY
    # all_proxies = crawlers.get_all_proxies_metadata()

    # crawler_full_config = Config_DB.get_full_config_by_section('crawler')

    return render_template("settings_crawler.html",
                           is_manager_connected=is_manager_connected,
                           lacus_url=lacus_url, api_key=api_key,
                           nb_captures=nb_captures,
                           # all_proxies=all_proxies,
                           is_crawler_working=is_crawler_working,
                           crawler_error_mess=crawler_error_mess,
                           is_onion_filter_enabled=is_onion_filter_enabled,
                           is_onion_filter_unknown=is_onion_filter_unknown
                           )


@crawler_splash.route('/crawler/settings/crawler/manager', methods=['GET', 'POST'])
@login_required
@login_admin
def crawler_lacus_settings_crawler_manager():
    if request.method == 'POST':
        lacus_url = request.form.get('lacus_url')
        api_key = request.form.get('api_key')

        res = crawlers.api_save_lacus_url_key({'url': lacus_url, 'api_key': api_key})
        # print(res)
        if res[1] != 200:
            return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]
        else:
            return redirect(url_for('crawler_splash.crawler_settings'))
    else:
        lacus_url = crawlers.get_lacus_url()
        api_key = crawlers.get_lacus_api_key()
        return render_template("settings_edit_lacus_crawler.html", lacus_url=lacus_url, api_key=api_key)

@crawler_splash.route('/crawler/settings/crawlers_to_launch', methods=['GET', 'POST'])
@login_required
@login_admin
def crawler_settings_crawlers_to_launch():
    if request.method == 'POST':
        nb_captures = request.form.get('nb_captures')
        res = crawlers.api_set_crawler_max_captures({'nb': nb_captures})
        if res[1] != 200:
            return create_json_response(res[0], res[1])
        else:
            return redirect(url_for('crawler_splash.crawler_settings'))
    else:
        nb_captures = crawlers.get_crawler_max_captures()
        return render_template("settings_edit_crawlers_to_launch.html",
                               nb_captures=nb_captures)


@crawler_splash.route('/crawler/settings/crawler/test', methods=['GET'])
@login_required
@login_admin
def crawler_settings_crawler_test():
    crawlers.test_ail_crawlers()
    return redirect(url_for('crawler_splash.crawler_settings'))

@crawler_splash.route('/crawler/settings/crawler/filter_unsafe_onion', methods=['GET'])
@login_required
@login_admin
def crawler_filter_unsafe_onion():
    filter_unsafe_onion = request.args.get('state')
    if filter_unsafe_onion == 'enable':
        filter_unsafe_onion = True
    else:
        filter_unsafe_onion = False
    crawlers.change_onion_filter_state(filter_unsafe_onion)
    return redirect(url_for('crawler_splash.crawler_settings'))

@crawler_splash.route('/crawler/settings/crawler/filter_unknown_onion', methods=['GET'])
@login_required
@login_admin
def crawler_filter_unknown_onion():
    filter_unknown_onion = request.args.get('state')
    if filter_unknown_onion == 'enable':
        filter_unknown_onion = True
    else:
        filter_unknown_onion = False
    crawlers.change_onion_filter_unknown_state(filter_unknown_onion)
    return redirect(url_for('crawler_splash.crawler_settings'))


# --- LACUS ---#
