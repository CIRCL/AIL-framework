#!/usr/bin/python3

"""
API Helper
===================


"""
import base64
import gzip
import hashlib
import json
import os
import pickle
import re
import sys
import time
import uuid

from enum import IntEnum, unique
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
#from bs4 import BeautifulSoup

from pylacus import PyLacus

from pyfaup.faup import Faup

# interact with splash_crawler API
import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from packages import git_status
from lib.ConfigLoader import ConfigLoader
from lib.objects.Domains import Domain
from core import screen

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
r_crawler = config_loader.get_db_conn("Kvrocks_Crawler")
r_cache = config_loader.get_redis_conn("Redis_Cache")

r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")

ITEMS_FOLDER = config_loader.get_config_str("Directories", "pastes")
HAR_DIR = config_loader.get_files_directory('har')
activate_crawler = config_loader.get_config_str("Crawler", "activate_crawler")
config_loader = None

faup = Faup()

# # # # # # # #
#             #
#   COMMON    #
#             #
# # # # # # # #

def gen_uuid():
    return str(uuid.uuid4())

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')

# # TODO: remove me ?
def get_current_date(separator=False):
    if separator:
        return datetime.now().strftime("%Y/%m/%d")
    else:
        return datetime.now().strftime("%Y%m%d")

def get_date_crawled_items_source(date):
    return os.path.join('crawled', date)

def get_date_har_dir(date):
    return os.path.join(HAR_DIR, date)

def is_valid_onion_domain(domain):
    if not domain.endswith('.onion'):
        return False
    domain = domain.replace('.onion', '', 1)
    if len(domain) == 16:  # v2 address
        r_onion = r'[a-z0-9]{16}'
        if re.match(r_onion, domain):
            return True
    elif len(domain) == 56:  # v3 address
        r_onion = r'[a-z0-9]{56}'
        if re.fullmatch(r_onion, domain):
            return True
    return False

def get_faup():
    return faup

def unpack_url(url):
    f = get_faup()
    f.decode(url)
    url_decoded = f.get()
    port = url_decoded['port']
    if not port:
        if url_decoded['scheme'] == 'http':
            port = 80
        elif url_decoded['scheme'] == 'https':
            port = 443
        else:
            port = 80
        url_decoded['port'] = port
    # decode URL
    try:
        url = url_decoded['url'].decode()
    except AttributeError:
        url = url_decoded['url']
    # if not url_decoded['scheme']:
    #     url = f'http://{url}'

    # Fix case
    url_decoded['domain'] = url_decoded['domain'].lower()
    url_decoded['url'] = url.replace(url_decoded['host'], url_decoded['host'].lower(), 1)
    return url_decoded

# # # # # # # #
#             #
#   FAVICON   # TODO REWRITE ME
#             #
# # # # # # # #

def get_favicon_from_html(html, domain, url):
    favicon_urls = extract_favicon_from_html(html, url)
    # add root favicon
    if not favicon_urls:
        favicon_urls.add(f'{urlparse(url).scheme}://{domain}/favicon.ico')
    print(favicon_urls)
    return favicon_urls

def extract_favicon_from_html(html, url):
    favicon_urls = set()
    soup = BeautifulSoup(html, 'html.parser')
    set_icons = set()
    # If there are multiple <link rel="icon">s, the browser uses their media,
    # type, and sizes attributes to select the most appropriate icon.
    # If several icons are equally appropriate, the last one is used.
    # If the most appropriate icon is later found to be inappropriate,
    # for example because it uses an unsupported format,
    # the browser proceeds to the next-most appropriate, and so on.
    # # DEBUG: /!\ firefox load all favicon ???

    # iOS Safari 'apple-touch-icon'
    # Safari pinned tabs 'mask-icon'
    # Android Chrome 'manifest'
    # Edge and IE 12:
    #   - <meta name="msapplication-TileColor" content="#aaaaaa"> <meta name="theme-color" content="#ffffff">
    #   - <meta name="msapplication-config" content="/icons/browserconfig.xml">

    # desktop browser 'shortcut icon' (older browser), 'icon'
    for favicon_tag in ['icon', 'shortcut icon']:
        if soup.head:
            for icon in soup.head.find_all('link', attrs={'rel': lambda x : x and x.lower() == favicon_tag, 'href': True}):
                set_icons.add(icon)

    # # TODO: handle base64 favicon
    for tag in set_icons:
        icon_url = tag.get('href')
        if icon_url:
            if icon_url.startswith('//'):
                icon_url = icon_url.replace('//', '/')
            if icon_url.startswith('data:'):
                # # TODO: handle base64 favicon
                pass
            else:
                icon_url = urljoin(url, icon_url)
                icon_url = urlparse(icon_url, scheme=urlparse(url).scheme).geturl()
                favicon_urls.add(icon_url)
    return favicon_urls


# # # - - # # #


################################################################################

# # TODO: handle prefix cookies
# # TODO: fill empty fields
def create_cookie_crawler(cookie_dict, domain, crawler_type='web'):
    # check cookie domain filed
    if not 'domain' in cookie_dict:
        cookie_dict['domain'] = f'.{domain}'

    # tor browser: disable secure cookie
    if crawler_type == 'onion':
        cookie_dict['secure'] = False

    # force cookie domain
    # url = urlparse(browser_cookie['Host raw'])
    # domain = url.netloc.split(':', 1)[0]
    # cookie_dict['domain'] = '.{}'.format(domain)

    # change expire date
    cookie_dict['expires'] = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    return cookie_dict

def load_crawler_cookies(cookiejar_uuid, domain, crawler_type='web'):
    cookies = get_cookiejar_cookies_list(cookiejar_uuid)
    all_cookies = []
    for cookie_dict in cookies:
        all_cookies.append(create_cookie_crawler(cookie_dict, domain, crawler_type=crawler_type))
    return all_cookies

################################################################################

def get_all_cookiejar():
    return r_serv_onion.smembers('cookiejar:all')

def get_global_cookiejar():
    cookiejars = r_serv_onion.smembers('cookiejar:global')
    if not cookiejars:
        cookiejars = []
    return cookiejars

def get_user_cookiejar(user_id):
    cookiejars = r_serv_onion.smembers('cookiejar:user:{}'.format(user_id))
    if not cookiejars:
        cookiejars = []
    return cookiejars

def exist_cookiejar(cookiejar_uuid):
    return r_serv_onion.exists('cookiejar_metadata:{}'.format(cookiejar_uuid))

def _set_cookiejar_date(cookiejar_uuid, date):
    r_serv_onion.hset(f'cookiejar_metadata:{cookiejar_uuid}', 'date', date)

# # TODO: sanitize cookie_uuid
def create_cookiejar(user_id, level=1, description=None, cookiejar_uuid=None):
    if not cookiejar_uuid:
        cookiejar_uuid = str(uuid.uuid4())

    r_serv_onion.sadd('cookiejar:all', cookiejar_uuid)
    if level == 0:
        r_serv_onion.sadd(f'cookiejar:user:{user_id}', cookiejar_uuid)
    else:
        r_serv_onion.sadd('cookiejar:global', cookiejar_uuid)
    # metadata
    r_serv_onion.hset(f'cookiejar_metadata:{cookiejar_uuid}', 'user_id', user_id)
    r_serv_onion.hset(f'cookiejar_metadata:{cookiejar_uuid}', 'level', level)
    r_serv_onion.hset(f'cookiejar_metadata:{cookiejar_uuid}', 'description', description)
    _set_cookiejar_date(cookiejar_uuid, datetime.now().strftime("%Y%m%d"))

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
    cookies = r_serv_onion.smembers('cookiejar:{}:cookies:uuid'.format(cookiejar_uuid))
    if not cookies:
        cookies = []
    return cookies

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
    level = r_serv_onion.hget('cookiejar_metadata:{}'.format(cookiejar_uuid), 'level')
    if not level:
        level = 1
    return int(level)

def get_cookiejar_metadata(cookiejar_uuid, level=False):
    dict_cookiejar = {}
    if exist_cookiejar(cookiejar_uuid):
        dict_cookiejar['cookiejar_uuid'] = cookiejar_uuid
        dict_cookiejar['description'] = get_cookiejar_description(cookiejar_uuid)
        dict_cookiejar['date'] = get_cookiejar_date(cookiejar_uuid)
        dict_cookiejar['user_id'] = get_cookiejar_owner(cookiejar_uuid)
        if level:
            dict_cookiejar['level'] = get_cookiejar_level(cookiejar_uuid)
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
    if int(r_serv_onion.scard(f'cookies:map:cookiejar:{cookie_uuid}')) > 0:
        return True
    return False

def get_cookie_value(cookie_uuid, name):
    return r_serv_onion.hget(f'cookiejar:cookie:{cookie_uuid}', name)

def set_cookie_value(cookie_uuid, name, value):
    r_serv_onion.hset(f'cookiejar:cookie:{cookie_uuid}', name, value)

def delete_cookie_value(cookie_uuid, name):
    r_serv_onion.hdel(f'cookiejar:cookie:{cookie_uuid}', name)

def get_cookie_dict(cookie_uuid):
    cookie_dict = {}
    for key_name in r_serv_onion.hkeys(f'cookiejar:cookie:{cookie_uuid}'):
        cookie_dict[key_name] = get_cookie_value(cookie_uuid, key_name)
    return cookie_dict

# name, value, path=None, httpOnly=None, secure=None, domain=None, text=None
def add_cookie_to_cookiejar(cookiejar_uuid, cookie_dict, cookie_uuid=None):
    # # TODO: sanitize cookie_uuid
    if not cookie_uuid:
        cookie_uuid = generate_uuid()
    r_serv_onion.sadd(f'cookiejar:{cookiejar_uuid}:cookies:uuid', cookie_uuid)
    r_serv_onion.sadd(f'cookies:map:cookiejar:{cookie_uuid}', cookiejar_uuid)

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
    r_serv_onion.srem(f'cookiejar:{cookiejar_uuid}:cookies:uuid', cookie_uuid)
    r_serv_onion.srem(f'cookies:map:cookiejar:{cookie_uuid}', cookiejar_uuid)
    if not exists_cookie(cookie_uuid):
        r_serv_onion.delete(f'cookiejar:cookie:{cookie_uuid}')

def edit_cookie(cookiejar_uuid, cookie_uuid, cookie_dict):
    # delete old keys
    for key_name in r_serv_onion.hkeys(f'cookiejar:cookie:{cookie_uuid}'):
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
    resp = import_cookies_from_json(json_cookies, cookiejar_uuid)
    if resp:
        return resp, 400
#### ####

#### COOKIES API ####

def api_verify_basic_cookiejar(cookiejar_uuid, user_id):
    if not exist_cookiejar(cookiejar_uuid):
        return {'error': 'unknown cookiejar uuid', 'cookiejar_uuid': cookiejar_uuid}, 404
    level = get_cookiejar_level(cookiejar_uuid)
    if level == 0: # # TODO: check if user is admin
        cookie_owner = get_cookiejar_owner(cookiejar_uuid)
        if cookie_owner != user_id:
            return {'error': 'The access to this cookiejar is restricted'}, 403

def api_get_cookiejar_cookies(cookiejar_uuid, user_id):
    resp = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if resp:
        return resp
    resp = get_cookiejar_cookies_list(cookiejar_uuid)
    return resp, 200

def api_edit_cookiejar_description(user_id, cookiejar_uuid, description):
    resp = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if resp:
        return resp
    edit_cookiejar_description(cookiejar_uuid, description)
    return {'cookiejar_uuid': cookiejar_uuid}, 200

def api_get_cookiejar_cookies_with_uuid(cookiejar_uuid, user_id):
    resp = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if resp:
        return resp
    resp = get_cookiejar_cookies_list(cookiejar_uuid, add_cookie_uuid=True)
    return resp, 200

def api_get_cookies_list_select(user_id):
    l_cookiejar = []
    for cookies_uuid in get_global_cookiejar():
        l_cookiejar.append(f'{get_cookiejar_description(cookies_uuid)} : {cookies_uuid}')
    for cookies_uuid in get_user_cookiejar(user_id):
        l_cookiejar.append(f'{get_cookiejar_description(cookies_uuid)} : {cookies_uuid}')
    return sorted(l_cookiejar)

def api_delete_cookie_from_cookiejar(user_id, cookiejar_uuid, cookie_uuid):
    resp = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if resp:
        return resp
    delete_cookie_from_cookiejar(cookiejar_uuid, cookie_uuid)
    return {'cookiejar_uuid': cookiejar_uuid, 'cookie_uuid': cookie_uuid}, 200

def api_delete_cookie_jar(user_id, cookiejar_uuid):
    resp = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if resp:
        return resp
    delete_cookie_jar(cookiejar_uuid)
    return {'cookiejar_uuid': cookiejar_uuid}, 200

def api_edit_cookie(user_id, cookiejar_uuid, cookie_uuid, cookie_dict):
    resp = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if resp:
        return resp
    if 'name' not in cookie_dict or 'value' not in cookie_dict or cookie_dict['name'] == '':
        return {'error': 'cookie name or value not provided'}, 400
    edit_cookie(cookiejar_uuid, cookie_uuid, cookie_dict)
    return get_cookie_dict(cookie_uuid), 200

def api_create_cookie(user_id, cookiejar_uuid, cookie_dict):
    resp = api_verify_basic_cookiejar(cookiejar_uuid, user_id)
    if resp:
        return resp
    if 'name' not in cookie_dict or 'value' not in cookie_dict or cookie_dict['name'] == '':
        return {'error': 'cookie name or value not provided'}, 400
    resp = add_cookie_to_cookiejar(cookiejar_uuid, cookie_dict)
    return resp, 200

#### ####

# # # # # # # #
#             #
#   CRAWLER   # ###################################################################################
#             #
# # # # # # # #


@unique
class CaptureStatus(IntEnum):
    """The status of the capture"""
    UNKNOWN = -1
    QUEUED = 0
    DONE = 1
    ONGOING = 2

def get_default_user_agent():
    return 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'

def get_blacklist():
    return r_crawler.smembers('blacklist:domain')

def is_blacklisted_domain(domain):
    return r_crawler.sismember('blacklist:domain', domain)

def blacklist_domain(domain):
    return r_crawler.sadd('blacklist:domain', domain)

def load_blacklist():
    try:
        with open(os.path.join(os.environ['AIL_BIN'], 'crawlers/blacklist.txt'), 'r') as f:
            r_crawler.delete('blacklist:domain')
            lines = f.read().splitlines()
            for line in lines:
                blacklist_domain(line)
    # TODO LOG
    except Exception as e:
        print(e)

def get_last_crawled_domains(domain_type):
    return r_crawler.lrange(f'last_{domain_type}', 0, -1)

def update_last_crawled_domain(domain_type, domain, epoch):
    # update list, last crawled domains
    r_crawler.lpush(f'last_{domain_type}', f'{domain}:{epoch}')
    r_crawler.ltrim(f'last_{domain_type}', 0, 15)

def create_item_metadata(item_id, domain, url, item_father):
    r_serv_metadata.hset(f'paste_metadata:{item_id}', 'father', item_father)
    r_serv_metadata.hset(f'paste_metadata:{item_id}', 'domain', domain)
    r_serv_metadata.hset(f'paste_metadata:{item_id}', 'real_link', url)
    # add this item_id to his father
    r_serv_metadata.sadd(f'paste_children:{item_father}', item_id)

def get_gzipped_b64_item(item_id, content):
    try:
        gzipencoded = gzip.compress(content.encode())
        gzip64encoded = base64.standard_b64encode(gzipencoded).decode()
        return gzip64encoded
    except:
        print(f'file error: {item_id}')
        return False

def get_crawlers_stats_by_day(date, domain_type):
    return {
        'date': date[0:4] + '-' + date[4:6] + '-' + date[6:8],
        'up': r_crawler.scard(f'{domain_type}_up:{date}'),
        'down': r_crawler.scard(f'{domain_type}_down:{date}'),
    }


def get_crawlers_stats(domain_type=None):
    stats = {}
    date = datetime.now().strftime("%Y%m%d")
    if domain_type:
        domain_types = [domain_type]
    else:
        domain_types = get_crawler_all_types()
    for domain_type in domain_types:
        queue = r_crawler.scard(f'crawler:queue:type:{domain_type}')
        up = r_crawler.scard(f'{domain_type}_up:{date}')
        down = r_crawler.scard(f'{domain_type}_down:{date}')
        crawled = up + down
        stats[domain_type] = {'queue': queue, 'up': up, 'down': down, 'crawled': crawled}
    return stats

#### CRAWLER STATE ####

# TODO SET IN UI OR USE DEFAULT
def get_crawler_max_captures():
    return 10

def get_nb_crawler_captures():
    return r_cache.zcard('crawler:captures')

def get_crawler_captures():
    return r_crawler.zrange('crawler:captures', 0, -1)

def reload_crawler_captures():
    r_cache.delete('crawler:captures')
    for capture in get_crawler_captures():
        r_cache.zadd('crawler:captures', {capture[0]: capture[1]})

def get_crawler_capture():
    return r_cache.zpopmin('crawler:captures')

def update_crawler_capture(capture_uuid):
    last_check = int(time.time())
    r_cache.zadd('crawler:captures', {capture_uuid: last_check})

def get_crawler_capture_task_uuid(capture_uuid):
    return r_crawler.hget('crawler:captures:tasks', capture_uuid)

def add_crawler_capture(task_uuid, capture_uuid):
    launch_time = int(time.time())
    r_crawler.hset(f'crawler:task:{task_uuid}', 'capture', capture_uuid)
    r_crawler.hset('crawler:captures:tasks', capture_uuid, task_uuid)
    r_crawler.zadd('crawler:captures', {capture_uuid: launch_time})
    r_cache.zadd('crawler:captures', {capture_uuid: launch_time})

def remove_crawler_capture(capture_uuid):
    r_crawler.zrem('crawler:captures', capture_uuid)
    r_crawler.hdel('crawler:captures:tasks', capture_uuid)

def get_crawler_capture_status():
    status = []
    for capture_uuid in get_crawler_captures():
        task_uuid = get_crawler_capture_task_uuid(capture_uuid)
        domain = get_crawler_task_domain(task_uuid)
        dom = Domain(domain)
        meta = {
            'uuid': task_uuid,
            'domain': dom.get_id(),
            'type': dom.get_domain_type(),
            'start_time': get_crawler_task_start_time(task_uuid),
            'status': 'test',
        }
        status.append(meta)
    return status

##-- CRAWLER STATE --##

#### CRAWLER TASK ####

def get_crawler_task_url(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'url')

def get_crawler_task_domain(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'domain')

def get_crawler_task_depth(task_uuid):
    depth = r_crawler.hget(f'crawler:task:{task_uuid}', 'depth')
    if not depth:
        depth = 1
    return int(depth)

def get_crawler_task_har(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'har') == '1'

def get_crawler_task_screenshot(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'screenshot') == '1'

def get_crawler_task_user_agent(task_uuid):
    user_agent = r_crawler.hget(f'crawler:task:{task_uuid}', 'user_agent')
    if not user_agent:
        user_agent = get_default_user_agent()
    return user_agent

def get_crawler_task_cookiejar(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'cookiejar')

def get_crawler_task_header(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'header')

def get_crawler_task_proxy(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'proxy')

def get_crawler_task_parent(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'parent')

def get_crawler_task_hash(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'hash')

def get_crawler_task_start_time(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'start_time')

def get_crawler_task_status(task_uuid):
    return r_crawler.hget(f'crawler:task:{task_uuid}', 'status')

def get_crawler_task_capture(task_uuid):
    return r_crawler.hset(f'crawler:task:{task_uuid}', 'capture')

def get_crawler_task(task_uuid):
    meta = {
        'uuid': task_uuid,
        'url': get_crawler_task_url(task_uuid),
        'domain': get_crawler_task_domain(task_uuid),
        'depth': get_crawler_task_depth(task_uuid),
        'har': get_crawler_task_har(task_uuid),
        'screenshot': get_crawler_task_screenshot(task_uuid),
        'user_agent': get_crawler_task_user_agent(task_uuid),
        'cookiejar': get_crawler_task_cookiejar(task_uuid),
        'header': get_crawler_task_header(task_uuid),
        'proxy': get_crawler_task_proxy(task_uuid),
        'parent': get_crawler_task_parent(task_uuid),
    }
    return meta

def get_task_status(task_uuid):
    domain = get_crawler_task_domain(task_uuid)
    dom = Domain(domain)
    meta = {
        'uuid': task_uuid,
        'domain': dom.get_id(),
        'domain_type': dom.get_domain_type(),
        'start_time': get_crawler_task_start_time(task_uuid),
        'status': 'test',
    }
    return meta

# domain -> uuid
def get_task_hash(url, domain, depth, har, screenshot, priority, proxy, cookiejar, user_agent, header):
    to_enqueue = {'domain': domain, 'depth': depth, 'har': har, 'screenshot': screenshot,
                  'priority': priority, 'proxy': proxy, 'cookiejar': cookiejar, 'user_agent': user_agent,
                  'header': header}
    if priority != 0:
        to_enqueue['url'] = url
    return hashlib.sha512(pickle.dumps(to_enqueue)).hexdigest()

# TODO STATUS UPDATE
# PRIORITY:  discovery = 0/10, feeder = 10, manual = 50, auto = 40, test = 100
def add_crawler_task(url, depth=1, har=True, screenshot=True, header=None, cookiejar=None, proxy=None, user_agent=None, parent='manual', priority=0):
    url_decoded = unpack_url(url)
    url = url_decoded['url']
    domain = url_decoded['domain']
    dom = Domain(domain)

    # Discovery crawler
    if priority == 0:
        if is_blacklisted_domain(dom.get_id()):
            return None
        if not dom.exists():
            priority = 10
        # Domain Crawled today or UP this month
        if dom.is_down_today() or dom.is_up_this_month():
            return None

    har = int(har)
    screenshot = int(screenshot)

    # TODO SELECT PROXY -> URL  TODO SELECT PROXY
    if proxy == 'web':
        proxy = None
    else:
        proxy = 'force_tor'
    if not user_agent:
        user_agent = get_default_user_agent()

    # TODO COOKIEJAR -> UUID
    if cookiejar:
        pass

    # Check if already in queue
    hash_query = get_task_hash(url, domain, depth, har, screenshot, priority, proxy, cookiejar, user_agent, header)
    if r_crawler.hexists(f'crawler:queue:hash', hash_query):
        return r_crawler.hget(f'crawler:queue:hash', hash_query)

    # TODO ADD TASK STATUS -----
    task_uuid = gen_uuid()  # TODO Save hash ??? (just to be safe and remove it)
    r_crawler.hset(f'crawler:task:{task_uuid}', 'domain', domain)
    r_crawler.hset(f'crawler:task:{task_uuid}', 'url', url)
    r_crawler.hset(f'crawler:task:{task_uuid}', 'depth', int(depth))
    r_crawler.hset(f'crawler:task:{task_uuid}', 'har', har)
    r_crawler.hset(f'crawler:task:{task_uuid}', 'screenshot', har)
    r_crawler.hset(f'crawler:task:{task_uuid}', 'user_agent', user_agent)
    r_crawler.hset(f'crawler:task:{task_uuid}', 'proxy', proxy)
    if cookiejar:
        r_crawler.hset(f'crawler:task:{task_uuid}', 'cookiejar', cookiejar) # TODO
    if header:
        r_crawler.hset(f'crawler:task:{task_uuid}', 'header', header)
    r_crawler.hset(f'crawler:task:{task_uuid}', 'hash', hash_query)

    r_crawler.hset(f'crawler:task:{task_uuid}', 'parent', parent)

    r_crawler.hset('crawler:queue:hash', hash_query, task_uuid)
    r_crawler.zadd('crawler:queue', {task_uuid: priority})
    # UI
    r_crawler.sadd(f'crawler:queue:type:{dom.get_domain_type()}', task_uuid)
    return task_uuid

def get_crawler_task_from_queue():
    task_uuid = r_crawler.zpopmax('crawler:queue')
    if not task_uuid or not task_uuid[0]:
        return None
    task_uuid, priority = task_uuid[0]
    r_crawler.sadd('crawler:queue:queued', task_uuid)
    r_crawler.hset(f'crawler:task:{task_uuid}', 'start_time', datetime.now().strftime("%Y/%m/%d  -  %H:%M.%S"))
    return task_uuid, priority

def clear_crawler_task(task_uuid, domain_type):
    hash_query = get_crawler_task_hash(task_uuid)
    r_crawler.hdel('crawler:queue:hash', hash_query)
    r_crawler.srem(f'crawler:queue:type:{domain_type}', task_uuid)
    r_crawler.srem('crawler:queue:queued', task_uuid)

def get_crawlers_tasks_status():
    tasks_status = []
    tasks = r_crawler.smembers('crawler:queue:queued')
    for task_uuid in tasks:
        tasks_status.append(get_task_status(task_uuid))
    return tasks_status

##-- CRAWLER TASK --##

#### CRAWLER TASK API ####

# # TODO: ADD user agent
# # TODO: sanitize URL
def api_add_crawler_task(data, user_id=None):
    url = data.get('url', None)
    if not url or url=='\n':
        return ({'status': 'error', 'reason': 'No url supplied'}, 400)

    screenshot = data.get('screenshot', False)
    if screenshot:
        screenshot = True
    else:
        screenshot = False
    har = data.get('har', False)
    if har:
        har = True
    else:
        har = False
    depth_limit = data.get('depth_limit', 1)
    if depth_limit:
        try:
            depth_limit = int(depth_limit)
            if depth_limit < 0:
                depth_limit = 0
        except ValueError:
            return ({'error':'invalid depth limit'}, 400)
    else:
        depth_limit = 0

    # cookiejar_uuid = data.get('cookiejar_uuid', None)
    # if cookiejar_uuid:
    #     if not exist_cookiejar(cookiejar_uuid):
    #         return ({'error': 'unknow cookiejar uuid', 'cookiejar_uuid': cookiejar_uuid}, 404)
    #     level = get_cookiejar_level(cookiejar_uuid)
    #     if level == 0:  # # TODO: check if user is admin ######################################################
    #         cookie_owner = get_cookiejar_owner(cookiejar_uuid)
    #         if cookie_owner != user_id:
    #             return ({'error': 'The access to this cookiejar is restricted'}, 403)

    # if auto_crawler:
    #     try:
    #         crawler_delta = int(crawler_delta)
    #         if crawler_delta < 0:
    #             return ({'error':'invalid delta between two pass of the crawler'}, 400)
    #     except ValueError:
    #         return ({'error':'invalid delta between two pass of the crawler'}, 400)

    proxy = data.get('proxy', None)
    if proxy == 'onion' or proxy == 'tor':
        proxy = 'force_tor'
    else:
        # TODO sanitize PROXY
        proxy = None

    # TODO #############################################################################################################
    auto_crawler = auto_crawler
    crawler_delta = crawler_delta
    parent = 'manual'

    return add_crawler_task(url, depth=depth_limit, har=har, screenshot=screenshot, cookiejar=cookiejar_uuid,
                            proxy=proxy, user_agent=user_agent, parent='manual', priority=90), 200





#### ####


###################################################################################
###################################################################################
###################################################################################
###################################################################################









#### CRAWLER GLOBAL ####

# TODO: # FIXME: config db, dynamic load
def is_crawler_activated():
    return activate_crawler == 'True'

def get_crawler_all_types():
    return ['onion', 'web']

def sanitize_crawler_types(l_crawler_types):
    all_crawler_types = get_crawler_all_types()
    if not l_crawler_types:
        return all_crawler_types
    for crawler_type in l_crawler_types:
        if crawler_type not in all_crawler_types:
            return all_crawler_types
    return l_crawler_types

def get_all_spash_crawler_status():
    crawler_metadata = []
    all_crawlers = r_cache.smembers('all_splash_crawlers')
    for crawler in all_crawlers:
        crawler_metadata.append(get_splash_crawler_status(crawler))
    return crawler_metadata

def reset_all_spash_crawler_status():
    r_cache.delete('all_splash_crawlers')

def get_splash_crawler_status(spash_url):
    crawler_type = r_cache.hget(f'metadata_crawler:{spash_url}', 'type')
    crawling_domain = r_cache.hget(f'metadata_crawler:{spash_url}', 'crawling_domain')
    started_time = r_cache.hget(f'metadata_crawler:{spash_url}', 'started_time')
    status_info = r_cache.hget(f'metadata_crawler:{spash_url}', 'status')
    crawler_info = f'{spash_url}  - {started_time}'
    if status_info=='Waiting' or status_info=='Crawling':
        status=True
    else:
        status=False
    return {'crawler_info': crawler_info, 'crawling_domain': crawling_domain, 'status_info': status_info, 'status': status, 'type': crawler_type}

def set_current_crawler_status(splash_url, status, started_time=False, crawled_domain=None, crawler_type=None):
    # TODO: get crawler type if None
    # Status: ['Waiting', 'Error', ...]
    r_cache.hset(f'metadata_crawler:{splash_url}', 'status', status)
    if started_time:
        r_cache.hset(f'metadata_crawler:{splash_url}', 'started_time', datetime.now().strftime("%Y/%m/%d  -  %H:%M.%S"))
    if crawler_type:
        r_cache.hset(f'metadata_crawler:{splash_url}', 'type', crawler_type)
    if crawled_domain:
        r_cache.hset(f'metadata_crawler:{splash_url}', 'crawling_domain', crawled_domain)

    #r_cache.sadd('all_splash_crawlers', splash_url) # # TODO: add me in fct: create_ail_crawler

def get_stats_last_crawled_domains(crawler_types, date):
    statDomains = {}
    for crawler_type in crawler_types:
        stat_type = {}
        stat_type['domains_up'] = r_crawler.scard('{}_up:{}'.format(crawler_type, date))
        stat_type['domains_down'] = r_crawler.scard('{}_down:{}'.format(crawler_type, date))
        stat_type['total'] = stat_type['domains_up'] + stat_type['domains_down']
        stat_type['domains_queue'] = get_nb_elem_to_crawl_by_type(crawler_type)
        statDomains[crawler_type] = stat_type
    return statDomains

# # TODO: handle custom proxy
def get_splash_crawler_latest_stats():
    now = datetime.now()
    date = now.strftime("%Y%m%d")
    return get_stats_last_crawled_domains(['onion', 'web'], date)

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
    crawlers_to_launch = list(set(all_splash) & set(dict_splash_name.keys()))
    for splash_name in crawlers_to_launch:
        try:
            nb_to_launch = int(dict_splash_name.get(splash_name, 0))
            if nb_to_launch < 0:
                return {'error':'The number of crawlers to launch is negative'}, 400
        except:
            return {'error':'invalid number of crawlers to launch'}, 400
        if nb_to_launch > 0:
            dict_crawlers_to_launch[splash_name] = nb_to_launch

    if dict_crawlers_to_launch:
        set_nb_crawlers_to_launch(dict_crawlers_to_launch)
        return (dict_crawlers_to_launch, 200)
    else:
        return {'error':'invalid input'}, 400

def add_domain_blacklist(domain_type, domain):
    r_serv_onion.sadd(f'blacklist_{domain_type}', domain)

##-- CRAWLER GLOBAL --##

#### AUTOMATIC CRAWLER ####

def get_auto_crawler_all_domain(l_crawler_types=[]):
    l_crawler_types = sanitize_crawler_types(l_crawler_types)
    if len(l_crawler_types) == 1:
        return r_serv_onion.smembers(f'auto_crawler_url:{l_crawler_types[0]}')
    else:
        l_keys_name = []
        for crawler_type in l_crawler_types:
            l_keys_name.append(f'auto_crawler_url:{crawler_type}')
        return r_serv_onion.sunion(l_keys_name[0], *l_keys_name[1:])

def add_auto_crawler_in_queue(domain, domain_type, port, epoch, delta, message):
    r_serv_onion.zadd('crawler_auto_queue', {f'{message};{domain_type}': int(time.time() + delta)})
    # update list, last auto crawled domains
    r_serv_onion.lpush('last_auto_crawled', f'{domain}:{port};{epoch}')
    r_serv_onion.ltrim('last_auto_crawled', 0, 9)

def update_auto_crawler_queue():
    current_epoch = int(time.time())
    # check if current_epoch > domain_next_epoch
    l_queue = r_serv_onion.zrangebyscore('crawler_auto_queue', 0, current_epoch)
    for elem in l_queue:
        mess, domain_type = elem.rsplit(';', 1)
        print(domain_type)
        print(mess)
        r_serv_onion.sadd(f'{domain_type}_crawler_priority_queue', mess)


##-- AUTOMATIC CRAWLER --##

#### CRAWLER TASK ####



##-- CRAWLER TASK --##



#### ####


def is_redirection(domain, last_url):
    url = urlparse(last_url)
    last_domain = url.netloc
    last_domain = last_domain.split('.')
    last_domain = '{}.{}'.format(last_domain[-2], last_domain[-1])
    return domain != last_domain

def create_item_id(item_dir, domain):
    # remove /
    domain = domain.replace('/', '_')
    if len(domain) > 215:
        UUID = domain[-215:]+str(uuid.uuid4())
    else:
        UUID = domain+str(uuid.uuid4())
    return os.path.join(item_dir, UUID)

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
    create_item_metadata(item_id, domain, 'last_url', 'father')

#### CRAWLER QUEUES ####

## queues priority:
# 1 - priority queue
# 2 - discovery queue
# 3 - default queue
##
def get_all_queues_names():
    return ['priority', 'discovery', 'default']

def get_all_queues_keys():
    return ['{}_crawler_priority_queue', '{}_crawler_discovery_queue', '{}_crawler_queue']

def get_queue_key_by_name(queue_name):
    if queue_name == 'priority':
        return '{}_crawler_priority_queue'
    elif queue_name == 'discovery':
        return '{}_crawler_discovery_queue'
    else: # default
        return '{}_crawler_queue'

def get_stats_elem_to_crawl_by_queue_type(queue_type):
    dict_stats = {}
    for queue_name in get_all_queues_names():
        dict_stats[queue_name] = r_serv_onion.scard(get_queue_key_by_name(queue_name).format(queue_type))
    return dict_stats

def get_all_queues_stats():
    dict_stats = {}
    for queue_type in get_crawler_all_types():
        dict_stats[queue_type] = get_stats_elem_to_crawl_by_queue_type(queue_type)
    for queue_type in get_all_splash():
        dict_stats[queue_type] = get_stats_elem_to_crawl_by_queue_type(queue_type)
    return dict_stats

def is_domain_in_queue(queue_type, domain):
    return r_serv_onion.sismember(f'{queue_type}_domain_crawler_queue', domain)

def is_item_in_queue(queue_type, url, item_id, queue_name=None):
    if queue_name is None:
        queues = get_all_queues_keys()
    else:
        queues = get_queue_key_by_name(queue_name)

    key = f'{url};{item_id}'
    for queue in queues:
        if r_serv_onion.sismember(queue.format(queue_type), key):
            return True
    return False

def queue_test_clean_up(queue_type, domain, item_id):
    date_month = datetime.now().strftime("%Y%m")
    r_serv_onion.srem(f'month_{queue_type}_up:{date_month}', domain)

    # Clean up
    r_serv_onion.srem(f'{queue_type}_domain_crawler_queue', domain)
    msg = f'{domain};{item_id}'
    r_serv_onion.srem(f'{queue_type}_crawler_discovery_queue', msg)
    r_serv_onion.srem(f'{queue_type}_crawler_queue', msg)


def remove_task_from_crawler_queue(queue_name, queue_type, key_to_remove):
    r_serv_onion.srem(queue_name.format(queue_type), key_to_remove)

# # TODO: keep auto crawler ?
def clear_crawler_queues():
    for queue_key in get_all_queues_keys():
        for queue_type in get_crawler_all_types():
            r_serv_onion.delete(queue_key.format(queue_type))

###################################################################################
def get_nb_elem_to_crawl_by_type(queue_type): # # TODO: rename me
    nb = r_serv_onion.scard('{}_crawler_priority_queue'.format(queue_type))
    nb += r_serv_onion.scard('{}_crawler_discovery_queue'.format(queue_type))
    nb += r_serv_onion.scard('{}_crawler_queue'.format(queue_type))
    return nb
###################################################################################

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
        all_domain_type.append('web')
    else:
        all_domain_type.append('web')
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
        crawler_type = 'web'
    return crawler_type


def get_elem_to_crawl_by_queue_type(l_queue_type):
    ## queues priority:
    # 1 - priority queue
    # 2 - discovery queue
    # 3 - normal queue
    ##

    for queue_key in get_all_queues_keys():
        for queue_type in l_queue_type:
            message = r_serv_onion.spop(queue_key.format(queue_type))
            if message:
                dict_to_crawl = {}
                splitted = message.rsplit(';', 1)
                if len(splitted) == 2:
                    url, item_id = splitted
                    item_id = item_id.replace(ITEMS_FOLDER+'/', '')
                else:
                # # TODO: to check/refractor
                    item_id = None
                    url = message
                crawler_type = get_crawler_type_by_url(url)
                return {'url': url, 'paste': item_id, 'type_service': crawler_type, 'queue_type': queue_type, 'original_message': message}
    return None

#### ---- ####

# # # # # # # # # # # #
#                     #
#   SPLASH MANAGER    #
#                     #
# # # # # # # # # # # #

    ## PROXY ##
def get_all_proxies(r_list=False):
    res = r_serv_onion.smembers('all_proxies')
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
    r_serv_onion.srem('all_proxies', proxy_name)
    ## -- ##

#### ---- ####


# # # # CRAWLER LACUS # # # #

def get_lacus_url():
    return r_db.hget('crawler:lacus', 'url')

def get_lacus_api_key(reload=False): # TODO: add in db config
    return r_db.hget('crawler:lacus', 'key')

# TODO Rewrite with new API key
def get_hidden_lacus_api_key(): # TODO: add in db config
    key = get_lacus_api_key()
    if key:
        if len(key)==41:
            return f'{key[:4]}*********************************{key[-4:]}'

# TODO Rewrite with new API key
def is_valid_api_key(api_key, search=re.compile(r'[^a-zA-Z0-9_-]').search):
    if len(api_key) != 41:
        return False
    return not bool(search(api_key))

def save_lacus_url_api(url, api_key):
    r_db.hset('crawler:lacus', 'url', url)
    r_db.hset('crawler:lacus', 'key', api_key)

def is_lacus_connected(delta_check=30):
    last_check = r_cache.hget('crawler:lacus', 'last_check')
    if last_check:
        if int(time.time()) - int(last_check) > delta_check:
            ping_lacus()
    else:
        ping_lacus()
    is_connected = r_cache.hget('crawler:lacus', 'connected')
    return is_connected == 'True'

def get_lacus_connection_metadata(force_ping=False):
    dict_manager={}
    if force_ping:
        dict_manager['status'] = ping_lacus()
    else:
        dict_manager['status'] = is_lacus_connected()
    if not dict_manager['status']:
        dict_manager['status_code'] = r_cache.hget('crawler:lacus', 'status_code')
        dict_manager['error'] = r_cache.hget('crawler:lacus', 'error')
    return dict_manager

def get_lacus():
    url = get_lacus_url()
    if url:
        return PyLacus(get_lacus_url())

# TODO CATCH EXCEPTIONS
def ping_lacus():
    # TODO CATCH EXCEPTION
    lacus = get_lacus()
    if not lacus:
        ping = False
    else:
        ping = lacus.is_up
    update_lacus_connection_status(ping)
    return ping

def update_lacus_connection_status(is_connected, req_error=None):
    r_cache.hset('crawler:lacus', 'connected', str(is_connected))
    r_cache.hset('crawler:lacus', 'last_check', int(time.time()))
    if not req_error:
        r_cache.hdel('crawler:lacus', 'error')
    else:
        r_cache.hset('crawler:lacus', 'status_code', req_error['status_code'])
        r_cache.hset('crawler:lacus', 'error', req_error['error'])

def api_save_lacus_url_key(data):
    # unpack json
    manager_url = data.get('url', None)
    api_key = data.get('api_key', None)
    if not manager_url: # or not api_key:
        return {'status': 'error', 'reason': 'No url or API key supplied'}, 400
    # check if is valid url
    try:
        result = urlparse(manager_url)
        if not all([result.scheme, result.netloc]):
            return {'status': 'error', 'reason': 'Invalid url'}, 400
    except:
        return {'status': 'error', 'reason': 'Invalid url'}, 400

    # # check if is valid key CURRENTLY DISABLE
    # if not is_valid_api_key(api_key):
    #     return ({'status': 'error', 'reason': 'Invalid API key'}, 400)

    save_lacus_url_api(manager_url, api_key)
    return {'url': manager_url, 'api_key': get_hidden_lacus_api_key()}, 200




 ## PROXY ##

    # TODO SAVE PROXY URL + ADD PROXY TESTS
    #          -> name + url

 ## PROXY ##

def is_test_ail_crawlers_successful():
    return r_db.hget('crawler:tor:test', 'success') == 'True'


def get_test_ail_crawlers_message():
    return r_db.hget('crawler:tor:test', 'message')


def save_test_ail_crawlers_result(test_success, message):
    r_db.hset('crawler:tor:test', 'success', str(test_success))
    r_db.hset('crawler:tor:test', 'message', message)

def test_ail_crawlers():
    # # TODO: test web domain
    if not ping_lacus():
        lacus_url = get_lacus_url()
        error_message = f'Error: Can\'t connect to AIL Lacus, {lacus_url}'
        print(error_message)
        save_test_ail_crawlers_result(False, error_message)
        return False

    lacus = get_lacus()
    commit_id = git_status.get_last_commit_id_from_local()
    user_agent = f'commit_id-AIL LACUS CRAWLER'
    domain = 'eswpccgr5xyovsahffkehgleqthrasfpfdblwbs4lstd345dwq5qumqd.onion'
    url = 'http://eswpccgr5xyovsahffkehgleqthrasfpfdblwbs4lstd345dwq5qumqd.onion'

    ## LAUNCH CRAWLER, TEST MODE ##
    # set_current_crawler_status(splash_url, 'CRAWLER TEST', started_time=True,
    # crawled_domain='TEST DOMAIN', crawler_type='onion')
    capture_uuid = lacus.enqueue(url=url, depth=0, user_agent=user_agent, proxy='force_tor',
                                 force=True, general_timeout_in_sec=90)
    status = lacus.get_capture_status(capture_uuid)
    launch_time = int(time.time()) # capture timeout
    while int(time.time()) - launch_time < 60 and status != CaptureStatus.DONE:
        # DEBUG
        print(int(time.time()) - launch_time)
        print(status)
        time.sleep(1)
        status = lacus.get_capture_status(capture_uuid)

    # TODO CRAWLER STATUS OR QUEUED CAPTURE LIST
    entries = lacus.get_capture(capture_uuid)
    if 'error' in entries:
        save_test_ail_crawlers_result(False, entries['error'])
        return False
    elif 'html' in entries and entries['html']:
        mess = 'It works!'
        if mess in entries['html']:
            save_test_ail_crawlers_result(True, mess)
            return True
        else:
            return False
    return False

#### ---- ####

#### CRAWLER PROXY ####

#### ---- ####


# TODO MOVE ME
load_blacklist()

if __name__ == '__main__':
    # res = get_splash_manager_version()
    # res = test_ail_crawlers()
    # res = is_test_ail_crawlers_successful()
    # print(res)
    # print(get_test_ail_crawlers_message())
    # print(get_all_queues_stats())

    # res = get_auto_crawler_all_domain()
    # res = get_all_cookiejar()
    res = unpack_url('http://test.com/')
    print(res)
