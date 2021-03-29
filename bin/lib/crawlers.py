#!/usr/bin/python3

"""
API Helper
===================


"""
import base64
import gzip
import json
import os
import re
import redis
import sys
import time
import uuid

import subprocess

from datetime import datetime, timedelta
from urllib.parse import urlparse

from pyfaup.faup import Faup

# interact with splash_crawler API
import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import git_status

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'core/'))
import screen

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
r_cache = config_loader.get_redis_conn("Redis_Cache")
PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes"))
config_loader = None

faup = Faup()

# # # # # # # #
#             #
#   COMMON    #
#             #
# # # # # # # #

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')

# # TODO: remove me ?
def get_current_date():
    return datetime.now().strftime("%Y%m%d")

def is_valid_onion_domain(domain):
    if not domain.endswith('.onion'):
        return False
    domain = domain.replace('.onion', '', 1)
    if len(domain) == 16: # v2 address
        r_onion = r'[a-z0-9]{16}'
        if re.match(r_onion, domain):
            return True
    elif len(domain) == 56: # v3 address
        r_onion = r'[a-z0-9]{56}'
        if re.fullmatch(r_onion, domain):
            return True
    return False

# TEMP FIX
def get_faup():
    return faup

################################################################################

# # TODO: handle prefix cookies
# # TODO: fill empty fields
def create_cookie_crawler(cookie_dict, domain, crawler_type='regular'):
    # check cookie domain filed
    if not 'domain' in cookie_dict:
        cookie_dict['domain'] = '.{}'.format(domain)

    # tor browser: disable secure cookie
    if crawler_type=='onion':
        cookie_dict['secure'] = False

    # force cookie domain
    # url = urlparse(browser_cookie['Host raw'])
    # domain = url.netloc.split(':', 1)[0]
    # cookie_dict['domain'] = '.{}'.format(domain)

    # change expire date
    cookie_dict['expires'] = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    return cookie_dict

def load_crawler_cookies(cookiejar_uuid, domain, crawler_type='regular'):
    cookies = get_cookiejar_cookies_list(cookiejar_uuid)
    all_cookies = []
    for cookie_dict in cookies:
        all_cookies.append(create_cookie_crawler(cookie_dict, domain, crawler_type=crawler_type))
    return all_cookies

################################################################################

def get_all_cookiejar():
    r_serv_onion.smembers('cookiejar:all')

def get_global_cookiejar():
    res = r_serv_onion.smembers('cookiejar:global')
    if not res:
        res = []
    return res

def get_user_cookiejar(user_id):
    res = r_serv_onion.smembers('cookiejar:user:{}'.format(user_id))
    if not res:
        res = []
    return res

def exist_cookiejar(cookiejar_uuid):
    return r_serv_onion.exists('cookiejar_metadata:{}'.format(cookiejar_uuid))

def create_cookiejar(user_id, level=1, description=None):
    cookiejar_uuid = str(uuid.uuid4())

    r_serv_onion.sadd('cookiejar:all', cookiejar_uuid)
    if level==0:
        r_serv_onion.sadd('cookiejar:user:{}'.format(user_id), cookiejar_uuid)
    else:
        r_serv_onion.sadd('cookiejar:global', cookiejar_uuid)
    # metadata
    r_serv_onion.hset('cookiejar_metadata:{}'.format(cookiejar_uuid), 'user_id', user_id)
    r_serv_onion.hset('cookiejar_metadata:{}'.format(cookiejar_uuid), 'level', level)
    r_serv_onion.hset('cookiejar_metadata:{}'.format(cookiejar_uuid), 'description', description)
    r_serv_onion.hset('cookiejar_metadata:{}'.format(cookiejar_uuid), 'date', datetime.now().strftime("%Y%m%d"))

    # if json_cookies:
    #     json_cookies = json.loads(json_cookies) # # TODO: catch Exception
    #     r_serv_onion.set('cookies:json_cookies:{}'.format(cookies_uuid), json.dumps(json_cookies))
    #
    # for cookie_dict in l_cookies:
    #     r_serv_onion.hset('cookies:manual_cookies:{}'.format(cookies_uuid), cookie_dict['name'], cookie_dict['value'])
    return cookiejar_uuid

def delete_cookie_jar(cookiejar_uuid):
    level = get_cookiejar_level(cookiejar_uuid)
    if level == 0:
        user_id = get_cookiejar_owner(cookiejar_uuid)
        r_serv_onion.srem('cookiejar:user:{}'.format(user_id), cookiejar_uuid)
    else:
        r_serv_onion.srem('cookiejar:global', cookiejar_uuid)

    r_serv_onion.delete('cookiejar_metadata:{}'.format(cookiejar_uuid))

def get_cookiejar_cookies_uuid(cookiejar_uuid):
    res = r_serv_onion.smembers('cookiejar:{}:cookies:uuid'.format(cookiejar_uuid))
    if not res:
        res = []
    return res

def get_cookiejar_cookies_list(cookiejar_uuid, add_cookie_uuid=False):
    l_cookiejar = []
    for cookie_uuid in get_cookiejar_cookies_uuid(cookiejar_uuid):
        if add_cookie_uuid:
            l_cookiejar.append((get_cookie_dict(cookie_uuid), cookie_uuid))
        else:
            l_cookiejar.append(get_cookie_dict(cookie_uuid))
    return l_cookiejar

## Cookiejar metadata ##
def get_cookiejar_description(cookiejar_uuid):
    return r_serv_onion.hget('cookiejar_metadata:{}'.format(cookiejar_uuid), 'description')

def get_cookiejar_date(cookiejar_uuid):
    return r_serv_onion.hget('cookiejar_metadata:{}'.format(cookiejar_uuid), 'date')

def get_cookiejar_owner(cookiejar_uuid):
    return r_serv_onion.hget('cookiejar_metadata:{}'.format(cookiejar_uuid), 'user_id')

def get_cookiejar_date(cookiejar_uuid):
    return r_serv_onion.hget('cookiejar_metadata:{}'.format(cookiejar_uuid), 'date')

def get_cookiejar_level(cookiejar_uuid):
    res = r_serv_onion.hget('cookiejar_metadata:{}'.format(cookiejar_uuid), 'level')
    if not res:
        res = 1
    return int(res)

def get_cookiejar_metadata(cookiejar_uuid, level=False):
    dict_cookiejar = {}
    if exist_cookiejar(cookiejar_uuid):
        dict_cookiejar['cookiejar_uuid'] = cookiejar_uuid
        dict_cookiejar['description'] = get_cookiejar_description(cookiejar_uuid)
        dict_cookiejar['date'] = get_cookiejar_date(cookiejar_uuid)
        dict_cookiejar['user_id'] = get_cookiejar_owner(cookiejar_uuid)
        if level:
            dict_cookiejar['level'] = get_cookies_level(cookiejar_uuid)
    return dict_cookiejar

def get_cookiejar_metadata_by_iterator(iter_cookiejar_uuid):
    l_cookiejar_metadata = []
    for cookiejar_uuid in iter_cookiejar_uuid:
        l_cookiejar_metadata.append(get_cookiejar_metadata(cookiejar_uuid))
    return l_cookiejar_metadata

def edit_cookiejar_description(cookiejar_uuid, description):
    r_serv_onion.hset('cookiejar_metadata:{}'.format(cookiejar_uuid), 'description', description)

# # # # # # # #
#             #
#   COOKIES   #
#             #
# # # # # # # #

# # # #
# Cookies Fields:
#   - name
#   - value
#   - path      (optional)
#   - domain    (optional)
#   - secure    (optional)
#   - httpOnly  (optional)
#   - text      (optional)
# # # #
def get_cookie_all_keys_name():
    return ['name', 'value', 'domain', 'path', 'httpOnly', 'secure']

def exists_cookie(cookie_uuid):
    if int(r_serv_onion.scard('cookies:map:cookiejar:{}'.format(cookie_uuid))) > 0:
        return True
    return False

def get_cookie_value(cookie_uuid, name):
    return r_serv_onion.hget('cookiejar:cookie:{}'.format(cookie_uuid), name)

def set_cookie_value(cookie_uuid, name, value):
    r_serv_onion.hset('cookiejar:cookie:{}'.format(cookie_uuid), name, value)

def delete_cookie_value(cookie_uuid, name):
    r_serv_onion.hdel('cookiejar:cookie:{}'.format(cookie_uuid), name)

def get_cookie_dict(cookie_uuid):
    cookie_dict = {}
    for key_name in r_serv_onion.hkeys('cookiejar:cookie:{}'.format(cookie_uuid)):
        cookie_dict[key_name] = get_cookie_value(cookie_uuid, key_name)
    return cookie_dict

# name, value, path=None, httpOnly=None, secure=None, domain=None, text=None
def add_cookie_to_cookiejar(cookiejar_uuid, cookie_dict):
    cookie_uuid = generate_uuid()
    r_serv_onion.sadd('cookiejar:{}:cookies:uuid'.format(cookiejar_uuid), cookie_uuid)
    r_serv_onion.sadd('cookies:map:cookiejar:{}'.format(cookie_uuid), cookiejar_uuid)

    set_cookie_value(cookie_uuid, 'name', cookie_dict['name'])
    set_cookie_value(cookie_uuid, 'value', cookie_dict['value'])
    if 'path' in cookie_dict:
        set_cookie_value(cookie_uuid, 'path', cookie_dict['path'])
    if 'httpOnly' in cookie_dict:
        set_cookie_value(cookie_uuid, 'httpOnly', cookie_dict['httpOnly'])
    if 'secure' in cookie_dict:
        set_cookie_value(cookie_uuid, 'secure', cookie_dict['secure'])
    if 'domain' in cookie_dict:
        set_cookie_value(cookie_uuid, 'domain', cookie_dict['domain'])
    if 'text' in cookie_dict:
        set_cookie_value(cookie_uuid, 'text', cookie_dict['text'])
    return cookie_uuid

def add_cookies_to_cookiejar(cookiejar_uuid, l_cookies):
    for cookie_dict in l_cookies:
        add_cookie_to_cookiejar(cookiejar_uuid, cookie_dict)

def delete_all_cookies_from_cookiejar(cookiejar_uuid):
    for cookie_uuid in get_cookiejar_cookies_uuid(cookiejar_uuid):
        delete_cookie_from_cookiejar(cookiejar_uuid, cookie_uuid)

def delete_cookie_from_cookiejar(cookiejar_uuid, cookie_uuid):
    r_serv_onion.srem('cookiejar:{}:cookies:uuid'.format(cookiejar_uuid), cookie_uuid)
    r_serv_onion.srem('cookies:map:cookiejar:{}'.format(cookie_uuid), cookiejar_uuid)
    if not exists_cookie(cookie_uuid):
        r_serv_onion.delete('cookiejar:cookie:{}'.format(cookie_uuid))

def edit_cookie(cookiejar_uuid, cookie_uuid, cookie_dict):
    # delete old keys
    for key_name in r_serv_onion.hkeys('cookiejar:cookie:{}'.format(cookie_uuid)):
        if key_name not in cookie_dict:
            delete_cookie_value(cookie_uuid, key_name)
    # add new keys
    cookie_all_keys_name = get_cookie_all_keys_name()
    for key_name in cookie_dict:
        if key_name in cookie_all_keys_name:
            set_cookie_value(cookie_uuid, key_name, cookie_dict[key_name])

##  - -  ##
## Cookies import ##       # TODO: add browser type ?
def import_cookies_from_json(json_cookies, cookiejar_uuid):
    for cookie in json_cookies:
        try:
            cookie_dict = unpack_imported_json_cookie(cookie)
            add_cookie_to_cookiejar(cookiejar_uuid, cookie_dict)
        except KeyError:
            return {'error': 'Invalid cookie key, please submit a valid JSON', 'cookiejar_uuid': cookiejar_uuid}

# # TODO: add text field
def unpack_imported_json_cookie(json_cookie):
    cookie_dict = {'name': json_cookie['Name raw'], 'value': json_cookie['Content raw']}
    if 'Path raw' in json_cookie:
        cookie_dict['path'] = json_cookie['Path raw']
    if 'httpOnly' in json_cookie:
        cookie_dict['httpOnly'] = json_cookie['HTTP only raw'] == 'true'
    if 'secure' in json_cookie:
        cookie_dict['secure'] = json_cookie['Send for'] == 'Encrypted connections only'
    if 'Host raw' in json_cookie:
        url = urlparse(json_cookie['Host raw'])
        cookie_dict['domain'] = url.netloc.split(':', 1)[0]
    return cookie_dict

def misp_cookie_import(misp_object, cookiejar_uuid):
    pass
##  - -  ##
#### COOKIEJAR API ####
def api_import_cookies_from_json(json_cookies_str, cookiejar_uuid): # # TODO: add catch
    json_cookies = json.loads(json_cookies_str)
    res = import_cookies_from_json(json_cookies, cookiejar_uuid)
    if res:
        return (res, 400)
#### ####

#### COOKIES API ####

def api_verify_basic_cookiejar(cookiejar_uuid, user_id):
    if not exist_cookiejar(cookiejar_uuid):
        return ({'error': 'unknow cookiejar uuid', 'cookiejar_uuid': cookiejar_uuid}, 404)
    level = get_cookiejar_level(cookiejar_uuid)
    if level == 0: # # TODO: check if user is admin
        cookie_owner = get_cookiejar_owner(cookiejar_uuid)
        if cookie_owner != user_id:
            return ({'error': 'The access to this cookiejar is restricted'}, 403)

def api_get_cookiejar_cookies(cookiejar_uuid, user_id):
    res = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if res:
        return res
    res = get_cookiejar_cookies_list(cookiejar_uuid)
    return (res, 200)

def api_edit_cookiejar_description(user_id, cookiejar_uuid, description):
    res = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if res:
        return res
    edit_cookiejar_description(cookiejar_uuid, description)
    return ({'cookiejar_uuid': cookiejar_uuid}, 200)

def api_get_cookiejar_cookies_with_uuid(cookiejar_uuid, user_id):
    res = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if res:
        return res
    res = get_cookiejar_cookies_list(cookiejar_uuid, add_cookie_uuid=True)
    return (res, 200)

def api_get_cookies_list_select(user_id):
    l_cookiejar = []
    for cookies_uuid in get_global_cookiejar():
        l_cookiejar.append('{} : {}'.format(get_cookiejar_description(cookies_uuid), cookies_uuid))
    for cookies_uuid in get_user_cookiejar(user_id):
        l_cookiejar.append('{} : {}'.format(get_cookiejar_description(cookies_uuid), cookies_uuid))
    return sorted(l_cookiejar)

def api_delete_cookie_from_cookiejar(user_id, cookiejar_uuid, cookie_uuid):
    res = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if res:
        return res
    delete_cookie_from_cookiejar(cookiejar_uuid, cookie_uuid)
    return ({'cookiejar_uuid': cookiejar_uuid, 'cookie_uuid': cookie_uuid}, 200)

def api_delete_cookie_jar(user_id, cookiejar_uuid):
    res = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if res:
        return res
    delete_cookie_jar(cookiejar_uuid)
    return ({'cookiejar_uuid': cookiejar_uuid}, 200)

def api_edit_cookie(user_id, cookiejar_uuid, cookie_uuid, cookie_dict):
    res = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if res:
        return res
    if 'name' not in cookie_dict or 'value' not in cookie_dict or cookie_dict['name'] == '':
        ({'error': 'cookie name or value not provided'}, 400)
    edit_cookie(cookiejar_uuid, cookie_uuid, cookie_dict)
    return (get_cookie_dict(cookie_uuid), 200)

def api_create_cookie(user_id, cookiejar_uuid, cookie_dict):
    res = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if res:
        return res
    if 'name' not in cookie_dict or 'value' not in cookie_dict or cookie_dict['name'] == '':
        ({'error': 'cookie name or value not provided'}, 400)
    res = add_cookie_to_cookiejar(cookiejar_uuid, cookie_dict)
    return (res, 200)

#### ####

# # # # # # # #
#             #
#   CRAWLER   #
#             #
# # # # # # # #

#### CRAWLER GLOBAL ####

def get_all_spash_crawler_status():
    crawler_metadata = []
    all_crawlers = r_cache.smembers('all_splash_crawlers')
    for crawler in all_crawlers:
        crawler_metadata.append(get_splash_crawler_status(crawler))
    return crawler_metadata

def reset_all_spash_crawler_status():
    r_cache.delete('all_splash_crawlers')

def get_splash_crawler_status(spash_url):
    crawler_type = r_cache.hget('metadata_crawler:{}'.format(spash_url), 'type')
    crawling_domain = r_cache.hget('metadata_crawler:{}'.format(spash_url), 'crawling_domain')
    started_time = r_cache.hget('metadata_crawler:{}'.format(spash_url), 'started_time')
    status_info = r_cache.hget('metadata_crawler:{}'.format(spash_url), 'status')
    crawler_info = '{}  - {}'.format(spash_url, started_time)
    if status_info=='Waiting' or status_info=='Crawling':
        status=True
    else:
        status=False
    return {'crawler_info': crawler_info, 'crawling_domain': crawling_domain, 'status_info': status_info, 'status': status, 'type': crawler_type}

def set_current_crawler_status(splash_url, status, started_time=False, crawled_domain=None, crawler_type=None):
    # TODO: get crawler type if None
    # Status: ['Waiting', 'Error', ...]
    r_cache.hset('metadata_crawler:{}'.format(splash_url), 'status', status)
    if started_time:
        r_cache.hset('metadata_crawler:{}'.format(splash_url), 'started_time', datetime.now().strftime("%Y/%m/%d  -  %H:%M.%S"))
    if crawler_type:
        r_cache.hset('metadata_crawler:{}'.format(splash_url), 'type', crawler_type)
    if crawled_domain:
        r_cache.hset('metadata_crawler:{}'.format(splash_url), 'crawling_domain', crawled_domain)

    #r_cache.sadd('all_splash_crawlers', splash_url) # # TODO: add me in fct: create_ail_crawler

def get_stats_last_crawled_domains(crawler_types, date):
    statDomains = {}
    for crawler_type in crawler_types:
        stat_type = {}
        stat_type['domains_up'] = r_serv_onion.scard('{}_up:{}'.format(crawler_type, date))
        stat_type['domains_down'] = r_serv_onion.scard('{}_down:{}'.format(crawler_type, date))
        stat_type['total'] = stat_type['domains_up'] + stat_type['domains_down']
        stat_type['domains_queue'] = get_nb_elem_to_crawl_by_type(crawler_type)
        statDomains[crawler_type] = stat_type
    return statDomains

# # TODO: handle custom proxy
def get_splash_crawler_latest_stats():
    now = datetime.now()
    date = now.strftime("%Y%m%d")
    return get_stats_last_crawled_domains(['onion', 'regular'], date)

def get_nb_crawlers_to_launch_by_splash_name(splash_name):
    res = r_serv_onion.hget('all_crawlers_to_launch', splash_name)
    if res:
        return int(res)
    else:
        return 0

def get_all_crawlers_to_launch_splash_name():
    return r_serv_onion.hkeys('all_crawlers_to_launch')

def get_nb_crawlers_to_launch():
    nb_crawlers_to_launch = r_serv_onion.hgetall('all_crawlers_to_launch')
    for splash_name in nb_crawlers_to_launch:
        nb_crawlers_to_launch[splash_name] = int(nb_crawlers_to_launch[splash_name])
    return nb_crawlers_to_launch

def get_nb_crawlers_to_launch_ui():
    nb_crawlers_to_launch = get_nb_crawlers_to_launch()
    for splash_name in get_all_splash():
        if splash_name not in nb_crawlers_to_launch:
            nb_crawlers_to_launch[splash_name] = 0
    return nb_crawlers_to_launch

def set_nb_crawlers_to_launch(dict_splash_name):
    r_serv_onion.delete('all_crawlers_to_launch')
    for splash_name in dict_splash_name:
        r_serv_onion.hset('all_crawlers_to_launch', splash_name, int(dict_splash_name[splash_name]))
    relaunch_crawlers()

def relaunch_crawlers():
    all_crawlers_to_launch = get_nb_crawlers_to_launch()
    for splash_name in all_crawlers_to_launch:
        nb_crawlers = int(all_crawlers_to_launch[splash_name])

        all_crawler_urls = get_splash_all_url(splash_name, r_list=True)
        if nb_crawlers > len(all_crawler_urls):
            print('Error, can\'t launch all Splash Dockers')
            print('Please launch {} additional {} Dockers'.format( nb_crawlers - len(all_crawler_urls), splash_name))
            nb_crawlers = len(all_crawler_urls)

        reset_all_spash_crawler_status()

        for i in range(0, int(nb_crawlers)):
            splash_url = all_crawler_urls[i]
            print(all_crawler_urls[i])

            launch_ail_splash_crawler(splash_url, script_options='{}'.format(splash_url))

def api_set_nb_crawlers_to_launch(dict_splash_name):
    # TODO: check if is dict
    dict_crawlers_to_launch = {}
    all_splash = get_all_splash()
    crawlers_to_launch = list(all_splash & set(dict_splash_name.keys()))
    for splash_name in crawlers_to_launch:
        try:
            nb_to_launch = int(dict_splash_name.get(splash_name, 0))
            if nb_to_launch < 0:
                return ({'error':'The number of crawlers to launch is negative'}, 400)
        except:
            return ({'error':'invalid number of crawlers to launch'}, 400)
        if nb_to_launch > 0:
            dict_crawlers_to_launch[splash_name] = nb_to_launch

    if dict_crawlers_to_launch:
        set_nb_crawlers_to_launch(dict_crawlers_to_launch)
        return (dict_crawlers_to_launch, 200)
    else:
        return ({'error':'invalid input'}, 400)


##-- CRAWLER GLOBAL --##

#### CRAWLER TASK ####
def create_crawler_task(url, screenshot=True, har=True, depth_limit=1, max_pages=100, auto_crawler=False, crawler_delta=3600, crawler_type=None, cookiejar_uuid=None, user_agent=None):

    crawler_config = {}
    crawler_config['depth_limit'] = depth_limit
    crawler_config['closespider_pagecount'] = max_pages

    if screenshot:
        crawler_config['png'] = True
    else:
        crawler_config['png'] = False
    if har:
        crawler_config['har'] = True
    else:
        crawler_config['har'] = False

    if user_agent:
        crawler_config['user_agent'] = user_agent
    if cookiejar_uuid:
        crawler_config['cookiejar_uuid'] = cookiejar_uuid

    if auto_crawler:
        crawler_mode = 'auto'
        crawler_config['time'] = crawler_delta
    else:
        crawler_mode = 'manual'

    # get crawler_mode
    faup.decode(url)
    unpack_url = faup.get()
    ## TODO: # FIXME: remove me
    try:
        domain = unpack_url['domain'].decode()
    except:
        domain = unpack_url['domain']

    ## TODO: # FIXME: remove me
    try:
        tld = unpack_url['tld'].decode()
    except:
        tld = unpack_url['tld']

    if crawler_type=='None':
        crawler_type = None

    if crawler_type:
        if crawler_type=='tor':
            crawler_type = 'onion'
    else:
        if tld == 'onion':
            crawler_type = 'onion'
        else:
            crawler_type = 'regular'

    save_crawler_config(crawler_mode, crawler_type, crawler_config, domain, url=url)
    send_url_to_crawl_in_queue(crawler_mode, crawler_type, url)

def save_crawler_config(crawler_mode, crawler_type, crawler_config, domain, url=None):
    if crawler_mode == 'manual':
        r_cache.set('crawler_config:{}:{}:{}'.format(crawler_mode, crawler_type, domain), json.dumps(crawler_config))
    elif crawler_mode == 'auto':
        r_serv_onion.set('crawler_config:{}:{}:{}:{}'.format(crawler_mode, crawler_type, domain, url), json.dumps(crawler_config))

def send_url_to_crawl_in_queue(crawler_mode, crawler_type, url):
    print('{}_crawler_priority_queue'.format(crawler_type), '{};{}'.format(url, crawler_mode))
    r_serv_onion.sadd('{}_crawler_priority_queue'.format(crawler_type), '{};{}'.format(url, crawler_mode))
    # add auto crawled url for user UI
    if crawler_mode == 'auto':
        r_serv_onion.sadd('auto_crawler_url:{}'.format(crawler_type), url)

#### ####
#### CRAWLER TASK API ####
def api_create_crawler_task(user_id, url, screenshot=True, har=True, depth_limit=1, max_pages=100, auto_crawler=False, crawler_delta=3600, crawler_type=None, cookiejar_uuid=None, user_agent=None):
    # validate url
    if url is None or url=='' or url=='\n':
        return ({'error':'invalid depth limit'}, 400)

    if depth_limit:
        try:
            depth_limit = int(depth_limit)
            if depth_limit < 0:
                depth_limit = 0
        except ValueError:
            return ({'error':'invalid depth limit'}, 400)
    if max_pages:
        try:
            max_pages = int(max_pages)
            if max_pages < 1:
                max_pages = 1
        except ValueError:
            return ({'error':'invalid max_pages limit'}, 400)

    if auto_crawler:
        try:
            crawler_delta = int(crawler_delta)
            if crawler_delta < 0:
                return ({'error':'invalid delta bettween two pass of the crawler'}, 400)
        except ValueError:
            return ({'error':'invalid delta bettween two pass of the crawler'}, 400)

    if cookiejar_uuid:
        if not exist_cookiejar(cookiejar_uuid):
            return ({'error': 'unknow cookiejar uuid', 'cookiejar_uuid': cookiejar_uuid}, 404)
        level = get_cookiejar_level(cookiejar_uuid)
        if level == 0: # # TODO: check if user is admin
            cookie_owner = get_cookiejar_owner(cookiejar_uuid)
            if cookie_owner != user_id:
                return ({'error': 'The access to this cookiejar is restricted'}, 403)

    # # TODO: verify splash name/crawler type

    create_crawler_task(url, screenshot=screenshot, har=har, depth_limit=depth_limit, max_pages=max_pages,
                        crawler_type=crawler_type,
                        auto_crawler=auto_crawler, crawler_delta=crawler_delta, cookiejar_uuid=cookiejar_uuid, user_agent=user_agent)
    return None

#### ####

#### SPLASH API ####
def is_splash_reachable(splash_url, timeout=1.0):
    try:
        r = requests.get(splash_url , timeout=timeout)
    except Exception:
        return False
    if r.status_code == 200:
        return True
    else:
        return False
#### ####

def is_redirection(domain, last_url):
    url = urlparse(last_url)
    last_domain = url.netloc
    last_domain = last_domain.split('.')
    last_domain = '{}.{}'.format(last_domain[-2], last_domain[-1])
    return domain != last_domain

# domain up
def create_domain_metadata(domain_type, domain, current_port, date, date_month):
    # Add to global set
    r_serv_onion.sadd('{}_up:{}'.format(domain_type, date), domain)
    r_serv_onion.sadd('full_{}_up'.format(domain_type), domain)
    r_serv_onion.sadd('month_{}_up:{}'.format(domain_type, date_month), domain)

    # create onion metadata
    if not r_serv_onion.exists('{}_metadata:{}'.format(domain_type, domain)):
        r_serv_onion.hset('{}_metadata:{}'.format(domain_type, domain), 'first_seen', date)
    r_serv_onion.hset('{}_metadata:{}'.format(domain_type, domain), 'last_check', date)

    # Update domain port number
    all_domain_ports = r_serv_onion.hget('{}_metadata:{}'.format(domain_type, domain), 'ports')
    if all_domain_ports:
        all_domain_ports = all_domain_ports.split(';')
    else:
        all_domain_ports = []
    if current_port not in all_domain_ports:
        all_domain_ports.append(current_port)
        r_serv_onion.hset('{}_metadata:{}'.format(domain_type, domain), 'ports', ';'.join(all_domain_ports))

# add root_item to history
def add_domain_root_item(root_item, domain_type, domain, epoch_date, port):
    # Create/Update crawler history
    r_serv_onion.zadd('crawler_history_{}:{}:{}'.format(domain_type, domain, port), epoch_date, root_item)

def create_item_metadata(item_id, domain, url, port, item_father):
    r_serv_metadata.hset('paste_metadata:{}'.format(item_id), 'father', item_father)
    r_serv_metadata.hset('paste_metadata:{}'.format(item_id), 'domain', '{}:{}'.format(domain, port))
    r_serv_metadata.hset('paste_metadata:{}'.format(item_id), 'real_link', url)
    # add this item_id to his father
    r_serv_metadata.sadd('paste_children:{}'.format(item_father), item_id)

def create_item_id(item_dir, domain):
    if len(domain) > 215:
        UUID = domain[-215:]+str(uuid.uuid4())
    else:
        UUID = domain+str(uuid.uuid4())
    return os.path.join(item_dir, UUID)

def save_crawled_item(item_id, item_content):
    try:
        gzipencoded = gzip.compress(item_content.encode())
        gzip64encoded = base64.standard_b64encode(gzipencoded).decode()
        return gzip64encoded
    except:
        print("file error: {}".format(item_id))
        return False

def save_har(har_dir, item_id, har_content):
    if not os.path.exists(har_dir):
        os.makedirs(har_dir)
    item_id = item_id.split('/')[-1]
    filename = os.path.join(har_dir, item_id + '.json')
    with open(filename, 'w') as f:
        f.write(json.dumps(har_content))

# # TODO: FIXME
def api_add_crawled_item(dict_crawled):

    domain = None
    # create item_id item_id =

    save_crawled_item(item_id, response.data['html'])
    create_item_metadata(item_id, domain, 'last_url', port, 'father')

#### CRAWLER QUEUES ####
def get_all_crawlers_queues_types():
    all_queues_types = set()
    all_splash_name = get_all_crawlers_to_launch_splash_name()
    for splash_name in all_splash_name:
        all_queues_types.add(get_splash_crawler_type(splash_name))
    all_splash_name = list()
    return all_queues_types

def get_crawler_queue_types_by_splash_name(splash_name):
    all_domain_type = [splash_name]
    crawler_type = get_splash_crawler_type(splash_name)
    #if not is_splash_used_in_discovery(splash_name)
    if crawler_type == 'tor':
        all_domain_type.append('onion')
        all_domain_type.append('regular')
    else:
        all_domain_type.append('regular')
    return all_domain_type

def get_crawler_type_by_url(url):
    faup.decode(url)
    unpack_url = faup.get()
    ## TODO: # FIXME: remove me
    try:
        tld = unpack_url['tld'].decode()
    except:
        tld = unpack_url['tld']

    if tld == 'onion':
        crawler_type = 'onion'
    else:
        crawler_type = 'regular'
    return crawler_type


def get_elem_to_crawl_by_queue_type(l_queue_type):
    ## queues priority:
    # 1 - priority queue
    # 2 - discovery queue
    # 3 - normal queue
    ##
    all_queue_key = ['{}_crawler_priority_queue', '{}_crawler_discovery_queue', '{}_crawler_queue']

    for queue_key in all_queue_key:
        for queue_type in l_queue_type:
            message = r_serv_onion.spop(queue_key.format(queue_type))
            if message:
                dict_to_crawl = {}
                splitted = message.rsplit(';', 1)
                if len(splitted) == 2:
                    url, item_id = splitted
                    item_id = item_id.replace(PASTES_FOLDER+'/', '')
                else:
                # # TODO: to check/refractor
                    item_id = None
                    url = message
                crawler_type = get_crawler_type_by_url(url)
                return {'url': url, 'paste': item_id, 'type_service': crawler_type, 'queue_type': queue_type, 'original_message': message}
    return None

def get_nb_elem_to_crawl_by_type(queue_type):
    nb = r_serv_onion.scard('{}_crawler_priority_queue'.format(queue_type))
    nb += r_serv_onion.scard('{}_crawler_discovery_queue'.format(queue_type))
    nb += r_serv_onion.scard('{}_crawler_queue'.format(queue_type))
    return nb

#### ---- ####

# # # # # # # # # # # #
#                     #
#   SPLASH MANAGER    #
#                     #
# # # # # # # # # # # #
def get_splash_manager_url(reload=False): # TODO: add in db config
    return r_serv_onion.get('crawler:splash:manager:url')

def get_splash_api_key(reload=False): # TODO: add in db config
    return r_serv_onion.get('crawler:splash:manager:key')

def get_hidden_splash_api_key(): # TODO: add in db config
    key = get_splash_api_key()
    if key:
        if len(key)==41:
            return f'{key[:4]}*********************************{key[-4:]}'

def is_valid_api_key(api_key, search=re.compile(r'[^a-zA-Z0-9_-]').search):
    if len(api_key) != 41:
        return False
    return not bool(search(api_key))

def save_splash_manager_url_api(url, api_key):
    r_serv_onion.set('crawler:splash:manager:url', url)
    r_serv_onion.set('crawler:splash:manager:key', api_key)

def get_splash_url_from_manager_url(splash_manager_url, splash_port):
    url = urlparse(splash_manager_url)
    host = url.netloc.split(':', 1)[0]
    return '{}:{}'.format(host, splash_port)

# def is_splash_used_in_discovery(splash_name):
#     res = r_serv_onion.hget('splash:metadata:{}'.format(splash_name), 'discovery_queue')
#     if res == 'True':
#         return True
#     else:
#         return False

def restart_splash_docker(splash_url, splash_name):
    splash_port = splash_url.split(':')[-1]
    return _restart_splash_docker(splash_port, splash_name)

def is_splash_manager_connected(delta_check=30):
    last_check = r_cache.hget('crawler:splash:manager', 'last_check')
    if last_check:
        if int(time.time()) - int(last_check) > delta_check:
            ping_splash_manager()
    else:
        ping_splash_manager()
    res = r_cache.hget('crawler:splash:manager', 'connected')
    return res == 'True'

def update_splash_manager_connection_status(is_connected, req_error=None):
    r_cache.hset('crawler:splash:manager', 'connected', is_connected)
    r_cache.hset('crawler:splash:manager', 'last_check', int(time.time()))
    if not req_error:
        r_cache.hdel('crawler:splash:manager', 'error')
    else:
        r_cache.hset('crawler:splash:manager', 'status_code', req_error['status_code'])
        r_cache.hset('crawler:splash:manager', 'error', req_error['error'])

def get_splash_manager_connection_metadata(force_ping=False):
    dict_manager={}
    if force_ping:
        dict_manager['status'] = ping_splash_manager()
    else:
        dict_manager['status'] = is_splash_manager_connected()
    if not dict_manager['status']:
        dict_manager['status_code'] = r_cache.hget('crawler:splash:manager', 'status_code')
        dict_manager['error'] = r_cache.hget('crawler:splash:manager', 'error')
    return dict_manager

    ## API ##
def ping_splash_manager():
    splash_manager_url = get_splash_manager_url()
    if not splash_manager_url:
        return False
    try:
        req = requests.get('{}/api/v1/ping'.format(splash_manager_url), headers={"Authorization": get_splash_api_key()}, verify=False)
        if req.status_code == 200:
            update_splash_manager_connection_status(True)
            return True
        else:
            res = req.json()
            if 'reason' in res:
                req_error = {'status_code': req.status_code, 'error': res['reason']}
            else:
                print(req.json())
                req_error = {'status_code': req.status_code, 'error': json.dumps(req.json())}
            update_splash_manager_connection_status(False, req_error=req_error)
            return False
    except requests.exceptions.ConnectionError:
        pass
    # splash manager unreachable
    req_error = {'status_code': 500, 'error': 'splash manager unreachable'}
    update_splash_manager_connection_status(False, req_error=req_error)
    return False

def get_splash_manager_session_uuid():
    try:
        req = requests.get('{}/api/v1/get/session_uuid'.format(get_splash_manager_url()), headers={"Authorization": get_splash_api_key()}, verify=False)
        if req.status_code == 200:
            res = req.json()
            if res:
                return res['session_uuid']
        else:
            print(req.json())
    except (requests.exceptions.ConnectionError, requests.exceptions.MissingSchema):
        # splash manager unreachable
        update_splash_manager_connection_status(False)

def get_splash_manager_version():
    splash_manager_url = get_splash_manager_url()
    if splash_manager_url:
        try:
            req = requests.get('{}/api/v1/version'.format(splash_manager_url), headers={"Authorization": get_splash_api_key()}, verify=False)
            if req.status_code == 200:
                return req.json()['message']
            else:
                print(req.json())
        except requests.exceptions.ConnectionError:
            pass

def get_all_splash_manager_containers_name():
    req = requests.get('{}/api/v1/get/splash/all'.format(get_splash_manager_url()), headers={"Authorization": get_splash_api_key()}, verify=False)
    if req.status_code == 200:
        return req.json()
    else:
        print(req.json())

def get_all_splash_manager_proxies():
    req = requests.get('{}/api/v1/get/proxies/all'.format(get_splash_manager_url()), headers={"Authorization": get_splash_api_key()}, verify=False)
    if req.status_code == 200:
        return req.json()
    else:
        print(req.json())

def _restart_splash_docker(splash_port, splash_name):
    dict_to_send = {'port': splash_port, 'name': splash_name}
    req = requests.post('{}/api/v1/splash/restart'.format(get_splash_manager_url()), headers={"Authorization": get_splash_api_key()}, verify=False, json=dict_to_send)
    if req.status_code == 200:
        return req.json()
    else:
        print(req.json())

def api_save_splash_manager_url_api(data):
    # unpack json
    manager_url = data.get('url', None)
    api_key = data.get('api_key', None)
    if not manager_url or not api_key:
        return ({'status': 'error', 'reason': 'No url or API key supplied'}, 400)
    # check if is valid url
    try:
        result = urlparse(manager_url)
        if not all([result.scheme, result.netloc]):
            return ({'status': 'error', 'reason': 'Invalid url'}, 400)
    except:
        return ({'status': 'error', 'reason': 'Invalid url'}, 400)

    # check if is valid key
    if not is_valid_api_key(api_key):
        return ({'status': 'error', 'reason': 'Invalid API key'}, 400)

    save_splash_manager_url_api(manager_url, api_key)
    return ({'url': manager_url, 'api_key': get_hidden_splash_api_key()}, 200)
    ## -- ##

    ## SPLASH ##
def get_all_splash(r_list=False):
    res = r_serv_onion.smembers('all_splash')
    if res:
        if r_list:
            return list(res)
        else:
            return res
    else:
        return []

def get_splash_proxy(splash_name):
    return r_serv_onion.hget('splash:metadata:{}'.format(splash_name), 'proxy')

def get_splash_all_url(splash_name, r_list=False):
    res = r_serv_onion.smembers('splash:url:{}'.format(splash_name))
    if res:
        if r_list:
            return list(res)
        else:
            return res
    else:
        return []

def get_splash_name_by_url(splash_url):
    return r_serv_onion.get('splash:map:url:name:{}'.format(splash_url))

def get_splash_crawler_type(splash_name):
    return r_serv_onion.hget('splash:metadata:{}'.format(splash_name), 'crawler_type')

def get_splash_crawler_description(splash_name):
    return r_serv_onion.hget('splash:metadata:{}'.format(splash_name), 'description')

def get_splash_crawler_metadata(splash_name):
    dict_splash = {}
    dict_splash['proxy'] = get_splash_proxy(splash_name)
    dict_splash['type'] = get_splash_crawler_type(splash_name)
    dict_splash['description'] = get_splash_crawler_description(splash_name)
    return dict_splash

def get_all_splash_crawler_metadata():
    dict_splash = {}
    for splash_name in get_all_splash():
        dict_splash[splash_name] = get_splash_crawler_metadata(splash_name)
    return dict_splash

def get_all_splash_by_proxy(proxy_name, r_list=False):
    res = r_serv_onion.smembers('proxy:splash:{}'.format(proxy_name))
    if res:
        if r_list:
            return list(res)
        else:
            return res
    else:
        return []

def get_all_splash_name_by_crawler_type(crawler_type):
    l_splash_name = []
    for splash_name in get_all_splash():
        if get_splash_crawler_type(splash_name) == crawler_type:
            l_splash_name.append(splash_name)
    return l_splash_name

def get_all_splash_url_by_crawler_type(crawler_type):
    l_splash_url = []
    for splash_name in get_all_splash_name_by_crawler_type(crawler_type):
        for splash_url in get_splash_all_url(splash_name, r_list=True):
            l_splash_url.append(splash_url)
    return l_splash_url

def delete_all_splash_containers():
    for splash_name in get_all_splash():
        delete_splash_container(splash_name)

def delete_splash_container(splash_name):
    r_serv_onion.srem('proxy:splash:{}'.format(get_splash_proxy(splash_name)), splash_name)
    r_serv_onion.delete('splash:metadata:{}'.format(splash_name))

    for splash_url in get_splash_all_url(splash_name):
        r_serv_onion.delete('splash:map:url:name:{}'.format(splash_url), splash_name)
        r_serv_onion.srem('splash:url:{}'.format(splash_name), splash_url)
    r_serv_onion.srem('all_splash', splash_name)
    ## -- ##

    ## PROXY ##
def get_all_proxies(r_list=False):
    res = r_serv_onion.smembers('all_proxy')
    if res:
        return list(res)
    else:
        return []

def delete_all_proxies():
    for proxy_name in get_all_proxies():
        delete_proxy(proxy_name)

def get_proxy_host(proxy_name):
    return r_serv_onion.hget('proxy:metadata:{}'.format(proxy_name), 'host')

def get_proxy_port(proxy_name):
    return r_serv_onion.hget('proxy:metadata:{}'.format(proxy_name), 'port')

def get_proxy_type(proxy_name):
    return r_serv_onion.hget('proxy:metadata:{}'.format(proxy_name), 'type')

def get_proxy_crawler_type(proxy_name):
    return r_serv_onion.hget('proxy:metadata:{}'.format(proxy_name), 'crawler_type')

def get_proxy_description(proxy_name):
    return r_serv_onion.hget('proxy:metadata:{}'.format(proxy_name), 'description')

def get_proxy_metadata(proxy_name):
    meta_dict = {}
    meta_dict['host'] = get_proxy_host(proxy_name)
    meta_dict['port'] = get_proxy_port(proxy_name)
    meta_dict['type'] = get_proxy_type(proxy_name)
    meta_dict['crawler_type'] = get_proxy_crawler_type(proxy_name)
    meta_dict['description'] = get_proxy_description(proxy_name)
    return meta_dict

def get_all_proxies_metadata():
    all_proxy_dict = {}
    for proxy_name in get_all_proxies():
        all_proxy_dict[proxy_name] = get_proxy_metadata(proxy_name)
    return all_proxy_dict

# def set_proxy_used_in_discovery(proxy_name, value):
#     r_serv_onion.hset('splash:metadata:{}'.format(splash_name), 'discovery_queue', value)

def delete_proxy(proxy_name): # # TODO: force delete (delete all proxy)
    proxy_splash = get_all_splash_by_proxy(proxy_name)
    #if proxy_splash:
    #    print('error, a splash container is using this proxy')
    r_serv_onion.delete('proxy:metadata:{}'.format(proxy_name))
    r_serv_onion.srem('all_proxy', proxy_name)
    ## -- ##

    ## LOADER ##
def load_all_splash_containers():
    delete_all_splash_containers()
    all_splash_containers_name = get_all_splash_manager_containers_name()
    for splash_name in all_splash_containers_name:
        r_serv_onion.sadd('all_splash', splash_name)

        proxy = all_splash_containers_name[splash_name]['proxy']
        if not proxy:
            proxy = {'name': 'no_proxy', 'crawler_type': 'web'}

        r_serv_onion.sadd('proxy:splash:{}'.format(proxy['name']), splash_name)

        r_serv_onion.hset('splash:metadata:{}'.format(splash_name), 'crawler_type', proxy['crawler_type'])
        r_serv_onion.hset('splash:metadata:{}'.format(splash_name), 'proxy', proxy['name'])
        description = all_splash_containers_name[splash_name].get('description', None)
        if description:
            r_serv_onion.hset('splash:metadata:{}'.format(splash_name), 'description', description)

        for port in all_splash_containers_name[splash_name]['ports']:
            splash_url = get_splash_url_from_manager_url(get_splash_manager_url(), port)
            r_serv_onion.sadd('splash:url:{}'.format(splash_name), splash_url)
            r_serv_onion.set('splash:map:url:name:{}'.format(splash_url), splash_name)

def load_all_proxy():
    delete_all_proxies()
    all_proxies = get_all_splash_manager_proxies()
    for proxy_name in all_proxies:
        proxy_dict = all_proxies[proxy_name]
        r_serv_onion.hset('proxy:metadata:{}'.format(proxy_name), 'host', proxy_dict['host'])
        r_serv_onion.hset('proxy:metadata:{}'.format(proxy_name), 'port', proxy_dict['port'])
        r_serv_onion.hset('proxy:metadata:{}'.format(proxy_name), 'type', proxy_dict['type'])
        r_serv_onion.hset('proxy:metadata:{}'.format(proxy_name), 'crawler_type', proxy_dict['crawler_type'])
        description = all_proxies[proxy_name].get('description', None)
        if description:
            r_serv_onion.hset('proxy:metadata:{}'.format(proxy_name), 'description', description)
        r_serv_onion.sadd('all_proxy', proxy_name)

def reload_splash_and_proxies_list():
    if ping_splash_manager():
        # LOAD PROXIES containers
        load_all_proxy()
        # LOAD SPLASH containers
        load_all_splash_containers()
        return True
    else:
        return False
    # # TODO: kill crawler screen ?
    ## -- ##

    ## SPLASH CONTROLLER ##
def launch_ail_splash_crawler(splash_url, script_options=''):
    screen_name = 'Crawler_AIL'
    dir_project = os.environ['AIL_HOME']
    script_location = os.path.join(os.environ['AIL_BIN'])
    script_name = 'Crawler.py'
    screen.create_screen(screen_name)
    screen.launch_uniq_windows_script(screen_name, splash_url, dir_project, script_location, script_name, script_options=script_options, kill_previous_windows=True)

def is_test_ail_crawlers_successful():
    return r_serv_onion.hget('crawler:tor:test', 'success') == 'True'

def get_test_ail_crawlers_message():
    return r_serv_onion.hget('crawler:tor:test', 'message')

def save_test_ail_crawlers_result(test_success, message):
    r_serv_onion.hset('crawler:tor:test', 'success', bool(test_success))
    r_serv_onion.hset('crawler:tor:test', 'message', message)

def test_ail_crawlers():
    # # TODO: test regular domain
    if not ping_splash_manager():
        manager_url = get_splash_manager_url()
        error_message = f'Error: Can\'t connect to AIL Splash Manager, http://{manager_url}'
        print(error_message)
        save_test_ail_crawlers_result(False, error_message)
        return False

    splash_url = get_all_splash_url_by_crawler_type('tor')
    if not splash_url:
        error_message = f'Error: No Tor Splash Launched'
        print(error_message)
        save_test_ail_crawlers_result(False, error_message)
        return False
    splash_url = splash_url[0]
    commit_id = git_status.get_last_commit_id_from_local()
    crawler_options = {'html': True,
                        'har': False,
                        'png': False,
                        'depth_limit': 0,
                        'closespider_pagecount': 100,
                        'cookiejar_uuid': None,
                        'user_agent': commit_id + '-AIL SPLASH CRAWLER'}
    date = {'date_day': datetime.now().strftime("%Y%m%d"),
            'date_month': datetime.now().strftime("%Y%m"),
            'epoch': int(time.time())}
    crawler_config = {'splash_url': f'http://{splash_url}',
                        'service_type': 'onion',
                        'url': 'http://eswpccgr5xyovsahffkehgleqthrasfpfdblwbs4lstd345dwq5qumqd.onion',
                        'domain': 'eswpccgr5xyovsahffkehgleqthrasfpfdblwbs4lstd345dwq5qumqd.onion',
                        'port': 80,
                        'original_item': None,
                        'item': None,
                        'crawler_options': crawler_options,
                        'date': date,
                        'requested': 'test'}

    ## CHECK IF SPLASH AVAILABLE ##
    try:
        r = requests.get(f'http://{splash_url}' , timeout=30.0)
        retry = False
    except Exception as e:
        error_message = f'Error: Can\'t connect to Splash Docker, http://{splash_url}'
        print(error_message)
        save_test_ail_crawlers_result(False, error_message)
        return False
    ## -- ##

    ## LAUNCH CRAWLER, TEST MODE ##
    set_current_crawler_status(splash_url, 'CRAWLER TEST', started_time=True, crawled_domain='TEST DOMAIN', crawler_type='onion')
    UUID = str(uuid.uuid4())
    r_cache.set('crawler_request:{}'.format(UUID), json.dumps(crawler_config))

    ## LAUNCH CRAWLER, TEST MODE ##
    tor_crawler_script = os.path.join(os.environ['AIL_BIN'], 'torcrawler/tor_crawler.py')
    process = subprocess.Popen(["python", tor_crawler_script, UUID],
                               stdout=subprocess.PIPE)
    while process.poll() is None:
        time.sleep(1)

    if process.returncode == 0:
        # Scrapy-Splash ERRORS
        stderr = process.stdout.read().decode()
        #print(stderr)
        if stderr:
            print(f'stderr: {stderr}')
            save_test_ail_crawlers_result(False, f'Error: {stderr}')
            set_current_crawler_status(splash_url, 'Error')

        output = process.stdout.read().decode()
        #print(output)
        # error: splash:Connection to proxy refused
        if 'Connection to proxy refused' in output:
            print('{} SPASH, PROXY DOWN OR BAD CONFIGURATION'.format(splash_url))
            save_test_ail_crawlers_result(False, 'SPASH, PROXY DOWN OR BAD CONFIGURATION')
            set_current_crawler_status(splash_url, 'Error')
            return False
        else:
            set_current_crawler_status(splash_url, 'Waiting')
            return True
    else:
        # ERROR
        stderr = process.stdout.read().decode()
        output = process.stdout.read().decode()
        error = f'-stderr-\n{stderr}\n-stdout-\n{output}'
        print(error)
        save_test_ail_crawlers_result(splash_url, error)
        return False
    return True
    ## -- ##

#### ---- ####

#### CRAWLER PROXY ####

#### ---- ####

if __name__ == '__main__':
    res = get_splash_manager_version()
    res = test_ail_crawlers()
    res = is_test_ail_crawlers_successful()
    print(res)
    print(get_test_ail_crawlers_message())
