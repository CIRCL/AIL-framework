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
from lib.objects.Items import Item

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
r_crawler = config_loader.get_db_conn("Kvrocks_Crawler")
r_cache = config_loader.get_redis_conn("Redis_Cache")

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
# # # # # # # # TODO CREATE NEW OBJECT

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
################################################################################
################################################################################

def get_cookiejars():
    return r_crawler.smembers('cookiejars:all')

def get_cookiejars_global():
    cookiejars = r_crawler.smembers('cookiejars:global')
    if not cookiejars:
        cookiejars = []
    return cookiejars

def get_cookiejars_user(user_id):
    cookiejars = r_crawler.smembers(f'cookiejars:user:{user_id}')
    if not cookiejars:
        cookiejars = []
    return cookiejars

class Cookiejar:

    def __init__(self, cookiejar_uuid):
        self.uuid = cookiejar_uuid

    def exists(self):
        return r_crawler.exists(f'cookiejar:meta:{self.uuid}')  # or cookiejar:uuid

    def get_date(self):
        return r_crawler.hget(f'cookiejar:meta:{self.uuid}', 'date')

    def _set_date(self, date):
        r_crawler.hset(f'cookiejar:meta:{self.uuid}', 'date', date)

    def get_description(self):
        return r_crawler.hget(f'cookiejar:meta:{self.uuid}', 'description')

    def set_description(self, description):
        r_crawler.hset(f'cookiejar:meta:{self.uuid}', 'description', description)

    def get_user(self):
        return r_crawler.hget(f'cookiejar:meta:{self.uuid}', 'user')

    def _set_user(self, user_id):
        return r_crawler.hset(f'cookiejar:meta:{self.uuid}', 'user', user_id)

    def get_level(self):
        level = r_crawler.hget(f'cookiejar:meta:{self.uuid}', 'level')
        if level:
            level = 1
        else:
            level = 0
        return level

    def _set_level(self, level):
        if level:
            level = 1
        else:
            level = 0
        r_crawler.hset(f'cookiejar:meta:{self.uuid}', 'level', level)

    def is_cookie_in_jar(self, cookie_uuid):
        return r_crawler.sismember(f'cookiejar:cookies:{self.uuid}', cookie_uuid)

    def get_cookies_uuid(self):
        return r_crawler.smembers(f'cookiejar:cookies:{self.uuid}')

    def get_cookies(self, r_json=False):
        l_cookies = []
        for cookie_uuid in self.get_cookies_uuid():
            cookies = Cookie(cookie_uuid)
            l_cookies.append(cookies.get_meta(r_json=r_json))
        return l_cookies

    def get_nb_cookies(self):
        return r_crawler.scard(f'cookiejar:cookies:{self.uuid}')

    def get_meta(self, level=False, nb_cookies=False, cookies=False, r_json=False):
        meta = {'uuid': self.uuid,
                'date': self.get_date(),
                'description': self.get_description(),
                'user': self.get_user()}
        if level:
            meta['level'] = self.get_level()
        if nb_cookies:
            meta['nb_cookies'] = self.get_nb_cookies()
        if cookies:
            meta['cookies'] = self.get_cookies(r_json=r_json)
        return meta

    def add_cookie(self, name, value, cookie_uuid=None, domain=None, httponly=None, path=None, secure=None, text=None):
        if cookie_uuid:
            cookie = Cookie(cookie_uuid)
            if cookie.exists():
                cookie_uuid = generate_uuid()
        else:
            cookie_uuid = generate_uuid()
        r_crawler.sadd(f'cookiejar:cookies:{self.uuid}', cookie_uuid)

        cookie = Cookie(cookie_uuid)
        cookie.set_cookiejar(self.uuid)

        cookie.set_field('name', name)
        cookie.set_field('value', value)
        if domain:
            cookie.set_field('domain', domain)
        if httponly:
            cookie.set_field('httpOnly', str(httponly))
        if path:
            cookie.set_field('path', path)
        if secure:
            cookie.set_field('secure', str(secure))
        if text:
            cookie.set_field('path', text)
        return cookie_uuid

    def delete_cookie(self, cookie_uuid):
        if self.is_cookie_in_jar(cookie_uuid):
            cookie = Cookie(cookie_uuid)
            cookie.delete()

    def create(self, user_id, description=None, level=1):
        if self.exists():
            raise Exception('Cookiejar already exists')

        r_crawler.sadd('cookiejars:all', self.uuid)
        if level == 0:
            r_crawler.sadd(f'cookiejars:user:{user_id}', self.uuid)
        else:
            r_crawler.sadd('cookiejars:global', self.uuid)

        self._set_user(user_id)
        self._set_date(datetime.now().strftime("%Y%m%d"))
        self._set_level(level)
        if description:
            self.set_description(description)

    def delete(self):
        for cookie_uuid in self.get_cookies_uuid():
            self.delete_cookie(cookie_uuid)
        r_crawler.srem(f'cookiejars:user:{self.get_user()}', self.uuid)
        r_crawler.srem('cookiejars:global', self.uuid)
        r_crawler.srem('cookiejars:all', self.uuid)
        r_crawler.delete(f'cookiejar:meta:{self.uuid}')


def create_cookiejar(user_id, description=None, level=1, cookiejar_uuid=None):
    if cookiejar_uuid:
        cookiejar = Cookiejar(cookiejar_uuid)
        if cookiejar.exists():
            cookiejar_uuid = generate_uuid()
    else:
        cookiejar_uuid = generate_uuid()
    cookiejar = Cookiejar(cookiejar_uuid)
    cookiejar.create(user_id, description=description, level=level)
    return cookiejar_uuid

def get_cookiejars_meta_by_iterator(iter_cookiejar_uuid):
    cookiejars_meta = []
    for cookiejar_uuid in iter_cookiejar_uuid:
        cookiejar = Cookiejar(cookiejar_uuid)
        cookiejars_meta.append(cookiejar.get_meta(nb_cookies=True))
    return cookiejars_meta

def get_cookiejars_by_user(user_id):
    cookiejars_global = get_cookiejars_global()
    cookiejars_user = get_cookiejars_user(user_id)
    return [*cookiejars_user, *cookiejars_global]

## API ##

def api_get_cookiejars_selector(user_id):
    cookiejars = []
    for cookiejar_uuid in get_cookiejars_by_user(user_id):
        cookiejar = Cookiejar(cookiejar_uuid)
        description = cookiejar.get_description()
        if not description:
            description = ''
        cookiejars.append(f'{description} : {cookiejar.uuid}')
    return sorted(cookiejars)

def api_verify_cookiejar_acl(cookiejar_uuid, user_id):
    cookiejar = Cookiejar(cookiejar_uuid)
    if not cookiejar.exists():
        return {'error': 'unknown cookiejar uuid', 'cookiejar_uuid': cookiejar_uuid}, 404
    if cookiejar.get_level() == 0:  # TODO: check if user is admin
        if cookiejar.get_user() != user_id:
            return {'error': 'The access to this cookiejar is restricted'}, 403

def api_edit_cookiejar_description(user_id, cookiejar_uuid, description):
    resp = api_verify_cookiejar_acl(cookiejar_uuid, user_id)
    if resp:
        return resp
    cookiejar = Cookiejar(cookiejar_uuid)
    cookiejar.set_description(description)
    return {'cookiejar_uuid': cookiejar_uuid}, 200

def api_delete_cookiejar(user_id, cookiejar_uuid):
    resp = api_verify_cookiejar_acl(cookiejar_uuid, user_id)
    if resp:
        return resp
    cookiejar = Cookiejar(cookiejar_uuid)
    cookiejar.delete()
    return {'cookiejar_uuid': cookiejar_uuid}, 200

def api_get_cookiejar(cookiejar_uuid, user_id):
    resp = api_verify_cookiejar_acl(cookiejar_uuid, user_id)
    if resp:
        return resp
    cookiejar = Cookiejar(cookiejar_uuid)
    meta = cookiejar.get_meta(level=True, cookies=True, r_json=True)
    return meta, 200

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

# TODO   MISP Import

class Cookie:

    def __init__(self, cookie_uuid):
        self.uuid = cookie_uuid

    def exists(self):
        return r_crawler.exists(f'cookie:meta:{self.uuid}')

    def get_cookiejar(self):
        return r_crawler.hget(f'cookie:meta:{self.uuid}', 'cookiejar')

    def set_cookiejar(self, cookiejar_uuid):
        r_crawler.hset(f'cookie:meta:{self.uuid}', 'cookiejar', cookiejar_uuid)

    def get_name(self):
        return r_crawler.hget(f'cookie:meta:{self.uuid}', 'name')

    def get_value(self):
        return r_crawler.hget(f'cookie:meta:{self.uuid}', 'value')

    def _get_field(self, field):
        return r_crawler.hget(f'cookie:meta:{self.uuid}', field)

    def set_field(self, field, value):
        return r_crawler.hset(f'cookie:meta:{self.uuid}', field, value)

    def remove_field(self, field):
        return r_crawler.hdel(f'cookie:meta:{self.uuid}', field)

    def get_fields(self):
        fields = set(r_crawler.hkeys(f'cookie:meta:{self.uuid}'))
        if 'cookiejar' in fields:
            fields.remove('cookiejar')
        return fields

    # def get_domain(self):
    #     return r_crawler.hget(f'cookie:meta:{self.uuid}', 'domain')
    #
    # def get_path(self):
    #     return r_crawler.hget(f'cookie:meta:{self.uuid}', 'path')
    #
    # def get_httpOnly(self):
    #     return r_crawler.hget(f'cookie:meta:{self.uuid}', 'httpOnly')
    #
    # def get_secure(self):
    #     return r_crawler.hget(f'cookie:meta:{self.uuid}', 'secure')

    # TODO expire ????
    def get_meta(self, r_json=False):
        meta = {}
        # ['domain', 'path', 'httpOnly', 'secure'] + name + value
        for field in self.get_fields():
            value = self._get_field(field)
            if value:
                meta[field] = value
        if r_json:
            data = json.dumps(meta, indent=4, sort_keys=True)
            meta = {'data': data}
            meta['uuid'] = self.uuid
        return meta

    def edit(self, cookie_dict):
        # remove old keys
        for field in self.get_fields():
            if field not in cookie_dict:
                self.remove_field(field)
        # add new keys
        for field in cookie_dict:
            value = cookie_dict[field]
            if value:
                if field == 'secure' or field == 'httpOnly':
                    value = str(value)
                self.set_field(field, value)

    def delete(self):
        cookiejar_uuid = self.get_cookiejar()
        r_crawler.delete(f'cookie:meta:{self.uuid}')
        r_crawler.srem(f'cookiejar:cookies:{cookiejar_uuid}', self.uuid)

## API ##

def api_get_cookie(user_id, cookie_uuid):
    cookie = Cookie(cookie_uuid)
    if not cookie.exists():
        return {'error': 'unknown cookie uuid', 'cookie_uuid': cookie_uuid}, 404
    resp = api_verify_cookiejar_acl(cookie.get_cookiejar(), user_id)
    if resp:
        return resp
    return cookie.get_meta()

def api_edit_cookie(user_id, cookie_uuid, cookie_dict):
    cookie = Cookie(cookie_uuid)
    if not cookie.exists():
        return {'error': 'unknown cookie uuid', 'cookie_uuid': cookie_uuid}, 404
    resp = api_verify_cookiejar_acl(cookie.get_cookiejar(), user_id)
    if resp:
        return resp
    if 'name' not in cookie_dict or 'value' not in cookie_dict or not cookie_dict['name'] or not cookie_dict['value']:
        return {'error': 'cookie name or value not provided'}, 400
    cookie.edit(cookie_dict)
    return cookie.get_meta(), 200

def api_create_cookie(user_id, cookiejar_uuid, cookie_dict):
    resp = api_verify_cookiejar_acl(cookiejar_uuid, user_id)
    if resp:
        return resp
    if 'name' not in cookie_dict or 'value' not in cookie_dict or not cookie_dict['name'] or not cookie_dict['value']:
        return {'error': 'cookie name or value not provided'}, 400
    cookiejar = Cookiejar(cookiejar_uuid)
    name = cookie_dict.get('name')
    value = cookie_dict.get('value')
    domain = cookie_dict.get('domain')
    path = cookie_dict.get('path')
    text = cookie_dict.get('text')
    httponly = bool(cookie_dict.get('httponly'))
    secure = bool(cookie_dict.get('secure'))
    cookiejar.add_cookie(name, value, domain=domain, httponly=httponly, path=path, secure=secure, text=text)
    return resp, 200

def api_delete_cookie(user_id, cookie_uuid):
    cookie = Cookie(cookie_uuid)
    if not cookie.exists():
        return {'error': 'unknown cookie uuid', 'cookie_uuid': cookie_uuid}, 404
    cookiejar_uuid = cookie.get_cookiejar()
    resp = api_verify_cookiejar_acl(cookiejar_uuid, user_id)
    if resp:
        return resp
    cookiejar = Cookiejar(cookiejar_uuid)
    if not cookiejar.is_cookie_in_jar(cookie_uuid):
        return {'error': 'Cookie isn\'t in the jar', 'cookiejar_uuid': cookiejar_uuid}, 404
    cookiejar.delete_cookie(cookie_uuid)
    return {'cookiejar_uuid': cookiejar_uuid, 'cookie_uuid': cookie_uuid}, 200

# def get_cookie_all_keys_name():
#     return ['name', 'value', 'domain', 'path', 'httpOnly', 'secure']

##  - -  ##
## Cookies import ##       # TODO: add browser type ?
def import_cookies_from_json(json_cookies, cookiejar_uuid):
    cookiejar = Cookiejar(cookiejar_uuid)
    for cookie in json_cookies:
        try:
            cookie_dict = unpack_imported_json_cookie(cookie)
            name = cookie_dict.get('name')
            value = cookie_dict.get('value')
            domain = cookie_dict.get('domain')
            httponly = cookie_dict.get('httponly')
            path = cookie_dict.get('path')
            secure = cookie_dict.get('secure')
            text = cookie_dict.get('text')
            cookiejar.add_cookie(name, value, domain=domain, httponly=httponly, path=path, secure=secure, text=text)
        except KeyError:
            return {'error': 'Invalid cookie key, please submit a valid JSON', 'cookiejar_uuid': cookiejar_uuid}, 400

# # TODO: add text field
def unpack_imported_json_cookie(json_cookie):
    cookie_dict = {'name': json_cookie['Name raw'], 'value': json_cookie['Content raw']}
    if 'Path raw' in json_cookie:
        cookie_dict['path'] = json_cookie['Path raw']
    if 'HTTP only raw' in json_cookie:
        cookie_dict['httponly'] = json_cookie['HTTP only raw'] == 'true'
    if 'Send for' in json_cookie:
        cookie_dict['secure'] = json_cookie['Send for'] == 'Encrypted connections only'
    if 'Host raw' in json_cookie:
        url = urlparse(json_cookie['Host raw'])
        cookie_dict['domain'] = url.netloc.split(':', 1)[0]
    return cookie_dict

##  - -  ##
#### COOKIEJAR API ####
def api_import_cookies_from_json(user_id, cookiejar_uuid, json_cookies_str): # # TODO: add catch
    resp = api_verify_cookiejar_acl(cookiejar_uuid, user_id)
    if resp:
        return resp
    json_cookies = json.loads(json_cookies_str)
    resp = import_cookies_from_json(json_cookies, cookiejar_uuid)
    if resp:
        return resp, 400
#### ####


# # # # # # # #
#             #
#   CRAWLER   # ###################################################################################
#             #
# # # # # # # #

def get_default_user_agent():
    return 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'

def get_last_crawled_domains(domain_type):
    return r_crawler.lrange(f'last_{domain_type}', 0, -1)

def update_last_crawled_domain(domain_type, domain, epoch):
    # update list, last crawled domains
    r_crawler.lpush(f'last_{domain_type}', f'{domain}:{epoch}')
    r_crawler.ltrim(f'last_{domain_type}', 0, 15)

def create_item_metadata(item_id, url, item_father):
    item = Item(item_id)
    item.set_crawled(url, item_father)

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

#### Blocklist ####

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

#### CRAWLER STATE ####

#### CRAWLER CAPTURE ####

def get_nb_crawler_captures():
    return r_cache.zcard('crawler:captures')

def get_crawler_captures():
    return r_crawler.zrange('crawler:captures', 0, -1)

def reload_crawler_captures():
    r_cache.delete('crawler:captures')
    for capture_uuid in get_crawler_captures():
        capture = CrawlerCapture(capture_uuid)
        r_cache.zadd('crawler:captures', {capture.uuid: 0})

@unique
class CaptureStatus(IntEnum):
    """The status of the capture"""
    UNKNOWN = -1
    QUEUED = 0
    DONE = 1
    ONGOING = 2

class CrawlerCapture:

    def __init__(self, task_uuid):
        self.uuid = task_uuid

    def exists(self):
        return r_crawler.hexists('crawler:captures:tasks', self.uuid)

    def get_task_uuid(self):
        return r_crawler.hget('crawler:captures:tasks', self.uuid)

    def get_task(self):
        task_uuid = self.get_task_uuid()
        if task_uuid:
            return CrawlerTask(task_uuid)

    def get_start_time(self):
        return self.get_task().get_start_time()

    def get_status(self):
        return r_cache.hget(f'crawler:capture:{self.uuid}', 'status')

    def create(self, task_uuid):
        if self.exists():
            raise Exception(f'Error: Capture {self.uuid} already exists')
        launch_time = int(time.time())
        r_crawler.hset(f'crawler:task:{task_uuid}', 'capture', self.uuid)
        r_crawler.hset('crawler:captures:tasks', self.uuid, task_uuid)
        r_crawler.zadd('crawler:captures', {self.uuid: launch_time})
        r_cache.hset(f'crawler:capture:{self.uuid}', 'launch_time', launch_time)
        r_cache.zadd('crawler:captures', {self.uuid: launch_time})

    def update(self, status):
        last_check = int(time.time())
        r_cache.hset(f'crawler:capture:{self.uuid}', 'status', status)
        r_cache.zadd('crawler:captures', {self.uuid: last_check})

    def remove(self): # TODO INCOMPLETE
        r_crawler.zrem('crawler:captures', self.uuid)
        r_crawler.hdel('crawler:captures:tasks', self.uuid)

    # TODO
    # TODO DELETE TASK ???
    def delete(self):
        # task = self.get_task()
        # task.delete()
        r_cache.delete(f'crawler:capture:{self.uuid}')


def create_capture(capture_uuid, task_uuid):
    capture = CrawlerCapture(capture_uuid)
    capture.create(task_uuid)

def get_crawler_capture():
    capture = r_cache.zpopmin('crawler:captures')
    if capture:
        capture = CrawlerCapture(capture[0][0])
    else:
        capture = None
    return capture

# TODO add capture times
def get_captures_status():
    status = []
    for capture_uuid in get_crawler_captures():
        capture = CrawlerCapture(capture_uuid)
        task = capture.get_task()
        domain = task.get_domain()
        dom = Domain(domain)
        meta = {
            'uuid': task.uuid,
            'domain': dom.get_id(),
            'type': dom.get_domain_type(),
            'start_time': capture.get_start_time(), ############### TODO
            'status': capture.get_status(),
        }
        status.append(meta)
    return status

##-- CRAWLER STATE --##

#### CRAWLER TASKS ####

#### CRAWLER TASK ####

class CrawlerTask:

    def __init__(self, task_uuid):
        self.uuid = task_uuid

    def exists(self):
        return r_crawler.exists(f'crawler:task:{self.uuid}')

    def get_url(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'url')

    def get_domain(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'domain')

    def get_depth(self):
        depth = r_crawler.hget(f'crawler:task:{self.uuid}', 'depth')
        if not depth:
            depth = 1
        return int(depth)

    def get_har(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'har') == '1'

    def get_screenshot(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'screenshot') == '1'

    def get_queue(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'queue')

    def get_user_agent(self):
        user_agent = r_crawler.hget(f'crawler:task:{self.uuid}', 'user_agent')
        if not user_agent:
            user_agent = get_default_user_agent()
        return user_agent

    def get_cookiejar(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'cookiejar')

    def get_cookies(self):
        cookiejar = self.get_cookiejar()
        if cookiejar:
            cookiejar = Cookiejar(cookiejar)
            return cookiejar.get_cookies()
        else:
            return []

    def get_header(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'header')

    def get_proxy(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'proxy')

    def get_parent(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'parent')

    def get_hash(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'hash')

    def get_start_time(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'start_time')

    # TODO
    def get_status(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'status') #######################################

    def get_capture(self):
        return r_crawler.hget(f'crawler:task:{self.uuid}', 'capture')

    def _set_field(self, field, value):
        return r_crawler.hset(f'crawler:task:{self.uuid}', field, value)

    def get_meta(self):
        meta = {
            'uuid': self.uuid,
            'url': self.get_url(),
            'domain': self.get_domain(),
            'depth': self.get_depth(),
            'har': self.get_har(),
            'screenshot': self.get_screenshot(),
            'type': self.get_queue(),
            'user_agent': self.get_user_agent(),
            'cookiejar': self.get_cookiejar(),
            'header': self.get_header(),
            'proxy': self.get_proxy(),
            'parent': self.get_parent(),
        }
        return meta

    # TODO STATUS UPDATE
    # TODO SANITIZE PRIORITY
    # PRIORITY:  discovery = 0/10, feeder = 10, manual = 50, auto = 40, test = 100
    def create(self, url, depth=1, har=True, screenshot=True, header=None, cookiejar=None, proxy=None,
               user_agent=None, parent='manual', priority=0):
        if self.exists():
            raise Exception('Error: Task already exists')

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

        if proxy == 'web':
            proxy = None
        elif proxy == 'force_tor' or proxy == 'tor' or proxy == 'onion':
            proxy = 'force_tor'
        if not user_agent:
            user_agent = get_default_user_agent()

        # TODO SANITIZE COOKIEJAR -> UUID

        # Check if already in queue
        hash_query = get_task_hash(url, domain, depth, har, screenshot, priority, proxy, cookiejar, user_agent, header)
        if r_crawler.hexists(f'crawler:queue:hash', hash_query):
            self.uuid = r_crawler.hget(f'crawler:queue:hash', hash_query)
            return self.uuid

        # TODO ADD TASK STATUS -----
        self._set_field('domain', domain)
        self._set_field('url', url)
        self._set_field('depth', int(depth))
        self._set_field('har', har)
        self._set_field('screenshot', screenshot)
        self._set_field('user_agent', user_agent)
        self._set_field('parent', parent)

        if cookiejar:
            self._set_field('cookiejar', cookiejar)
        if header:
            self._set_field('header', header)
        if proxy:
            self._set_field('proxy', proxy)

        r_crawler.hset('crawler:queue:hash', hash_query, self.uuid)
        self._set_field('hash', hash_query)
        r_crawler.zadd('crawler:queue', {self.uuid: priority})
        # UI
        domain_type = dom.get_domain_type()
        r_crawler.sadd(f'crawler:queue:type:{domain_type}', self.uuid)
        self._set_field('queue', domain_type)
        return self.uuid

    def lacus_queue(self):
        r_crawler.sadd('crawler:queue:queued', self.uuid)
        self._set_field('start_time', datetime.now().strftime("%Y/%m/%d  -  %H:%M.%S"))

    def clear(self):
        r_crawler.hdel('crawler:queue:hash', self.get_hash())
        r_crawler.srem(f'crawler:queue:type:{self.get_queue()}', self.uuid)
        r_crawler.srem('crawler:queue:queued', self.uuid)

    def delete(self):
        self.clear()
        r_crawler.delete(f'crawler:task:{self.uuid}')
        # r_crawler.zadd('crawler:queue', {self.uuid: priority})



# TODO move to class ???
def get_task_hash(url, domain, depth, har, screenshot, priority, proxy, cookiejar, user_agent, header):
    to_enqueue = {'domain': domain, 'depth': depth, 'har': har, 'screenshot': screenshot,
                  'priority': priority, 'proxy': proxy, 'cookiejar': cookiejar, 'user_agent': user_agent,
                  'header': header}
    if priority != 0:
        to_enqueue['url'] = url
    return hashlib.sha512(pickle.dumps(to_enqueue)).hexdigest()

def add_task_to_lacus_queue():
    task_uuid = r_crawler.zpopmax('crawler:queue')
    if not task_uuid or not task_uuid[0]:
        return None
    task_uuid, priority = task_uuid[0]
    task = CrawlerTask(task_uuid)
    task.lacus_queue()
    return task.uuid, priority

# PRIORITY:  discovery = 0/10, feeder = 10, manual = 50, auto = 40, test = 100
def create_task(url, depth=1, har=True, screenshot=True, header=None, cookiejar=None, proxy=None,
                user_agent=None, parent='manual', priority=0, task_uuid=None):
    if task_uuid:
        if CrawlerTask(task_uuid).exists():
            task_uuid = gen_uuid()
    else:
        task_uuid = gen_uuid()
    task = CrawlerTask(task_uuid)
    task_uuid = task.create(url, depth=depth, har=har, screenshot=screenshot, header=header, cookiejar=cookiejar,
                            proxy=proxy, user_agent=user_agent, parent=parent, priority=priority)
    return task_uuid

######################################################################
######################################################################

# def get_task_status(task_uuid):
#     domain = r_crawler.hget(f'crawler:task:{task_uuid}', 'domain')
#     dom = Domain(domain)
#     meta = {
#         'uuid': task_uuid,
#         'domain': dom.get_id(),
#         'domain_type': dom.get_domain_type(),
#         'start_time': r_crawler.hget(f'crawler:task:{task_uuid}', 'start_time'),
#         'status': 'test',
#     }
#     return meta

# def get_crawlers_tasks_status():
#     tasks_status = []
#     tasks = r_crawler.smembers('crawler:queue:queued')
#     for task_uuid in tasks:
#         tasks_status.append(get_task_status(task_uuid))
#     return tasks_status

##-- CRAWLER TASK --##

#### CRAWLER TASK API ####

# # TODO: ADD user agent
# # TODO: sanitize URL
def api_add_crawler_task(data, user_id=None):
    url = data.get('url', None)
    if not url or url == '\n':
        return {'status': 'error', 'reason': 'No url supplied'}, 400

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
    depth_limit = data.get('depth', 1)
    if depth_limit:
        try:
            depth_limit = int(depth_limit)
            if depth_limit < 0:
                depth_limit = 0
        except ValueError:
            return {'error': 'invalid depth limit'}, 400
    else:
        depth_limit = 0

    cookiejar_uuid = data.get('cookiejar', None)
    if cookiejar_uuid:
        cookiejar = Cookiejar(cookiejar_uuid)
        if not cookiejar.exists():
            return {'error': 'unknown cookiejar uuid', 'cookiejar_uuid': cookiejar_uuid}, 404
        level = cookiejar.get_level()
        if level == 0:  # # TODO: check if user is admin
            if cookiejar.get_user() != user_id:
                return {'error': 'The access to this cookiejar is restricted'}, 403
        cookiejar_uuid = cookiejar.uuid

    # if auto_crawler:
    #     try:
    #         crawler_delta = int(crawler_delta)
    #         if crawler_delta < 0:
    #             return ({'error':'invalid delta between two pass of the crawler'}, 400)
    #     except ValueError:
    #         return ({'error':'invalid delta between two pass of the crawler'}, 400)

    # PROXY
    proxy = data.get('proxy', None)
    if proxy == 'onion' or proxy == 'tor' or proxy == 'force_tor':
        proxy = 'force_tor'
    elif proxy:
        verify = api_verify_proxy(proxy)
        if verify[1] != 200:
            return verify

    # TODO #############################################################################################################
    # auto_crawler = auto_crawler
    # crawler_delta = crawler_delta
    parent = 'manual'

    # TODO HEADERS
    # TODO USER AGENT
    return create_task(url, depth=depth_limit, har=har, screenshot=screenshot, header=None, cookiejar=cookiejar_uuid,
                       proxy=proxy, user_agent=None, parent='manual', priority=90), 200


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

# # # # # # # # # # # #
#                     #
#   CRAWLER MANAGER   # TODO REFACTOR ME
#                     #
# # # # # # # # # # # #

def api_verify_proxy(proxy_url):
    parsed_proxy = urlparse(proxy_url)
    if parsed_proxy.scheme and parsed_proxy.hostname and parsed_proxy.port:
        if parsed_proxy.scheme in ['http', 'https', 'socks5']:
            if (parsed_proxy.username and parsed_proxy.password) != (
                    not parsed_proxy.username and not parsed_proxy.password):
                return proxy_url, 200
            else:
                return {'error': 'You need to enter a username AND a password for your proxy.'}, 400
        else:
            return {'error': 'Proxy scheme not supported: must be http(s) or socks5.'}, 400
    else:
        return {'error': 'Invalid proxy: Check that you entered a scheme, a hostname and a port.'}, 400

def get_proxies():
    return r_crawler.smembers('crawler:proxies')

class CrawlerProxy:
    def __init__(self, proxy_uuid):
        self.uuid = proxy_uuid

    def get_description(self):
        return r_crawler.hgrt(f'crawler:proxy:{self.uuif}', 'description')

    # Host
    # Port
    # Type -> need test
    def get_url(self):
        return r_crawler.hgrt(f'crawler:proxy:{self.uuif}', 'url')

###############################################################################################
###############################################################################################
###############################################################################################
###############################################################################################


# # # # CRAWLER LACUS # # # #

def get_lacus_url():
    return r_db.hget('crawler:lacus', 'url')

def get_lacus_api_key():
    return r_db.hget('crawler:lacus', 'key')

# TODO Rewrite with new API key
def get_hidden_lacus_api_key():
    key = get_lacus_api_key()
    if key:
        if len(key) == 41:
            return f'{key[:4]}*********************************{key[-4:]}'

# TODO Rewrite with new API key
def is_valid_api_key(api_key, search=re.compile(r'[^a-zA-Z0-9_-]').search):
    if len(api_key) != 41:
        return False
    return not bool(search(api_key))

def save_lacus_url_api(url, api_key):
    r_db.hset('crawler:lacus', 'url', url)
    # r_db.hset('crawler:lacus', 'key', api_key)

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
    dict_manager = {}
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
    req_error = None
    lacus = get_lacus()
    if not lacus:
        ping = False
        req_error = {'error': 'Lacus URL undefined', 'status_code': 400}
    else:
        ping = lacus.is_up
    update_lacus_connection_status(ping, req_error=req_error)
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

def get_crawler_max_captures():
    nb_captures = r_cache.hget('crawler:lacus', 'nb_captures')
    if not nb_captures:
        nb_captures = r_db.hget('crawler:lacus', 'nb_captures')
        if not nb_captures:
            nb_captures = 10
            save_nb_max_captures(nb_captures)
        else:
            r_cache.hset('crawler:lacus', 'nb_captures', int(nb_captures))
    return int(nb_captures)

def save_nb_max_captures(nb_captures):
    r_db.hset('crawler:lacus', 'nb_captures', int(nb_captures))
    r_cache.hset('crawler:lacus', 'nb_captures', int(nb_captures))

def api_set_crawler_max_captures(data):
    nb_captures = data.get('nb', 10)
    try:
        nb_captures = int(nb_captures)
        if nb_captures < 1:
            nb_captures = 1
    except (TypeError, ValueError):
        return {'error': 'Invalid number of crawlers to launch'}, 400
    save_nb_max_captures(nb_captures)
    return nb_captures, 200

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

# TODO CREATE TEST TASK
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
    user_agent = f'{commit_id}-AIL LACUS CRAWLER'
    # domain = 'eswpccgr5xyovsahffkehgleqthrasfpfdblwbs4lstd345dwq5qumqd.onion'
    url = 'http://eswpccgr5xyovsahffkehgleqthrasfpfdblwbs4lstd345dwq5qumqd.onion'

    ## LAUNCH CRAWLER, TEST MODE ##
    # set_current_crawler_status(splash_url, 'CRAWLER TEST', started_time=True,
    # crawled_domain='TEST DOMAIN', crawler_type='onion')
    capture_uuid = lacus.enqueue(url=url, depth=0, user_agent=user_agent, proxy='force_tor',
                                 force=True, general_timeout_in_sec=90)
    status = lacus.get_capture_status(capture_uuid)
    launch_time = int(time.time())  # capture timeout
    while int(time.time()) - launch_time < 90 and status != CaptureStatus.DONE:
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
    elif status == 2:
        save_test_ail_crawlers_result(False, 'Timeout Error')
    else:
        save_test_ail_crawlers_result(False, 'Error')
    return False

#### ---- ####


# TODO MOVE ME
load_blacklist()

# if __name__ == '__main__':
#     task = CrawlerTask('2dffcae9-8f66-4cfa-8e2c-de1df738a6cd')
#     print(task.get_meta())

