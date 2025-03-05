#!/usr/bin/python3

"""
API Helper
===================


"""
import base64
import gzip
import hashlib
import json
import logging
import os
import pickle
import re
import sys
import time
import uuid

from enum import IntEnum, unique
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

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
from packages import Date
from lib import ail_orgs
from lib.exceptions import OnionFilteringError
from lib.ConfigLoader import ConfigLoader
from lib.regex_helper import regex_findall
from lib.objects.Domains import Domain
from lib.objects.Titles import Title
from lib.objects import HHHashs
from lib.objects.Items import Item
from lib import Tag

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
r_crawler = config_loader.get_db_conn("Kvrocks_Crawler")
r_cache = config_loader.get_redis_conn("Redis_Cache")

ITEMS_FOLDER = config_loader.get_config_str("Directories", "pastes")
HAR_DIR = config_loader.get_files_directory('har')
activate_crawler = config_loader.get_config_str("Crawler", "activate_crawler")
D_HAR = config_loader.get_config_boolean('Crawler', 'default_har')
D_SCREENSHOT = config_loader.get_config_boolean('Crawler', 'default_screenshot')
config_loader = None

faup = Faup()

# logger_crawler = logging.getLogger('crawlers.log')

# # # # # # # #
#             #
#   DOMAINS   #
#             #
# # # # # # # #

# is safe ???
# TODO FILTER URL ???

def api_get_onion_lookup(domain):  # TODO check if object process done ???
    domain = domain.lower()
    url_unpack = unpack_url(domain)
    domain = url_unpack['domain']
    dom = Domain(domain)
    if not is_valid_onion_v3_domain(domain):
        return {'error': 'Invalid Domain', 'domain': domain}, 404
    if not dom.exists():
        if is_crawler_activated():
            create_task(domain, parent='lookup', priority=0, har=D_HAR, screenshot=D_SCREENSHOT)
        return {'error': 'domain not found', 'domain': domain}, 404
    if not dom.was_up():
        return {'error': 'domain not found', 'domain': domain}, 404
    # else
    ## TODO check if object process done -> return result if more than one history
    #   #-> check item history
    meta = dom.get_meta(options={'languages'})
    meta['first_seen'] = meta['first_seen'].replace('/', '-')
    meta['last_seen'] = meta['last_check'].replace('/', '-')
    meta['languages'] = list(meta['languages'])
    tags = []
    for tag in meta['tags']:
        if tag.startswith('dark-web:') or tag.startswith('infoleak:'):
            tags.append(tag)
    meta['tags'] = tags
    del meta['domain']
    del meta['last_check']
    del meta['type']
    del meta['status']
    meta['titles'] = []
    for h in dom.get_correlation('title').get('title', []):
        t = Title(h[1:])
        meta['titles'].append(t.get_content())
    return meta

def api_get_domain_from_url(url):
    url = url.lower()
    url_unpack = unpack_url(url)
    return url_unpack['domain']

## onion correlation cache ##

def is_domain_correlation_cache(domain):
    return r_cache.sismember('cache:domain:correlation', domain)

def add_domain_correlation_cache(domain, obj_gid):
    r_cache.sadd('cache:domain:correlation', domain)
    r_cache.sadd(f'cache:domain:correlation:objs:{domain}', obj_gid)

def save_domain_correlation_cache(is_domain_up, domain):
    if is_domain_up:
        dom = Domain(domain)
        for obj_gid in r_cache.smembers(f'cache:domain:correlation:objs:{domain}'):
            obj_type, obj_subtype, obj_id = obj_gid.split(':', 2)
            if not obj_subtype:
                obj_subtype = ''
            dom.add_correlation(obj_type, obj_subtype, obj_id)
    r_cache.srem('cache:domain:correlation', domain)
    r_cache.delete(f'cache:domain:correlation:objs:{domain}')

# TODO CHECK ALL TASK IF STORED IN DB
def cleanup_domain_correlation_cache(domain):
    pass

# -- #

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

def get_har_dir():
    return HAR_DIR

def is_valid_onion_v3_domain(domain):
    if len(domain) == 62:  # v3 address
        return domain[:56].isalnum()
    return False

def is_valid_onion_domain(domain):
    if not domain.endswith('.onion'):
        return False
    return is_valid_onion_v3_domain(domain)
    # domain = domain.replace('.onion', '', 1)
    # if len(domain) == 16:  # v2 address
    #     r_onion = r'[a-z0-9]{16}'
    #     if re.match(r_onion, domain):
    #         return True
    # elif len(domain) == 56:  # v3 address
    #     r_onion = r'[a-z0-9]{56}'
    #     if re.fullmatch(r_onion, domain):
    #         return True
    # return False

def is_valid_domain(domain):
    faup.decode(domain)
    url_unpack = faup.get()
    unpack_domain = url_unpack['domain'].lower()
    return domain == unpack_domain

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

# TODO options to only extract domains
# TODO extract onions
def extract_url_from_text(content):
    urls = set()
    r_url = r"(?:(?:https?|ftp):\/\/)?(?:\S+(?::\S*)?@)?(?:\[(?:(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}|(?:[A-Fa-f0-9]{1,4}:){1,7}:|(?:[A-Fa-f0-9]{1,4}:){1,6}:[A-Fa-f0-9]{1,4}|::(?:[A-Fa-f0-9]{1,4}:){0,5}[A-Fa-f0-9]{1,4}|(?:[A-Fa-f0-9]{1,4}:){1,5}::(?:[A-Fa-f0-9]{1,4})?|(?:[A-Fa-f0-9]{1,4}:){1,4}::(?:[A-Fa-f0-9]{1,4}:){0,1}[A-Fa-f0-9]{1,4}|(?:[A-Fa-f0-9]{1,3}:){1}::(?:[A-Fa-f0-9]{1,4}:){0,2}[A-Fa-f0-9]{1,4}|(?:[A-Fa-f0-9]{1,2}:){1}::(?:[A-Fa-f0-9]{1,4}:){0,3}[A-Fa-f0-9]{1,4}|[A-Fa-f0-9]{1,4}::(?:[A-Fa-f0-9]{1,4}:){0,4}[A-Fa-f0-9]{1,4}|::(?:[A-Fa-f0-9]{1,4}:){0,5}[A-Fa-f0-9]{1,4}|fe80:(?:[A-Fa-f0-9]{0,4}:){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9])?[0-9])\.){3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9])?[0-9]))\]|(?:(?:25[0-5]|2[0-4]\d|1\d\d|\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|\d{1,2})|(?:(?:[a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}))(?::\d{2,5})?(?:\/[^\s]*)?"
    for url in regex_findall('extract_url_from_text', gen_uuid(), r_url, 'user_id', content, max_time=10):
        if url.startswith('http://'):
            if url in urls:
                continue
        elif not url.startswith('https://'):
            if f'http://{url}' in urls:
                continue
        urls.add(url)
        # check if onions
    return list(urls)
    # extract onions
    # extract IP


# # # # # # # #
#             #
#   FAVICON   # TODO REWRITE ME
#             #
# # # # # # # # TODO CREATE NEW OBJECT

def get_favicon_from_html(html, domain, url):
    favicon_urls, favicons = extract_favicon_from_html(html, url)
    # add root favicon
    if not favicon_urls:
        favicon_urls.add(f'{urlparse(url).scheme}://{domain}/favicon.ico')
    print(favicon_urls)
    return favicon_urls

def extract_favicon_from_html(html, url):
    favicons = set()
    favicons_urls = set()

    soup = BeautifulSoup(html, 'html.parser')
    all_icons = set()
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

    # Root Favicon
    f = get_faup()
    f.decode(url)
    url_decoded = f.get()
    root_domain = f"{url_decoded['scheme']}://{url_decoded['domain']}"
    default_icon = f'{root_domain}/favicon.ico'
    favicons_urls.add(default_icon)
    # print(default_icon)

    # shortcut
    for shortcut in soup.find_all('link', rel='shortcut icon'):
        all_icons.add(shortcut)
    # icons
    for icon in soup.find_all('link', rel='icon'):
        all_icons.add(icon)

    for mask_icon in soup.find_all('link', rel='mask-icon'):
        all_icons.add(mask_icon)
    for apple_touche_icon in soup.find_all('link', rel='apple-touch-icon'):
        all_icons.add(apple_touche_icon)
    for msapplication in soup.find_all('meta', attrs={'name': 'msapplication-TileImage'}):  # msapplication-TileColor
        all_icons.add(msapplication)

    # msapplication-TileImage

    # print(all_icons)
    for tag in all_icons:
        icon_url = tag.get('href')
        if icon_url:
            if icon_url.startswith('data:'):
                data = icon_url.split(',', 1)
                if len(data) > 1:
                    data = ''.join(data[1].split())
                    favicon = base64.b64decode(data)
                    if favicon:
                        favicons.add(favicon)
            else:
                favicon_url = urljoin(url, icon_url)
                favicons_urls.add(favicon_url)
        elif tag.get('name') == 'msapplication-TileImage':
            icon_url = tag.get('content')
            if icon_url:
                if icon_url.startswith('data:'):
                    data = icon_url.split(',', 1)
                    if len(data) > 1:
                        data = ''.join(data[1].split())
                        favicon = base64.b64decode(data)
                        if favicon:
                            favicons.add(favicon)
                else:
                    favicon_url = urljoin(url, icon_url)
                    favicons_urls.add(favicon_url)
                    print(favicon_url)

    # print(favicons_urls)
    return favicons_urls, favicons

# mmh3.hash(favicon)

# # # - - # # #

# # # # # # # #
#             #
#    TITLE    #
#             #
# # # # # # # #

# /!\ REQUIRE ALARM SIGNAL
def extract_title_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title
    if title:
        title = title.string
        if title:
            return str(title)
    return ''

def extract_description_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    description = soup.find('meta', attrs={'name': 'description'})
    if description:
        return description['content']
    return ''

def extract_keywords_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    keywords = soup.find('meta', attrs={'name': 'keywords'})
    if keywords:
        return keywords['content']
    return ''

def extract_author_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    keywords = soup.find('meta', attrs={'name': 'author'})
    if keywords:
        return keywords['content']
    return ''

# # # - - # # #


# # # # # # # #
#             #
#     HAR     #
#             #
# # # # # # # #

def create_har_id(date, item_id):
    item_id = item_id.split('/')[-1]
    return os.path.join(date, f'{item_id}.json.gz')

def save_har(har_id, har_content):
    # create dir
    har_dir = os.path.dirname(os.path.join(get_har_dir(), har_id))
    if not os.path.exists(har_dir):
        os.makedirs(har_dir)
    # save HAR
    filename = os.path.join(get_har_dir(), har_id)
    with gzip.open(filename, 'wb') as f:
        f.write(json.dumps(har_content).encode())

def get_all_har_ids():
    har_ids = []
    today_root_dir = os.path.join(HAR_DIR, Date.get_today_date_str(separator=True))
    dirs_year = set()
    for ydir in next(os.walk(HAR_DIR))[1]:
        if len(ydir) == 4:
            try:
                int(ydir)
                dirs_year.add(ydir)
            except (TypeError, ValueError):
                pass

    if os.path.exists(today_root_dir):
        for file in [f for f in os.listdir(today_root_dir) if os.path.isfile(os.path.join(today_root_dir, f))]:
            har_id = os.path.relpath(os.path.join(today_root_dir, file), HAR_DIR)
            har_ids.append(har_id)

    for ydir in sorted(dirs_year, reverse=False):
        search_dear = os.path.join(HAR_DIR, ydir)
        for root, dirs, files in os.walk(search_dear):
            for file in files:
                if root != today_root_dir:
                    har_id = os.path.relpath(os.path.join(root, file), HAR_DIR)
                    har_ids.append(har_id)
    return har_ids

def get_month_har_ids(year, month):
    har_ids = []
    month_path = os.path.join(HAR_DIR, year, month)
    for root, dirs, files in os.walk(month_path):
        for file in files:
            har_id = os.path.relpath(os.path.join(root, file), HAR_DIR)
            har_ids.append(har_id)
    return har_ids


def get_har_content(har_id):
    har_path = os.path.join(HAR_DIR, har_id)
    try:
        with gzip.open(har_path) as f:
            try:
                return json.loads(f.read())
            except json.decoder.JSONDecodeError:
                return {}
    except Exception as e:
        print(e) # TODO LOGS
        return {}

def extract_cookies_names_from_har(har):
    cookies = set()
    for entrie in har.get('log', {}).get('entries', []):
        for cookie in entrie.get('request', {}).get('cookies', []):
            name = cookie.get('name')
            if name:
                cookies.add(name)
        for cookie in entrie.get('response', {}).get('cookies', []):
            name = cookie.get('name')
            if name:
                cookies.add(name)
    return cookies

def _reprocess_all_hars_cookie_name():
    from lib.objects import CookiesNames
    for har_id in get_all_har_ids():
        domain = har_id.split('/')[-1]
        domain = domain[:-44]
        date = har_id.split('/')
        date = f'{date[-4]}{date[-3]}{date[-2]}'
        for cookie_name in extract_cookies_names_from_har(get_har_content(har_id)):
            print(domain, date, cookie_name)
            cookie = CookiesNames.create(cookie_name)
            cookie.add(date, Domain(domain))

def extract_etag_from_har(har):  # TODO check response url
    etags = set()
    for entrie in har.get('log', {}).get('entries', []):
        for header in entrie.get('response', {}).get('headers', []):
            if header.get('name') == 'etag':
                # print(header)
                etag = header.get('value')
                if etag:
                    etags.add(etag)
    return etags

def _reprocess_all_hars_etag():
    from lib.objects import Etags
    for har_id in get_all_har_ids():
        domain = har_id.split('/')[-1]
        domain = domain[:-44]
        date = har_id.split('/')
        date = f'{date[-4]}{date[-3]}{date[-2]}'
        for etag_content in extract_etag_from_har(get_har_content(har_id)):
            print(domain, date, etag_content)
            etag = Etags.create(etag_content)
            etag.add(date, Domain(domain))

def extract_hhhash_by_id(har_id, domain, date):
    return extract_hhhash(get_har_content(har_id), domain, date)

def extract_hhhash(har, domain, date):
    hhhashs = set()
    urls = set()
    for entrie in har.get('log', {}).get('entries', []):
        url = entrie.get('request').get('url')
        if url not in urls:
            # filter redirect
            if entrie.get('response').get('status') == 200:  # != 301:
                # print(url, entrie.get('response').get('status'))

                f = get_faup()
                f.decode(url)
                domain_url = f.get().get('domain')
                if domain_url == domain:

                    headers = entrie.get('response').get('headers')

                    hhhash_header = HHHashs.build_hhhash_headers(headers)
                    hhhash = HHHashs.hhhash_headers(hhhash_header)

                    if hhhash not in hhhashs:
                        print('', url, hhhash)

                        # -----
                        obj = HHHashs.create(hhhash_header, hhhash)
                        obj.add(date, Domain(domain))

                    hhhashs.add(hhhash)
                    urls.add(url)
    print()
    print()
    print('HHHASH:')
    for hhhash in hhhashs:
        print(hhhash)
    return hhhashs

def _reprocess_all_hars_hhhashs():
    for har_id in get_all_har_ids():
        print()
        print(har_id)
        domain = har_id.split('/')[-1]
        domain = domain[:-44]
        date = har_id.split('/')
        date = f'{date[-4]}{date[-3]}{date[-2]}'
        extract_hhhash_by_id(har_id, domain, date)


def _gzip_har(har_id):
    har_path = os.path.join(HAR_DIR, har_id)
    new_id = f'{har_path}.gz'
    if not har_id.endswith('.gz'):
        if not os.path.exists(new_id):
            with open(har_path, 'rb') as f:
                content = f.read()
            if content:
                with gzip.open(new_id, 'wb') as f:
                    r = f.write(content)
                    print(r)
    if os.path.exists(new_id) and os.path.exists(har_path):
        os.remove(har_path)
        print('delete:', har_path)

def _gzip_all_hars():
    for har_id in get_all_har_ids():
        _gzip_har(har_id)

# # # - - # # #

################################################################################

# # TODO:
# # TODO: REVIEW ME THEN REMOVE ME
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

################################################################################
################################################################################
################################################################################

# # # # # # # # #
#               #
#   COOKIEJARS  #
#               #
# # # # # # # # #

# TODO EDIT COOKIEJAR

def get_cookiejars():
    return r_crawler.smembers('cookiejars:all')

def get_cookiejars_global():
    cookiejars = r_crawler.smembers('cookiejars:global')
    if not cookiejars:
        cookiejars = []
    return cookiejars

def get_cookiejars_org(org_uuid):
    cookiejars = ail_orgs.get_org_objs_by_type(org_uuid, 'cookiejar')
    if not cookiejars:
        cookiejars = []
    return cookiejars

def get_cookiejars_orgs():
    cookiejars = []
    for cookiejar_uuid in get_cookiejars():
        cookiejar = Cookiejar(cookiejar_uuid)
        if cookiejar.get_level() == 2:
            cookiejars.append(cookiejar_uuid)
    return cookiejars

def get_cookiejars_user(user_id):
    cookiejars = r_crawler.smembers(f'cookiejars:user:{user_id}')
    if not cookiejars:
        cookiejars = []
    return cookiejars

def get_cookiejars_users():
    cookiejars = []
    for cookiejar_uuid in get_cookiejars():
        cookiejar = Cookiejar(cookiejar_uuid)
        if cookiejar.get_level() == 0:
            cookiejars.append(cookiejar_uuid)
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

    ## LEVEL ##

    def get_level(self):
        return int(r_crawler.hget(f'cookiejar:meta:{self.uuid}', 'level'))

    def set_level(self, level, org_uuid):
        level = int(level)
        r_crawler.hset(f'cookiejar:meta:{self.uuid}', 'level', level)
        if level == 0:
            r_crawler.sadd(f'cookiejars:user:{self.get_user()}', self.uuid)
        elif level == 1:
            r_crawler.sadd('cookiejars:global', self.uuid)
        elif level == 2:
            self.add_to_org(org_uuid)

    def reset_level(self, old_level, new_level, new_org_uuid):
        if old_level == 0:
            r_crawler.srem(f'cookiejars:user:{self.get_user()}', self.uuid)
        elif old_level == 1:
            r_crawler.srem('cookiejars:global', self.uuid)
        # Org
        elif old_level == 2:
            ail_orgs.remove_obj_to_org(self.get_org(), 'cookiejar', self.uuid)
        self.set_level(new_level, new_org_uuid)

    ## --LEVEL-- ##

    ## ORG ##

    def get_creator_org(self):
        return r_crawler.hget(f'cookiejar:meta:{self.uuid}', 'creator_org')

    def get_org(self):
        return r_crawler.hget(f'cookiejar:meta:{self.uuid}', 'org')

    def add_to_org(self, org_uuid):
        r_crawler.hset(f'cookiejar:meta:{self.uuid}', 'org', org_uuid)
        ail_orgs.add_obj_to_org(org_uuid, 'cookiejar', self.uuid)

        ## -ORG- ##

    def is_cookie_in_jar(self, cookie_uuid):
        # kvrocks sismember TEMP fix
        try:
            return r_crawler.sismember(f'cookiejar:cookies:{self.uuid}', cookie_uuid)
        except:
            return False

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
                'org': self.get_org(),
                'user': self.get_user()}
        meta['org_name'] = ail_orgs.Organisation(meta['org']).get_name()
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

    # TODO Last EDIT
    def create(self, user_org, user_id, level, description=None):
        if self.exists():
            raise Exception('Cookiejar already exists')

        r_crawler.sadd('cookiejars:all', self.uuid)
        r_crawler.hset(f'cookiejar:meta:{self.uuid}', 'creator_org', user_org)

        self._set_user(user_id)
        self.set_level(level, user_org)

        self._set_date(datetime.now().strftime("%Y%m%d"))  # TODO improve DATE
        if description:
            self.set_description(description)

    def delete(self):
        for cookie_uuid in self.get_cookies_uuid():
            self.delete_cookie(cookie_uuid)
        r_crawler.srem(f'cookiejars:user:{self.get_user()}', self.uuid)
        r_crawler.srem('cookiejars:global', self.uuid)
        r_crawler.srem('cookiejars:all', self.uuid)
        level = self.get_level()
        if level == 2:
            ail_orgs.remove_obj_to_org(self.get_org(), 'investigation', self.uuid)
        r_crawler.delete(f'cookiejar:meta:{self.uuid}')


def create_cookiejar(user_org, user_id, description=None, level=1, cookiejar_uuid=None):
    if cookiejar_uuid:
        cookiejar = Cookiejar(cookiejar_uuid)
        if cookiejar.exists():
            cookiejar_uuid = generate_uuid()
    else:
        cookiejar_uuid = generate_uuid()
    cookiejar = Cookiejar(cookiejar_uuid)
    cookiejar.create(user_org, user_id, level, description=description)
    return cookiejar_uuid

def get_cookiejars_meta_by_iterator(iter_cookiejar_uuid):
    cookiejars_meta = []
    for cookiejar_uuid in iter_cookiejar_uuid:
        cookiejar = Cookiejar(cookiejar_uuid)
        cookiejars_meta.append(cookiejar.get_meta(nb_cookies=True))
    return cookiejars_meta

def get_cookiejars_by_user(user_org, user_id):
    cookiejars_global = get_cookiejars_global()
    cookiejars_org = get_cookiejars_org(user_org)
    cookiejars_user = get_cookiejars_user(user_id)
    return [*cookiejars_user, *cookiejars_org, *cookiejars_global]

## API ##

def api_get_cookiejars_selector(user_org, user_id):
    cookiejars = []
    for cookiejar_uuid in get_cookiejars_by_user(user_org, user_id):
        cookiejar = Cookiejar(cookiejar_uuid)
        description = cookiejar.get_description()
        if not description:
            description = ''
        cookiejars.append(f'{description} : {cookiejar.uuid}')
    return sorted(cookiejars)

def api_edit_cookiejar_description(user_org, user_id, user_role, cookiejar_uuid, description):
    resp = api_check_cookiejar_access_acl(cookiejar_uuid, user_org, user_id, user_role, 'edit')
    if resp:
        return resp
    cookiejar = Cookiejar(cookiejar_uuid)
    cookiejar.set_description(description)
    return {'cookiejar_uuid': cookiejar_uuid}, 200

def api_delete_cookiejar(user_org, user_id, user_role, cookiejar_uuid):
    resp = api_check_cookiejar_access_acl(cookiejar_uuid, user_org, user_id, user_role, 'delete')
    if resp:
        return resp
    cookiejar = Cookiejar(cookiejar_uuid)
    cookiejar.delete()
    return {'cookiejar_uuid': cookiejar_uuid}, 200

def api_get_cookiejar(user_org, user_id, user_role, cookiejar_uuid):
    resp = api_check_cookiejar_access_acl(cookiejar_uuid, user_org, user_id, user_role, 'view')
    if resp:
        return resp
    cookiejar = Cookiejar(cookiejar_uuid)
    meta = cookiejar.get_meta(level=True, cookies=True, r_json=True)
    return meta, 200

####  ACL  ####

def api_check_cookiejar_access_acl(cookiejar_uuid, user_org, user_id, user_role, action):
    cookiejar = Cookiejar(cookiejar_uuid)
    if not cookiejar.exists():
        return {'error': 'unknown cookiejar uuid', 'cookiejar_uuid': cookiejar_uuid}, 404
    if not ail_orgs.check_obj_access_acl(cookiejar, user_org, user_id, user_role, action):
        return {"status": "error", "reason": "Access Denied"}, 403

####  API  ####

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
            meta = {'data': data, 'uuid': self.uuid}
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

def api_get_cookie(user_org, user_id, user_role, cookie_uuid):
    cookie = Cookie(cookie_uuid)
    if not cookie.exists():
        return {'error': 'unknown cookie uuid', 'cookie_uuid': cookie_uuid}, 404
    resp = api_check_cookiejar_access_acl(cookie.get_cookiejar(), user_org, user_id, user_role, 'view')
    if resp:
        return resp
    return cookie.get_meta()

def api_edit_cookie(user_org, user_id, user_role, cookie_uuid, cookie_dict):
    cookie = Cookie(cookie_uuid)
    if not cookie.exists():
        return {'error': 'unknown cookie uuid', 'cookie_uuid': cookie_uuid}, 404
    resp = api_check_cookiejar_access_acl(cookie.get_cookiejar(), user_org, user_id, user_role, 'edit')
    if resp:
        return resp
    if 'name' not in cookie_dict or 'value' not in cookie_dict or not cookie_dict['name'] or not cookie_dict['value']:
        return {'error': 'cookie name or value not provided'}, 400
    cookie.edit(cookie_dict)
    return cookie.get_meta(), 200

def api_create_cookie(user_org, user_id, user_role, cookiejar_uuid, cookie_dict):
    resp = api_check_cookiejar_access_acl(cookiejar_uuid, user_org, user_id, user_role, 'edit')
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

def api_delete_cookie(user_org, user_id, user_role, cookie_uuid):
    cookie = Cookie(cookie_uuid)
    if not cookie.exists():
        return {'error': 'unknown cookie uuid', 'cookie_uuid': cookie_uuid}, 404
    cookiejar_uuid = cookie.get_cookiejar()
    resp = api_check_cookiejar_access_acl(cookiejar_uuid, user_org, user_id, user_role, 'edit')
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
def api_import_cookies_from_json(user_org, user_id, user_role, cookiejar_uuid, json_cookies_str):  # # TODO: add catch
    resp = api_check_cookiejar_access_acl(cookiejar_uuid, user_org, user_id, user_role, 'edit')
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
    return 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'

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

def get_crawlers_stats_by_month(domain_type, date=None):
    stats = []
    for date in Date.get_month_dates(date=date):
        stats.append(get_crawlers_stats_by_day(date, domain_type))
    return stats

def get_crawlers_stats_up_down_by_month(domain_type, date=None):
    stats = {'down': 0, 'up': 0}
    for date in Date.get_month_dates(date=date):
        day = get_crawlers_stats_by_day(date, domain_type)
        stats['down'] += day.get('down', 0)
        stats['up'] += day.get('up', 0)
    return stats

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

def reload_crawlers_stats():
    for domain_type in get_crawler_all_types():
        tasks = r_crawler.smembers(f'crawler:queue:type:{domain_type}')
        for task_uuid in tasks:
            task = CrawlerTask(task_uuid)
            if not task.is_in_queue() and task.get_status() is None:
                capture = task.get_capture()
                if capture:
                    c = CrawlerCapture(capture)
                    if not c.exists():
                        task.delete()
                else:
                    task.delete()

#### Blocklist ####

def get_blacklist():
    return r_crawler.smembers('blacklist:domain')

def is_blacklisted_domain(domain):
    # kvrocks sismember TEMP fix
    try:
        return r_crawler.sismember('blacklist:domain', domain)
    except:
        return False

def blacklist_domain(domain):
    return r_crawler.sadd('blacklist:domain', domain)

def unblacklist_domain(domain):
    return r_crawler.srem('blacklist:domain', domain)

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

def api_blacklist_domain(data):
    domain = str(data.get('domain', '')).lower()
    if not is_valid_domain(domain):
        return {'error': 'invalid domain'}, 400
    if is_blacklisted_domain(domain):
        return {'error': 'domain already blacklisted'}, 400
    return blacklist_domain(domain), 200

def api_unblacklist_domain(data):
    domain = str(data.get('domain', '')).lower()
    if not is_valid_domain(domain):
        return {'error': 'invalid domain'}, 400
    if not is_blacklisted_domain(domain):
        return {'error': 'domain not blacklisted'}, 404
    return unblacklist_domain(domain), 200

#### CRAWLER Scheduler ####

@unique
class ScheduleStatus(IntEnum):
    """The status of the capture"""
    UNKNOWN = -1
    QUEUED = 0
    SCHEDULED = 1
    ONGOING = 2

def get_schedulers_uuid():
    return r_crawler.smembers('scheduler:schedules')

def get_schedulers_metas():
    schedulers = []
    for schedule_uuid in get_schedulers_uuid():
        schedule = CrawlerSchedule(schedule_uuid)
        schedulers.append(schedule.get_meta_status())
    return schedulers

class CrawlerScheduler:

    def __init__(self):
        self.min_frequency = 60  # TODO ADD IN CONFIG

    def update_queue(self):
        for schedule_uuid in get_schedulers_uuid():
            schedule = CrawlerSchedule(schedule_uuid)
            # check if already in scheduler queue
            if schedule.is_scheduled():
                continue
            if schedule.is_tasked():
                continue

            # EXPIRE ????

            time_next_run = 0.0
            frequency = schedule.get_frequency()  # optional or later -> cron
            if frequency == 'hourly':
                time_next_run = (datetime.now() + timedelta(hours=1)).timestamp()
            elif frequency == 'daily':
                time_next_run = (datetime.now() + timedelta(days=1)).timestamp()
            elif frequency == 'weekly':
                time_next_run = (datetime.now() + timedelta(weeks=1)).timestamp()
            elif frequency == 'monthly':
                time_next_run = (datetime.now() + relativedelta(months=1)).timestamp()
            else:
                months, weeks, days, hours, minutes = frequency.split(':')
                if not months:
                    months = 0
                if not weeks:
                    weeks = 0
                if not days:
                    days = 0
                if not hours:
                    hours = 0
                if not minutes:
                    minutes = 0
                current_time = datetime.now().timestamp()
                time_next_run = (datetime.now() + relativedelta(months=int(months), weeks=int(weeks),
                                                                days=int(days), hours=int(hours),
                                                                minutes=int(minutes))).timestamp()
                # Make sure the next capture is not scheduled for in a too short interval
                interval_next_capture = time_next_run - current_time
                if interval_next_capture < self.min_frequency:
                    # self.logger.warning(f'The next capture is scheduled too soon: {interval_next_capture}s. Minimal interval: {self.min_frequency}s.')
                    print(f'The next capture is scheduled too soon: {interval_next_capture}s. Minimal interval: {self.min_frequency}s.')
                    time_next_run = (datetime.now() + timedelta(seconds=self.min_frequency)).timestamp()

            schedule.set_next_run(time_next_run)
            print('scheduled:', schedule_uuid)

    def process_queue(self):
        now = datetime.now().timestamp()
        for raw_schedule in r_crawler.zrangebyscore('scheduler:queue', '-inf', int(now), withscores=True):
            schedule_uuid, next_run = raw_schedule
            schedule = CrawlerSchedule(schedule_uuid)
            if not schedule.exists():
                return None
            meta = schedule.get_meta()
            task_uuid = create_task(meta['url'], depth=meta['depth'], har=meta['har'], screenshot=meta['screenshot'],
                                    header=meta['header'],
                                    cookiejar=meta['cookiejar'], proxy=meta['proxy'],
                                    tags=meta['tags'],
                                    user_agent=meta['user_agent'], parent='scheduler', priority=40)
            if task_uuid:
                schedule.set_task(task_uuid)
                r_crawler.zrem('scheduler:queue', schedule_uuid)


# TODO Expire -> stuck in crawler queue or reached delta
class CrawlerSchedule:
    def __init__(self, schedule_uuid):
        self.uuid = schedule_uuid

    def exists(self):
        return r_crawler.exists(f'schedule:{self.uuid}')

    def get_frequency(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'frequency')

    def get_user(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'user')

    def get_date(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'date')

    def get_captures(self): # only scheduled capture ????? exclude manual/discovery
        pass

    def get_status(self):
        if self.is_scheduled():
            return ScheduleStatus.SCHEDULED
        if self.is_tasked():
            if self.is_ongoing():
                return ScheduleStatus.ONGOING
            else:
                return ScheduleStatus.QUEUED
        return ScheduleStatus.UNKNOWN

    def get_task_uuid(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'task')

    def is_tasked(self):
        task_uuid = self.get_task_uuid()
        if task_uuid:
            task = CrawlerTask(task_uuid)
            tasked = task.exists()
            if not tasked:
                r_crawler.hdel(f'schedule:{self.uuid}', 'task')
            return tasked
        return False

    def get_task(self):
        task_uuid = self.get_task_uuid()
        if task_uuid:
            return CrawlerTask(task_uuid)

    def set_task(self, task_uuid):
        return r_crawler.hset(f'schedule:{self.uuid}', 'task', task_uuid)

    def is_ongoing(self):
        task = self.get_task()
        if task:
            return task.is_ongoing()
        return False

    def get_next_run(self, r_str=False):
        next_run = r_crawler.zscore('scheduler:queue', self.uuid)
        if next_run and r_str:
            next_run = time.strftime('%Y-%m-%d - %H:%M:%S', time.localtime(int(next_run)))
        return next_run

    def set_next_run(self, time_next_run):
        r_crawler.zadd('scheduler:queue', mapping={self.uuid: time_next_run})

    def is_scheduled(self):
        return bool(r_crawler.zscore('scheduler:queue', self.uuid))

    def get_url(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'url')

    def get_depth(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'depth')

    def get_har(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'har') == 'True'

    def get_screenshot(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'screenshot') == 'True'

    def get_header(self):
        r_crawler.hget(f'schedule:{self.uuid}', 'header')

    def get_cookiejar(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'cookiejar')

    def get_proxy(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'proxy')

    def get_user_agent(self):
        return r_crawler.hget(f'schedule:{self.uuid}', 'user_agent')

    def _set_field(self, field, value):
        return r_crawler.hset(f'schedule:{self.uuid}', field, value)

    def get_tags(self):
        return r_crawler.smembers(f'schedule:tags:{self.uuid}')

    def set_tags(self, tags=[]):
        for tag in tags:
            r_crawler.sadd(f'schedule:tags:{self.uuid}', tag)
            # Tag.create_custom_tag(tag)

    def get_meta(self, ui=False):
        meta = {
            'uuid': self.uuid,
            'date': self.get_date(),
            'frequency': self.get_frequency(),
            'user': self.get_user(),
            'url': self.get_url(),
            'depth': self.get_depth(),
            'har': self.get_har(),
            'screenshot': self.get_screenshot(),
            'user_agent': self.get_user_agent(),
            'cookiejar': self.get_cookiejar(),
            'header': self.get_header(),
            'proxy': self.get_proxy(),
            'tags': self.get_tags(),
        }
        status = self.get_status()
        if ui:
            status = status.name
            r_str = True
        else:
            r_str = False
        meta['status'] = status
        meta['next_run'] = self.get_next_run(r_str=r_str)
        return meta

    def get_meta_status(self):  # TODO:  Description ? Frequency ???
        meta = {'uuid': self.uuid,
                'url': self.get_url(),
                'user': self.get_user(),
                'tags': self.get_tags(),
                'next_run': self.get_next_run(r_str=True)}
        status = self.get_status()
        if isinstance(status, ScheduleStatus):
            status = status.name
        meta['status'] = status
        return meta

    def create(self, frequency, user, url,
               depth=1, har=True, screenshot=True, header=None, cookiejar=None, proxy=None, user_agent=None, tags=[]):

        if self.exists():
            raise Exception('Error: Monitor already exists')

        url_decoded = unpack_url(url)
        url = url_decoded['url']

        self._set_field('date', datetime.now().strftime("%Y-%m-%d"))
        self._set_field('frequency', frequency)
        self._set_field('user', user)
        self._set_field('url', url)
        self._set_field('depth', int(depth))
        self._set_field('har', str(har))
        self._set_field('screenshot', str(screenshot))

        if cookiejar:
            self._set_field('cookiejar', cookiejar)
        if header:
            self._set_field('header', header)
        if proxy:
            if proxy == 'web':
                proxy = None
            elif proxy == 'force_tor' or proxy == 'tor' or proxy == 'onion':
                proxy = 'force_tor'
            self._set_field('proxy', proxy)
        if user_agent:
            self._set_field('user_agent', user_agent)

        if tags:
            self.set_tags(tags)

        r_crawler.sadd('scheduler:schedules', self.uuid)

    def delete(self):
        # remove from schedule queue
        r_crawler.zrem('scheduler:queue', self.uuid)

        # delete task
        task = self.get_task()
        if task:
            task.delete()

        # delete meta
        r_crawler.delete(f'schedule:{self.uuid}')
        r_crawler.delete(f'schedule:tags:{self.uuid}')
        r_crawler.srem('scheduler:schedules', self.uuid)

def create_schedule(frequency, user, url, depth=1, har=True, screenshot=True, header=None, cookiejar=None, proxy=None, user_agent=None, tags=[]):
    schedule_uuid = gen_uuid()
    schedule = CrawlerSchedule(schedule_uuid)
    schedule.create(frequency, user, url, depth=depth, har=har, screenshot=screenshot, header=header, cookiejar=cookiejar, proxy=proxy, user_agent=user_agent, tags=tags)
    return schedule_uuid

def _delete_schedules():
    for schedule_uuid in get_schedulers_uuid():
        schedule = CrawlerSchedule(schedule_uuid)
        schedule.delete()

# TODO sanityze UUID
def api_delete_schedule(data):
    schedule_uuid = data.get('uuid')
    schedule = CrawlerSchedule(schedule_uuid)
    if not schedule.exists():
        return {'error': 'unknown schedule uuid', 'uuid': schedule}, 404
    return schedule.delete(), 200

#### CRAWLER CAPTURE ####

def get_nb_crawler_captures():
    return r_cache.zcard('crawler:captures')

def get_crawler_captures():
    return r_crawler.zrange('crawler:captures', 0, -1)

def reload_crawler_captures():
    r_cache.delete('crawler:captures')
    for capture_uuid in get_crawler_captures():
        capture = CrawlerCapture(capture_uuid)
        capture.update(None)

def _clear_captures():
    for capture_uuid in get_crawler_captures():
        capture = CrawlerCapture(capture_uuid)
        task = capture.get_task()
        task.delete()
        capture.delete()
        print(capture_uuid, 'deleted')

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

    def get_start_time(self, r_str=True):
        start_time = self.get_task().get_start_time()
        if r_str:
            return start_time
        elif not start_time:
            return 0
        else:
            start_time = datetime.strptime(start_time, "%Y/%m/%d  -  %H:%M.%S").timestamp()
            return int(start_time)

    def get_status(self):
        status = r_cache.hget(f'crawler:capture:{self.uuid}', 'status')
        if not status:
            status = -1
        return status

    def is_ongoing(self):
        return self.get_status() == CaptureStatus.ONGOING

    def create(self, task_uuid):
        if self.exists():
            print(f'Capture {self.uuid} already exists')  # TODO LOGS
            return None
        launch_time = int(time.time())
        r_crawler.hset(f'crawler:task:{task_uuid}', 'capture', self.uuid)
        r_crawler.hset('crawler:captures:tasks', self.uuid, task_uuid)
        r_cache.hset(f'crawler:capture:{self.uuid}', 'launch_time', launch_time)
        r_crawler.zadd('crawler:captures', {self.uuid: launch_time})
        r_cache.zadd('crawler:captures', {self.uuid: launch_time})

    def update(self, status):
        # Error or Reload
        if status is None:
            r_cache.hset(f'crawler:capture:{self.uuid}', 'status', CaptureStatus.UNKNOWN.value)
            r_cache.zadd('crawler:captures', {self.uuid: 0})
        else:
            last_check = int(time.time())
            r_cache.hset(f'crawler:capture:{self.uuid}', 'status', status)
            r_cache.zadd('crawler:captures', {self.uuid: last_check})

    # Crawler
    def remove(self):
        r_crawler.zrem('crawler:captures', self.uuid)
        r_cache.delete(f'crawler:capture:{self.uuid}')
        r_crawler.hdel('crawler:captures:tasks', self.uuid)

    # Manual
    def delete(self):
        # remove Capture from crawler queue
        r_cache.zrem('crawler:captures', self.uuid)
        self.remove()


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
        if not task:
            meta = {
                'uuid': 'UNKNOWN',
                'domain': 'UNKNOWN',
                'type': 'UNKNOWN',
                'start_time': capture.get_start_time(),
                'status': capture.get_status(),
            }
        else:
            domain = task.get_domain()
            dom = Domain(domain)
            meta = {
                'uuid': task.uuid,
                'domain': dom.get_id(),
                'type': dom.get_domain_type(),
                'start_time': capture.get_start_time(),
                'status': capture.get_status(),
            }
        capture_status = capture.get_status()
        if capture_status:
            capture_status = CaptureStatus(int(capture_status)).name
        meta['status'] = capture_status
        status.append(meta)
    return status

def delete_captures():
    for capture_uuid in get_crawler_captures():
        capture = CrawlerCapture(capture_uuid)
        capture.delete()

## --CRAWLER STATE-- ##


#### CRAWLER TASK ####

class CrawlerTask:

    def __init__(self, task_uuid):
        self.uuid = task_uuid

    def exists(self):
        return r_crawler.exists(f'crawler:task:{self.uuid}')

    def is_in_queue(self):
        if r_crawler.zscore('crawler:queue', self.uuid) is not None:
            return True
        else:
            return False

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

    def is_ongoing(self):
        capture_uuid = self.get_capture()
        if capture_uuid:
            return CrawlerCapture(capture_uuid).is_ongoing()
        return False

    def _set_field(self, field, value):
        return r_crawler.hset(f'crawler:task:{self.uuid}', field, value)

    def get_tags(self):
        return r_crawler.smembers(f'crawler:task:tags:{self.uuid}')

    def set_tags(self, tags):
        for tag in tags:
            r_crawler.sadd(f'crawler:task:tags:{self.uuid}', tag)
            # Tag.create_custom_tag(tag)

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
            'tags': self.get_tags(),
        }
        return meta

    # TODO STATUS UPDATE
    # TODO SANITIZE PRIORITY
    # PRIORITY:  discovery = 0/10, feeder = 10, manual = 50, auto = 40, test = 100
    def create(self, url, depth=1, har=True, screenshot=True, header=None, cookiejar=None, proxy=None,
               user_agent=None, tags=[], parent='manual', priority=0, external=False):
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

        # TODO SANITIZE COOKIEJAR -> UUID

        # Check if already in queue
        hash_query = get_task_hash(url, domain, depth, har, screenshot, priority, proxy, cookiejar, user_agent, header, tags)
        if r_crawler.hexists(f'crawler:queue:hash', hash_query):
            self.uuid = r_crawler.hget(f'crawler:queue:hash', hash_query)
            return self.uuid

        self._set_field('domain', domain)
        self._set_field('url', url)
        self._set_field('depth', int(depth))
        self._set_field('har', har)
        self._set_field('screenshot', screenshot)
        self._set_field('parent', parent)

        if cookiejar:
            self._set_field('cookiejar', cookiejar)
        if header:
            self._set_field('header', header)
        if proxy:
            self._set_field('proxy', proxy)
        if user_agent:
            self._set_field('user_agent', user_agent)

        if tags:
            self.set_tags(tags)

        r_crawler.hset('crawler:queue:hash', hash_query, self.uuid)
        self._set_field('hash', hash_query)
        if not external:
            self.add_to_db_crawler_queue(priority)
        # UI
        domain_type = dom.get_domain_type()
        r_crawler.sadd(f'crawler:queue:type:{domain_type}', self.uuid)
        self._set_field('queue', domain_type)
        return self.uuid

    def add_to_db_crawler_queue(self, priority):
        r_crawler.zadd('crawler:queue', {self.uuid: priority})

    def start(self):
        self._set_field('start_time', datetime.now().strftime("%Y/%m/%d  -  %H:%M.%S"))

    def reset(self):
        priority = 49
        r_crawler.hdel(f'crawler:task:{self.uuid}', 'start_time')
        self.add_to_db_crawler_queue(priority)

    # Crawler
    def remove(self):  # zrem cache + DB
        capture_uuid = self.get_capture()
        if capture_uuid:
            capture = CrawlerCapture(capture_uuid)
            capture.remove()
        queue_type = self.get_queue()
        if queue_type:
            r_crawler.srem(f'crawler:queue:type:{queue_type}', self.uuid)
        task_hash = self.get_hash()
        if task_hash:
            r_crawler.hdel('crawler:queue:hash', task_hash)
        # meta
        r_crawler.delete(f'crawler:task:{self.uuid}')

    # Manual
    def delete(self):
        # queue
        r_crawler.zrem('crawler:queue', self.uuid)
        self.remove()


# TODO move to class ???
def get_task_hash(url, domain, depth, har, screenshot, priority, proxy, cookiejar, user_agent, header, tags):
    to_enqueue = {'domain': domain, 'depth': depth, 'har': har, 'screenshot': screenshot,
                  'priority': priority, 'proxy': proxy, 'cookiejar': cookiejar, 'user_agent': user_agent,
                  'header': header, 'tags': tags}
    if priority != 0:
        to_enqueue['url'] = url
    return hashlib.sha512(pickle.dumps(to_enqueue)).hexdigest()

def add_task_to_lacus_queue():
    task_uuid = r_crawler.zpopmax('crawler:queue')
    if not task_uuid or not task_uuid[0]:
        return None
    task_uuid, priority = task_uuid[0]
    task = CrawlerTask(task_uuid)
    return task, priority

# PRIORITY:  discovery = 0/10, feeder = 10, manual = 50, auto = 40, test = 100
def create_task(url, depth=1, har=True, screenshot=True, header=None, cookiejar=None, proxy=None,
                user_agent=None, tags=[], parent='manual', priority=0, task_uuid=None, external=False):
    if task_uuid:
        if CrawlerTask(task_uuid).exists():
            task_uuid = gen_uuid()
    else:
        task_uuid = gen_uuid()
    task = CrawlerTask(task_uuid)
    task_uuid = task.create(url, depth=depth, har=har, screenshot=screenshot, header=header, cookiejar=cookiejar,
                            proxy=proxy, user_agent=user_agent, tags=tags, parent=parent, priority=priority,
                            external=external)
    return task_uuid

## -- CRAWLER TASK -- ##

#### CRAWLER TASK API ####

# # TODO: ADD user agent
# # TODO: sanitize URL

def api_parse_task_dict_basic(data, user_id):
    url = data.get('url', None)
    urls = data.get('urls', None)
    if (not url or url == '\n') and not urls:
        return {'status': 'error', 'reason': 'No url(s) supplied'}, 400

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

    # PROXY
    proxy = data.get('proxy', None)
    if proxy == 'onion' or proxy == 'tor' or proxy == 'force_tor':
        proxy = 'force_tor'
    elif proxy:
        verify = api_verify_proxy(proxy)
        if verify[1] != 200:
            return verify

    tags = data.get('tags', [])

    data = {'depth_limit': depth_limit, 'har': har, 'screenshot': screenshot, 'proxy': proxy, 'tags': tags}
    if url :
        data['url'] = url
    elif urls:
        data['urls'] = urls
    return data, 200

def api_add_crawler_task(data, user_org, user_id=None):
    task, resp = api_parse_task_dict_basic(data, user_id)
    if resp != 200:
        return task, resp

    url = task.get('url')
    urls = task.get('urls')
    screenshot = task['screenshot']
    har = task['har']
    depth_limit = task['depth_limit']
    proxy = task['proxy']
    tags = task['tags']

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

    cookies = data.get('cookies', None)
    if not cookiejar_uuid and cookies:
        # Create new cookiejar
        cookiejar_uuid = create_cookiejar(user_org, user_id, "single-shot cookiejar", 1, None)  # TODO REVIEW DEFAULT LEVEL
        cookiejar = Cookiejar(cookiejar_uuid)
        for cookie in cookies:
            try:
                name = cookie.get('name')
                value = cookie.get('value')
                cookiejar.add_cookie(name, value, None, None, None, None, None)
            except KeyError:
                return {'error': 'Invalid cookie key, please submit a valid JSON', 'cookiejar_uuid': cookiejar_uuid}, 400

    frequency = data.get('frequency', None)
    if frequency:
        if frequency not in ['monthly', 'weekly', 'daily', 'hourly']:
            if not isinstance(frequency, dict):
                return {'error': 'Invalid frequency'}, 400
            else:
                try:
                    months = int(frequency.get('months', 0))
                    weeks = int(frequency.get('weeks', 0))
                    days = int(frequency.get('days', 0))
                    hours = int(frequency.get('hours', 0))
                    minutes = int(frequency.get('minutes', 0))
                except (TypeError, ValueError):
                    return {'error': 'Invalid frequency'}, 400
                if min(months, weeks, days, hours, minutes) < 0:
                    return {'error': 'Invalid frequency'}, 400
                if max(months, weeks, days, hours, minutes) <= 0:
                    return {'error': 'Invalid frequency'}, 400
                frequency = f'{months}:{weeks}:{days}:{hours}:{minutes}'
    if url:
        if frequency:
            # TODO verify user
            task_uuid = create_schedule(frequency, user_id, url, depth=depth_limit, har=har, screenshot=screenshot, header=None,
                                        cookiejar=cookiejar_uuid, proxy=proxy, user_agent=None, tags=tags)
        else:
            # TODO HEADERS
            # TODO USER AGENT
            task_uuid = create_task(url, depth=depth_limit, har=har, screenshot=screenshot, header=None,
                                    cookiejar=cookiejar_uuid, proxy=proxy, user_agent=None, tags=tags,
                                    parent='manual', priority=90)
    elif urls:
        for url in urls:
            task_uuid = create_task(url, depth=depth_limit, har=har, screenshot=screenshot, header=None,
                                    cookiejar=cookiejar_uuid, proxy=proxy, user_agent=None, tags=tags,
                                    parent='manual', priority=90)

    return {'uuid': task_uuid}, 200


#### ####

# TODO cookiejar - cookies - frequency
def api_add_crawler_capture(data, user_id):
    task, resp = api_parse_task_dict_basic(data, user_id)
    if resp != 200:
        return task, resp

    task_uuid = data.get('task_uuid')
    if not task_uuid:
        return {'error': 'Invalid task_uuid', 'task_uuid': task_uuid}, 400
    capture_uuid = data.get('capture_uuid')
    if not capture_uuid:
        return {'error': 'Invalid capture_uuid', 'capture_uuid': capture_uuid}, 400

    # parent = data.get('parent')

    # TODO parent
    task_uuid = create_task(task['url'], depth=task['depth_limit'], har=task['har'], screenshot=task['screenshot'],
                            proxy=task['proxy'], tags=task['tags'],
                            parent='manual', task_uuid=task_uuid, external=True)
    if not task_uuid:
        return {'error': 'Aborted by Crawler', 'task_uuid': task_uuid, 'capture_uuid': capture_uuid}, 400
    task = CrawlerTask(task_uuid)
    create_capture(capture_uuid, task_uuid)
    task.start()
    return {'uuid': capture_uuid}, 200

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

##-- CRAWLER GLOBAL --##


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
        n_uuid = domain[-215:]+str(uuid.uuid4())
    else:
        n_uuid = domain+str(uuid.uuid4())
    return os.path.join(item_dir, n_uuid)

# # # # # # # # # # # #
#                     #
#   CRAWLER MANAGER   # TODO REFACTOR ME
#                     #
# # # # # # # # # # # #

#### PROXY ####

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
        return r_crawler.hget(f'crawler:proxy:{self.uuid}', 'description')

    # Host
    # Port
    # Type -> need test
    def get_url(self):
        return r_crawler.hget(f'crawler:proxy:{self.uuid}', 'url')

#### CRAWLER LACUS ####

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
        try:
            ping = lacus.is_up
        except:
            req_error = {'error': 'Failed to connect Lacus URL', 'status_code': 400}
            ping = False
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
    if not manager_url:  # or not api_key:
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

## TEST ##

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


# # # # # # # # # # # # #
#                       #
#   CONTENT FILTERING   #
#                       #
# # # # # # # # # # # # #

def _onion_lookup(onion_url):
    try:
        commit_id = git_status.get_last_commit_id_from_local()
        user_agent = f'AIL-{commit_id}'
        headers = {'User-Agent': user_agent}
        response = requests.get(f'https://onion.ail-project.org/api/lookup/{onion_url}', timeout=10, headers=headers)
        if response.status_code == 200:
            json_response = response.json()
            return json_response
        else:
            print(response)
            return {'error': f'{response.status_code}'}
    except requests.exceptions.ConnectionError:
        return {'error': f'Connection Error'}
    except requests.exceptions.ReadTimeout:
        return {'error': f'Timeout Error'}


def check_if_onion_is_safe(onion_url, unknown):
    resp = _onion_lookup(onion_url)
    if resp:
        if isinstance(resp, dict):
            if 'tags' in resp:
                return Tag.is_tags_safe(resp['tags'])
            elif 'error' in resp:
                if resp['error']:
                    raise OnionFilteringError(resp['error'])
        elif not unknown:
            if isinstance(resp, list):
                if len(resp) > 1:
                    if resp[1] == 404:
                        return True
    return False


def _is_onion_filter_enabled():
    enabled = r_crawler.hget('crawler:onion_filter', 'enabled')
    if enabled is None:
        r_crawler.hset('crawler:onion_filter', 'enabled', str(True))
        filter_enabled = True
    else:
        filter_enabled = enabled == 'True'
    r_cache.set('crawler:onion_filter:state', str(filter_enabled))
    return filter_enabled

def is_onion_filter_enabled(cache=True):
    if cache:
        res = r_cache.get('crawler:onion_filter:state')
        if res is None:
            enabled = _is_onion_filter_enabled()
            r_cache.set('crawler:onion_filter:state', str(enabled))
            return enabled
        else:
            return res == 'True'
    else:
        return _is_onion_filter_enabled()

def get_onion_filter_last_update_time():
    last_update_time = r_cache.get('crawler:onion_filter:last_update_time')
    if not last_update_time:
        last_update_time = r_crawler.hget('crawler:onion_filter', 'update_time')
        if not last_update_time:
            last_update_time = 0
        last_update_time = float(last_update_time)
        r_cache.set('crawler:onion_filter:last_update_time', last_update_time)
    return float(last_update_time)

def change_onion_filter_state(new_state):
    old_state = is_onion_filter_enabled(cache=False)
    if old_state != new_state:
        r_crawler.hset('crawler:onion_filter', 'enabled', str(new_state))
        r_cache.set('crawler:onion_filter:state', str(new_state))
        update_time = time.time()
        r_crawler.hset('crawler:onion_filter', 'update_time', update_time)
        r_cache.set('crawler:onion_filter:last_update_time', update_time)
        return True
    return False

# # Crawl Unknown Onion # #
def _is_onion_filter_unknown():
    unknown = r_crawler.hget('crawler:onion_filter', 'unknown')
    if unknown is None:
        r_crawler.hset('crawler:onion_filter', 'unknown', str(False))
        filter_enabled = False
    else:
        filter_enabled = unknown == 'True'
    r_cache.set('crawler:onion_filter:unknown', str(filter_enabled))
    return filter_enabled

def is_onion_filter_unknown(cache=True):
    if cache:
        res = r_cache.get('crawler:onion_filter:unknown')
        if res is None:
            unknown = _is_onion_filter_unknown()
            r_cache.set('crawler:onion_filter:unknown', str(unknown))
            return unknown
        else:
            return res == 'True'
    else:
        return _is_onion_filter_unknown()

def change_onion_filter_unknown_state(new_state):
    old_state = is_onion_filter_unknown(cache=False)
    if old_state != new_state:
        r_crawler.hset('crawler:onion_filter', 'unknown', str(new_state))
        r_cache.set('crawler:onion_filter:unknown', str(new_state))
        update_time = time.time()
        r_crawler.hset('crawler:onion_filter', 'update_time', update_time)
        r_cache.set('crawler:onion_filter:last_update_time', update_time)
        return True
    return False

#### ---- ####


# TODO MOVE ME IN CRAWLER OR FLASK
load_blacklist()

# if __name__ == '__main__':
#     delete_captures()
#
#     item_id = 'crawled/2023/02/20/data.gz'
#     item = Item(item_id)
#     content = item.get_content()
#     temp_url = ''
#     r = extract_favicon_from_html(content, temp_url)
#     print(r)
#     _reprocess_all_hars_cookie_name()
#     _reprocess_all_hars_etag()
#     _gzip_all_hars()
#     _reprocess_all_hars_hhhashs()
