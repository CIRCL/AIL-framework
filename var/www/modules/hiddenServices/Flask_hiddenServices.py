#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import datetime
import sys
import os
import time
from pyfaup.faup import Faup
from flask import Flask, render_template, jsonify, request, send_file, Blueprint, redirect, url_for

from Role_Manager import login_admin, login_analyst, login_read_only, no_cache
from flask_login import login_required

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import crawlers

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl
r_cache = Flask_config.r_cache
r_serv_onion = Flask_config.r_serv_onion
r_serv_metadata = Flask_config.r_serv_metadata
bootstrap_label = Flask_config.bootstrap_label

hiddenServices = Blueprint('hiddenServices', __name__, template_folder='templates')

faup = Faup()
list_types=['onion', 'regular']
dic_type_name={'onion':'Onion', 'regular':'Website'}

# ============ FUNCTIONS ============


def is_valid_domain(domain):
    faup.decode(domain)
    domain_unpack = faup.get()
    if domain_unpack['tld'] is not None and domain_unpack['scheme'] is None and domain_unpack['port'] is None and domain_unpack['query_string'] is None:
        return True
    else:
        return False

def get_type_domain(domain):
    if domain is None:
        type = 'regular'
    else:
        if domain.rsplit('.', 1)[1] == 'onion':
            type = 'onion'
        else:
            type = 'regular'
    return type

def get_domain_from_url(url):
    faup.decode(url)
    unpack_url = faup.get()
    domain = unpack_url['domain']
    ## TODO: FIXME remove me
    try:
        domain = domain.decode()
    except:
        pass
    return domain

def get_last_domains_crawled(type): # DONE
    return r_serv_onion.lrange('last_{}'.format(type), 0 ,-1)


def get_last_crawled_domains_metadata(list_domains_crawled, date, type=None, auto_mode=False):
    list_crawled_metadata = []
    for domain_epoch in list_domains_crawled:
        if not auto_mode:
            domain, epoch = domain_epoch.rsplit(';', 1)
        else:
            url = domain_epoch
            domain = domain_epoch
        domain = domain.split(':')
        if len(domain) == 1:
            port = 80
            domain = domain[0]
        else:
            port = domain[1]
            domain = domain[0]
        metadata_domain = {}
        # get Domain type
        if type is None:
            type_domain = get_type_domain(domain)
        else:
            type_domain = type
        if auto_mode:
            metadata_domain['url'] = url
            epoch = r_serv_onion.zscore('crawler_auto_queue', '{};auto;{}'.format(domain, type_domain))
            #domain in priority queue
            if epoch is None:
                epoch = 'In Queue'
            else:
                epoch = datetime.datetime.fromtimestamp(float(epoch)).strftime('%Y-%m-%d %H:%M:%S')

        metadata_domain['domain'] = domain
        if len(domain) > 45:
            domain_name, tld_domain = domain.rsplit('.', 1)
            metadata_domain['domain_name'] = '{}[...].{}'.format(domain_name[:40], tld_domain)
        else:
            metadata_domain['domain_name'] = domain
        metadata_domain['port'] = port
        metadata_domain['epoch'] = epoch
        metadata_domain['last_check'] = r_serv_onion.hget('{}_metadata:{}'.format(type_domain, domain), 'last_check')
        if metadata_domain['last_check'] is None:
            metadata_domain['last_check'] = '********'
        metadata_domain['first_seen'] = r_serv_onion.hget('{}_metadata:{}'.format(type_domain, domain), 'first_seen')
        if metadata_domain['first_seen'] is None:
            metadata_domain['first_seen'] = '********'
        if r_serv_onion.sismember('{}_up:{}'.format(type_domain, metadata_domain['last_check']) , domain):
            metadata_domain['status_text'] = 'UP'
            metadata_domain['status_color'] = 'Green'
            metadata_domain['status_icon'] = 'fa-check-circle'
        else:
            metadata_domain['status_text'] = 'DOWN'
            metadata_domain['status_color'] = 'Red'
            metadata_domain['status_icon'] = 'fa-times-circle'
        list_crawled_metadata.append(metadata_domain)
    return list_crawled_metadata

def delete_auto_crawler(url):
    domain = get_domain_from_url(url)
    type = get_type_domain(domain)
    # remove from set
    r_serv_onion.srem('auto_crawler_url:{}'.format(type), url)
    # remove config
    r_serv_onion.delete('crawler_config:auto:{}:{}:{}'.format(type, domain, url))
    # remove from queue
    r_serv_onion.srem('{}_crawler_priority_queue'.format(type), '{};auto'.format(url))
    # remove from crawler_auto_queue
    r_serv_onion.zrem('crawler_auto_queue'.format(type), '{};auto;{}'.format(url, type))

# ============= ROUTES ==============

@hiddenServices.route("/crawlers/blacklisted_domains", methods=['GET'])
@login_required
@login_read_only
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
@login_required
@login_analyst
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
@login_required
@login_analyst
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

@hiddenServices.route("/crawlers/auto_crawler", methods=['GET'])
@login_required
@login_read_only
def auto_crawler():
    nb_element_to_display = 100
    try:
        page = int(request.args.get('page'))
    except:
        page = 1
    if page <= 0:
        page = 1

    nb_auto_onion = r_serv_onion.scard('auto_crawler_url:onion')
    nb_auto_regular = r_serv_onion.scard('auto_crawler_url:regular')

    if nb_auto_onion > nb_auto_regular:
        nb_max = nb_auto_onion
    else:
        nb_max = nb_auto_regular

    nb_page_max = nb_max/(nb_element_to_display)
    if isinstance(nb_page_max, float):
        nb_page_max = int(nb_page_max)+1
    if page > nb_page_max:
        page = nb_page_max
    start = nb_element_to_display*(page -1)
    stop = nb_element_to_display*page

    last_auto_crawled = get_last_domains_crawled('auto_crawled')
    last_domains = get_last_crawled_domains_metadata(last_auto_crawled, '')

    if start > nb_auto_onion:
        auto_crawler_domain_onions = []
    elif stop > nb_auto_onion:
        auto_crawler_domain_onions = list(r_serv_onion.smembers('auto_crawler_url:onion'))[start:nb_auto_onion]
    else:
        auto_crawler_domain_onions = list(r_serv_onion.smembers('auto_crawler_url:onion'))[start:stop]

    if start > nb_auto_regular:
        auto_crawler_domain_regular = []
    elif stop > nb_auto_regular:
        auto_crawler_domain_regular = list(r_serv_onion.smembers('auto_crawler_url:regular'))[start:nb_auto_regular]
    else:
        auto_crawler_domain_regular = list(r_serv_onion.smembers('auto_crawler_url:regular'))[start:stop]

    auto_crawler_domain_onions_metadata = get_last_crawled_domains_metadata(auto_crawler_domain_onions, '', type='onion', auto_mode=True)
    auto_crawler_domain_regular_metadata = get_last_crawled_domains_metadata(auto_crawler_domain_regular, '', type='regular', auto_mode=True)

    return render_template("Crawler_auto.html", page=page, nb_page_max=nb_page_max,
                                last_domains=last_domains,
                                is_manager_connected=crawlers.get_lacus_connection_metadata(),
                                auto_crawler_domain_onions_metadata=auto_crawler_domain_onions_metadata,
                                auto_crawler_domain_regular_metadata=auto_crawler_domain_regular_metadata)

@hiddenServices.route("/crawlers/remove_auto_crawler", methods=['GET'])
@login_required
@login_analyst
def remove_auto_crawler():
    url = request.args.get('url')
    page = request.args.get('page')

    if url:
        delete_auto_crawler(url)
    return redirect(url_for('hiddenServices.auto_crawler', page=page))


# ========= REGISTRATION =========
app.register_blueprint(hiddenServices, url_prefix=baseUrl)
