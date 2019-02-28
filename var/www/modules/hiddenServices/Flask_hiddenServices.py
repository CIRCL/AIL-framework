#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import datetime
import sys
import os
import json
from pyfaup.faup import Faup
from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for

from Date import Date
from HiddenServices import HiddenServices

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_cache = Flask_config.r_cache
r_serv_onion = Flask_config.r_serv_onion
r_serv_metadata = Flask_config.r_serv_metadata
bootstrap_label = Flask_config.bootstrap_label
PASTES_FOLDER = Flask_config.PASTES_FOLDER

hiddenServices = Blueprint('hiddenServices', __name__, template_folder='templates')

faup = Faup()
list_types=['onion', 'regular']
dic_type_name={'onion':'Onion', 'regular':'Website'}

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

def substract_date(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from # timedelta
    l_date = []
    for i in range(delta.days + 1):
        date = date_from + datetime.timedelta(i)
        l_date.append( date.strftime('%Y%m%d') )
    return l_date

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

def is_valid_domain(domain):
    faup.decode(domain)
    domain_unpack = faup.get()
    if domain_unpack['tld'] is not None and domain_unpack['scheme'] is None and domain_unpack['port'] is None and domain_unpack['query_string'] is None:
        return True
    else:
        return False

def get_onion_status(domain, date):
    if r_serv_onion.sismember('onion_up:'+date , domain):
        return True
    else:
        return False

def get_domain_type(domain):
    type_id = domain.split(':')[-1]
    if type_id == 'onion':
        return 'onion'
    else:
        return 'regular'

def get_last_domains_crawled(type):
    return r_serv_onion.lrange('last_{}'.format(type), 0 ,-1)

def get_stats_last_crawled_domains(type, date):
    statDomains = {}
    statDomains['domains_up'] = r_serv_onion.scard('{}_up:{}'.format(type, date))
    statDomains['domains_down'] = r_serv_onion.scard('{}_down:{}'.format(type, date))
    statDomains['total'] = statDomains['domains_up'] + statDomains['domains_down']
    statDomains['domains_queue'] = r_serv_onion.scard('{}_crawler_queue'.format(type))
    statDomains['domains_queue'] += r_serv_onion.scard('{}_crawler_priority_queue'.format(type))
    return statDomains

def get_last_crawled_domains_metadata(list_domains_crawled, date, type=None):
    list_crawled_metadata = []
    for domain_epoch in list_domains_crawled:
        domain, epoch = domain_epoch.rsplit(';', 1)
        metadata_domain = {}
        # get Domain type
        if type is None:
            type = get_domain_type(domain)

        metadata_domain['domain'] = domain
        metadata_domain['epoch'] = epoch
        print(epoch)
        metadata_domain['last_check'] = r_serv_onion.hget('{}_metadata:{}'.format(type, domain), 'last_check')
        if metadata_domain['last_check'] is None:
            metadata_domain['last_check'] = '********'
        metadata_domain['first_seen'] = r_serv_onion.hget('{}_metadata:{}'.format(type, domain), 'first_seen')
        if metadata_domain['first_seen'] is None:
            metadata_domain['first_seen'] = '********'
        if r_serv_onion.sismember('{}_up:{}'.format(type, metadata_domain['last_check']) , domain):
            metadata_domain['status_text'] = 'UP'
            metadata_domain['status_color'] = 'Green'
            metadata_domain['status_icon'] = 'fa-check-circle'
        else:
            metadata_domain['status_text'] = 'DOWN'
            metadata_domain['status_color'] = 'Red'
            metadata_domain['status_icon'] = 'fa-times-circle'
        list_crawled_metadata.append(metadata_domain)
    return list_crawled_metadata

def get_crawler_splash_status(type):
    crawler_metadata = []
    all_crawlers = r_cache.smembers('{}_crawlers'.format(type))
    for crawler in all_crawlers:
        crawling_domain = r_cache.hget('metadata_crawler:{}'.format(crawler), 'crawling_domain')
        started_time = r_cache.hget('metadata_crawler:{}'.format(crawler), 'started_time')
        status_info = r_cache.hget('metadata_crawler:{}'.format(crawler), 'status')
        crawler_info = '{}  - {}'.format(crawler, started_time)
        if status_info=='Waiting' or status_info=='Crawling':
            status=True
        else:
            status=False
        crawler_metadata.append({'crawler_info': crawler_info, 'crawling_domain': crawling_domain, 'status_info': status_info, 'status': status})

    return crawler_metadata

def create_crawler_config(mode, service_type, crawler_config, domain):
    print(crawler_config)
    if mode == 'manual':
        r_cache.set('crawler_config:{}:{}:{}'.format(mode, service_type, domain), json.dumps(crawler_config))
    elif mode == 'auto':
        r_serv_onion.set('crawler_config:{}:{}:{}'.format(mode, service_type, domain), json.dumps(crawler_config))

def send_url_to_crawl_in_queue(mode, service_type, url):
    r_serv_onion.sadd('{}_crawler_priority_queue'.format(service_type), '{};{}'.format(url, mode))
    # add auto crawled url for user UI
    if mode == 'auto':
        r_serv_onion.sadd('auto_crawler_url:{}'.format(service_type), url)

# ============= ROUTES ==============

@hiddenServices.route("/crawlers/", methods=['GET'])
def dashboard():
    return render_template("Crawler_dashboard.html")

@hiddenServices.route("/hiddenServices/2", methods=['GET'])
def hiddenServices_page_test():
    return render_template("Crawler_index.html")

@hiddenServices.route("/crawlers/manual", methods=['GET'])
def manual():
    return render_template("Crawler_Splash_manual.html")

@hiddenServices.route("/crawlers/crawler_splash_onion", methods=['GET'])
def crawler_splash_onion():
    type = 'onion'
    last_onions = get_last_domains_crawled(type)
    list_onion = []

    now = datetime.datetime.now()
    date = now.strftime("%Y%m%d")
    statDomains = get_stats_last_crawled_domains(type, date)

    list_onion = get_last_crawled_domains_metadata(last_onions, date, type=type)
    crawler_metadata = get_crawler_splash_status(type)

    date_string = '{}-{}-{}'.format(date[0:4], date[4:6], date[6:8])
    return render_template("Crawler_Splash_onion.html", last_onions=list_onion, statDomains=statDomains,
                            crawler_metadata=crawler_metadata, date_from=date_string, date_to=date_string)

@hiddenServices.route("/crawlers/crawler_splash_regular", methods=['GET'])
def crawler_splash_regular():
    type = 'regular'
    type_name = dic_type_name[type]
    list_domains = []

    now = datetime.datetime.now()
    date = now.strftime("%Y%m%d")
    date_string = '{}-{}-{}'.format(date[0:4], date[4:6], date[6:8])

    statDomains = get_stats_last_crawled_domains(type, date)

    list_domains = get_last_crawled_domains_metadata(get_last_domains_crawled(type), date, type=type)
    crawler_metadata = get_crawler_splash_status(type)

    return render_template("Crawler_Splash_last_by_type.html", type=type, type_name=type_name,
                            last_domains=list_domains, statDomains=statDomains,
                            crawler_metadata=crawler_metadata, date_from=date_string, date_to=date_string)

@hiddenServices.route("/crawlers/blacklisted_domains", methods=['GET'])
def blacklisted_domains():
    blacklist_domain = request.args.get('blacklist_domain')
    unblacklist_domain = request.args.get('unblacklist_domain')
    type = request.args.get('type')
    if type in list_types:
        type_name = dic_type_name[type]
        if blacklist_domain is not None:
            blacklist_domain = int(blacklist_domain)
        if unblacklist_domain is not None:
            unblacklist_domain = int(unblacklist_domain)
        try:
            page = int(request.args.get('page'))
        except:
            page = 1
        if page <= 0:
            page = 1
        nb_page_max = r_serv_onion.scard('blacklist_{}'.format(type))/(1000)
        if isinstance(nb_page_max, float):
            nb_page_max = int(nb_page_max)+1
        if page > nb_page_max:
            page = nb_page_max
        start = 1000*(page -1)
        stop = 1000*page

        list_blacklisted = list(r_serv_onion.smembers('blacklist_{}'.format(type)))
        list_blacklisted_1 = list_blacklisted[start:stop]
        list_blacklisted_2 = list_blacklisted[stop:stop+1000]
        return render_template("blacklisted_domains.html", list_blacklisted_1=list_blacklisted_1, list_blacklisted_2=list_blacklisted_2,
                                type=type, type_name=type_name, page=page, nb_page_max=nb_page_max,
                                blacklist_domain=blacklist_domain, unblacklist_domain=unblacklist_domain)
    else:
        return 'Incorrect Type'

@hiddenServices.route("/crawler/blacklist_domain", methods=['GET'])
def blacklist_domain():
    domain = request.args.get('domain')
    type = request.args.get('type')
    try:
        page = int(request.args.get('page'))
    except:
        page = 1
    if type in list_types:
        if is_valid_domain(domain):
            res = r_serv_onion.sadd('blacklist_{}'.format(type), domain)
            if page:
                if res == 0:
                    return redirect(url_for('hiddenServices.blacklisted_domains', page=page, type=type, blacklist_domain=2))
                else:
                    return redirect(url_for('hiddenServices.blacklisted_domains', page=page, type=type, blacklist_domain=1))
        else:
            return redirect(url_for('hiddenServices.blacklisted_domains', page=page, type=type, blacklist_domain=0))
    else:
        return 'Incorrect type'

@hiddenServices.route("/crawler/unblacklist_domain", methods=['GET'])
def unblacklist_domain():
    domain = request.args.get('domain')
    type = request.args.get('type')
    try:
        page = int(request.args.get('page'))
    except:
        page = 1
    if type in list_types:
        if is_valid_domain(domain):
            res = r_serv_onion.srem('blacklist_{}'.format(type), domain)
            if page:
                if res == 0:
                    return redirect(url_for('hiddenServices.blacklisted_domains', page=page, type=type, unblacklist_domain=2))
                else:
                    return redirect(url_for('hiddenServices.blacklisted_domains', page=page, type=type, unblacklist_domain=1))
        else:
            return redirect(url_for('hiddenServices.blacklisted_domains', page=page, type=type, unblacklist_domain=0))
    else:
        return 'Incorrect type'

@hiddenServices.route("/crawlers/create_spider_splash", methods=['POST'])
def create_spider_splash():
    url = request.form.get('url_to_crawl')
    automatic = request.form.get('crawler_type')
    crawler_time = request.form.get('crawler_epoch')
    #html = request.form.get('html_content_id')
    screenshot = request.form.get('screenshot')
    har = request.form.get('har')
    depth_limit = request.form.get('depth_limit')
    max_pages = request.form.get('max_pages')

    # validate url
    if url is None or url=='' or url=='\n':
        return 'incorrect url'

    crawler_config = {}

    # verify user input
    if automatic:
        automatic = True
    else:
        automatic = False
    if not screenshot:
        crawler_config['png'] = 0
    if not har:
        crawler_config['har'] = 0

    # verify user input
    if depth_limit:
        try:
            depth_limit = int(depth_limit)
            if depth_limit < 0:
                return 'incorrect depth_limit'
            else:
                crawler_config['depth_limit'] = depth_limit
        except:
            return 'incorrect depth_limit'
    if max_pages:
        try:
            max_pages = int(max_pages)
            if max_pages < 1:
                return 'incorrect max_pages'
            else:
                crawler_config['closespider_pagecount'] = max_pages
        except:
            return 'incorrect max_pages'

    # get service_type
    faup.decode(url)
    unpack_url = faup.get()
    domain = unpack_url['domain'].decode()
    if unpack_url['tld'] == b'onion':
        service_type = 'onion'
    else:
        service_type = 'regular'

    if automatic:
        mode = 'auto'
        try:
            crawler_time = int(crawler_time)
            if crawler_time < 0:
                return 'incorrect epoch'
            else:
                crawler_config['time'] = crawler_time
        except:
            return 'incorrect epoch'
    else:
        mode = 'manual'
        epoch = None

    create_crawler_config(mode, service_type, crawler_config, domain)
    send_url_to_crawl_in_queue(mode, service_type, url)

    return redirect(url_for('hiddenServices.manual'))

@hiddenServices.route("/hiddenServices/", methods=['GET'])
def hiddenServices_page():
    last_onions = r_serv_onion.lrange('last_onion', 0 ,-1)
    list_onion = []

    now = datetime.datetime.now()
    date = now.strftime("%Y%m%d")

    statDomains = {}
    statDomains['domains_up'] = r_serv_onion.scard('onion_up:{}'.format(date))
    statDomains['domains_down'] = r_serv_onion.scard('onion_down:{}'.format(date))
    statDomains['total'] = statDomains['domains_up'] + statDomains['domains_down']
    statDomains['domains_queue'] = r_serv_onion.scard('onion_domain_crawler_queue')

    for onion in last_onions:
        metadata_onion = {}
        metadata_onion['domain'] = onion
        metadata_onion['last_check'] = r_serv_onion.hget('onion_metadata:{}'.format(onion), 'last_check')
        if metadata_onion['last_check'] is None:
            metadata_onion['last_check'] = '********'
        metadata_onion['first_seen'] = r_serv_onion.hget('onion_metadata:{}'.format(onion), 'first_seen')
        if metadata_onion['first_seen'] is None:
            metadata_onion['first_seen'] = '********'
        if get_onion_status(onion, metadata_onion['last_check']):
            metadata_onion['status_text'] = 'UP'
            metadata_onion['status_color'] = 'Green'
            metadata_onion['status_icon'] = 'fa-check-circle'
        else:
            metadata_onion['status_text'] = 'DOWN'
            metadata_onion['status_color'] = 'Red'
            metadata_onion['status_icon'] = 'fa-times-circle'
        list_onion.append(metadata_onion)

    crawler_metadata=[]
    all_onion_crawler = r_cache.smembers('all_crawler:onion')
    for crawler in all_onion_crawler:
        crawling_domain = r_cache.hget('metadata_crawler:{}'.format(crawler), 'crawling_domain')
        started_time = r_cache.hget('metadata_crawler:{}'.format(crawler), 'started_time')
        status_info = r_cache.hget('metadata_crawler:{}'.format(crawler), 'status')
        crawler_info = '{}  - {}'.format(crawler, started_time)
        if status_info=='Waiting' or status_info=='Crawling':
            status=True
        else:
            status=False
        crawler_metadata.append({'crawler_info': crawler_info, 'crawling_domain': crawling_domain, 'status_info': status_info, 'status': status})

    date_string = '{}-{}-{}'.format(date[0:4], date[4:6], date[6:8])
    return render_template("hiddenServices.html", last_onions=list_onion, statDomains=statDomains,
                            crawler_metadata=crawler_metadata, date_from=date_string, date_to=date_string)

@hiddenServices.route("/hiddenServices/last_crawled_domains_with_stats_json", methods=['GET'])
def last_crawled_domains_with_stats_json():
    last_onions = r_serv_onion.lrange('last_onion', 0 ,-1)
    list_onion = []

    now = datetime.datetime.now()
    date = '{}{}{}'.format(now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))
    statDomains = {}
    statDomains['domains_up'] = r_serv_onion.scard('onion_up:{}'.format(date))
    statDomains['domains_down'] = r_serv_onion.scard('onion_down:{}'.format(date))
    statDomains['total'] = statDomains['domains_up'] + statDomains['domains_down']
    statDomains['domains_queue'] = r_serv_onion.scard('onion_domain_crawler_queue')

    for onion in last_onions:
        metadata_onion = {}
        metadata_onion['domain'] = onion
        metadata_onion['last_check'] = r_serv_onion.hget('onion_metadata:{}'.format(onion), 'last_check')
        if metadata_onion['last_check'] is None:
            metadata_onion['last_check'] = '********'
        metadata_onion['first_seen'] = r_serv_onion.hget('onion_metadata:{}'.format(onion), 'first_seen')
        if metadata_onion['first_seen'] is None:
            metadata_onion['first_seen'] = '********'
        if get_onion_status(onion, metadata_onion['last_check']):
            metadata_onion['status_text'] = 'UP'
            metadata_onion['status_color'] = 'Green'
            metadata_onion['status_icon'] = 'fa-check-circle'
        else:
            metadata_onion['status_text'] = 'DOWN'
            metadata_onion['status_color'] = 'Red'
            metadata_onion['status_icon'] = 'fa-times-circle'
        list_onion.append(metadata_onion)

    crawler_metadata=[]
    all_onion_crawler = r_cache.smembers('all_crawler:onion')
    for crawler in all_onion_crawler:
        crawling_domain = r_cache.hget('metadata_crawler:{}'.format(crawler), 'crawling_domain')
        started_time = r_cache.hget('metadata_crawler:{}'.format(crawler), 'started_time')
        status_info = r_cache.hget('metadata_crawler:{}'.format(crawler), 'status')
        crawler_info = '{}  - {}'.format(crawler, started_time)
        if status_info=='Waiting' or status_info=='Crawling':
            status=True
        else:
            status=False
        crawler_metadata.append({'crawler_info': crawler_info, 'crawling_domain': crawling_domain, 'status_info': status_info, 'status': status})

    date_string = '{}-{}-{}'.format(date[0:4], date[4:6], date[6:8])

    return jsonify({'last_onions': list_onion, 'statDomains': statDomains, 'crawler_metadata':crawler_metadata})

@hiddenServices.route("/hiddenServices/get_onions_by_daterange", methods=['POST'])
def get_onions_by_daterange():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    domains_up = request.form.get('domains_up')
    domains_down = request.form.get('domains_down')
    domains_tags = request.form.get('domains_tags')

    return redirect(url_for('hiddenServices.show_domains_by_daterange', date_from=date_from, date_to=date_to, domains_up=domains_up, domains_down=domains_down, domains_tags=domains_tags))

@hiddenServices.route("/hiddenServices/show_domains_by_daterange", methods=['GET'])
def show_domains_by_daterange():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    domains_up = request.args.get('domains_up')
    domains_down = request.args.get('domains_down')
    domains_tags = request.args.get('domains_tags')

    date_range = []
    if date_from is not None and date_to is not None:
        #change format
        try:
            if len(date_from) != 8:
                date_from = date_from[0:4] + date_from[5:7] + date_from[8:10]
                date_to = date_to[0:4] + date_to[5:7] + date_to[8:10]
            date_range = substract_date(date_from, date_to)
        except:
            pass

    if not date_range:
        date_range.append(datetime.date.today().strftime("%Y%m%d"))
        date_from = date_range[0][0:4] + '-' + date_range[0][4:6] + '-' + date_range[0][6:8]
        date_to = date_from

    else:
        date_from = date_from[0:4] + '-' + date_from[4:6] + '-' + date_from[6:8]
        date_to = date_to[0:4] + '-' + date_to[4:6] + '-' + date_to[6:8]

    domains_by_day = {}
    domain_metadata = {}
    for date in date_range:
        if domains_up:
            domains_up = True
            domains_by_day[date] = list(r_serv_onion.smembers('onion_up:{}'.format(date)))
            for domain in domains_by_day[date]:
                h = HiddenServices(domain, 'onion')
                domain_metadata[domain] = {}
                if domains_tags:
                    domains_tags = True
                    domain_metadata[domain]['tags'] = h.get_domain_tags(update=True)

                domain_metadata[domain]['last_check'] = r_serv_onion.hget('onion_metadata:{}'.format(domain), 'last_check')
                if domain_metadata[domain]['last_check'] is None:
                    domain_metadata[domain]['last_check'] = '********'
                domain_metadata[domain]['first_seen'] = r_serv_onion.hget('onion_metadata:{}'.format(domain), 'first_seen')
                if domain_metadata[domain]['first_seen'] is None:
                    domain_metadata[domain]['first_seen'] = '********'
                domain_metadata[domain]['status_text'] = 'UP'
                domain_metadata[domain]['status_color'] = 'Green'
                domain_metadata[domain]['status_icon'] = 'fa-check-circle'

        if domains_down:
            domains_down = True
            domains_by_day_down = list(r_serv_onion.smembers('onion_down:{}'.format(date)))
            if domains_up:
                domains_by_day[date].extend(domains_by_day_down)
            else:
                domains_by_day[date] = domains_by_day_down
            for domain in domains_by_day_down:
                #h = HiddenServices(onion_domain, 'onion')
                domain_metadata[domain] = {}
                #domain_metadata[domain]['tags'] = h.get_domain_tags()

                domain_metadata[domain]['last_check'] = r_serv_onion.hget('onion_metadata:{}'.format(domain), 'last_check')
                if domain_metadata[domain]['last_check'] is None:
                    domain_metadata[domain]['last_check'] = '********'
                domain_metadata[domain]['first_seen'] = r_serv_onion.hget('onion_metadata:{}'.format(domain), 'first_seen')
                if domain_metadata[domain]['first_seen'] is None:
                    domain_metadata[domain]['first_seen'] = '********'

                domain_metadata[domain]['status_text'] = 'DOWN'
                domain_metadata[domain]['status_color'] = 'Red'
                domain_metadata[domain]['status_icon'] = 'fa-times-circle'

    return render_template("domains.html", date_range=date_range, domains_by_day=domains_by_day, domain_metadata=domain_metadata,
                                date_from=date_from, date_to=date_to, domains_up=domains_up, domains_down=domains_down,
                                domains_tags=domains_tags, bootstrap_label=bootstrap_label)

@hiddenServices.route("/hiddenServices/onion_domain", methods=['GET'])
def onion_domain():
    onion_domain = request.args.get('onion_domain')
    if onion_domain is None or not r_serv_onion.exists('onion_metadata:{}'.format(onion_domain)):
        return '404'
        # # TODO: FIXME return 404

    last_check = r_serv_onion.hget('onion_metadata:{}'.format(onion_domain), 'last_check')
    if last_check is None:
        last_check = '********'
    last_check = '{}/{}/{}'.format(last_check[0:4], last_check[4:6], last_check[6:8])
    first_seen = r_serv_onion.hget('onion_metadata:{}'.format(onion_domain), 'first_seen')
    if first_seen is None:
        first_seen = '********'
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

@hiddenServices.route('/hiddenServices/domain_crawled_by_type_json')
def domain_crawled_by_type_json():
    current_date = request.args.get('date')
    type = request.args.get('type')
    if type in list_types:

        num_day_type = 7
        date_range = get_date_range(num_day_type)
        range_decoder = []
        for date in date_range:
            day_crawled = {}
            day_crawled['date']= date[0:4] + '-' + date[4:6] + '-' + date[6:8]
            day_crawled['UP']= nb_domain_up = r_serv_onion.scard('{}_up:{}'.format(type, date))
            day_crawled['DOWN']= nb_domain_up = r_serv_onion.scard('{}_up:{}'.format(type, date))
            range_decoder.append(day_crawled)

        return jsonify(range_decoder)

    else:
        return jsonify('Incorrect Type')

# ========= REGISTRATION =========
app.register_blueprint(hiddenServices, url_prefix=baseUrl)
