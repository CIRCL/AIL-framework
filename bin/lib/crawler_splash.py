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
import uuid

from datetime import datetime, timedelta
from urllib.parse import urlparse

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader


config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
config_loader = None

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
# # # #
def create_cookie_dict(browser_cookie=[], cookie_name=None, cookie_value=None, domain=None, crawler_type='regular'):
    # UI created
    if cookie_name and cookie_value and domain:
        dict_cookie = create_cookie_dict_from_input(cookie_name, cookie_value, domain)
    # Cookies imported from the browser
    else:
        dict_cookie = create_cookie_dict_from_browser(browser_cookie)

    # tor browser: disable secure cookie
    if crawler_type=='onion':
        dict_cookie['secure'] = False

    dict_cookie['expires'] = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    return dict_cookie

def create_cookie_dict_from_input(cookie_name, cookie_value, cookie_domain):
    # WebKit use domain for cookie validation
    return {'name': cookie_name, 'value': cookie_value, 'domain': '.{}'.format(cookie_domain)}

# # TODO: handle prefix cookies
# # TODO: fill empty fields
def create_cookie_dict_from_browser(browser_cookie):
    url = urlparse(browser_cookie['Host raw'])
    domain = url.netloc.split(':', 1)[0]
    dict_cookie = {'path': browser_cookie['Path raw'],
                   'name': browser_cookie['Name raw'],
                   'httpOnly': browser_cookie['HTTP only raw'] == 'true',
                   'secure': browser_cookie['Send for'] == 'Encrypted connections only',
                   'domain': domain,
                   'value': browser_cookie['Content raw']
                  }
    return dict_cookie

def load_cookies(cookies_uuid, domain=None, crawler_type='regular'):
    cookies_json, l_cookies = get_cookies(cookies_uuid)
    all_cookies = []
    for cookie_dict in cookies_json:
        all_cookies.append(create_cookie_dict(browser_cookie=cookie_dict, crawler_type=crawler_type))
    for cookie_name, cookie_value in l_cookies:
        all_cookies.append(create_cookie_dict( cookie_name=cookie_name, cookie_value=cookie_value, domain=domain, crawler_type=crawler_type))
    return all_cookies

def get_all_cookies():
    r_serv_onion.smembers('cookies:all')

def get_all_global_cookies():
    r_serv_onion.smembers('cookies:global')

def get_user_cookies(user_id):
    r_serv_onion.smembers('cookies:user:{}'.format(user_id))

def exist_cookies_uuid(cookies_uuid):
    return r_serv_onion.exists('cookie_metadata:{}'.format(cookies_uuid))

def get_manual_cookies_keys(cookies_uuid):
    return r_serv_onion.hgetall('cookies:manual_cookies:{}'.format(cookies_uuid))

def get_manual_cookie_val(cookies_uuid, cookie_name):
    return r_serv_onion.hget('cookies:manual_cookies:{}'.format(cookies_uuid), cookie_name)

def get_cookies(cookies_uuid):
    cookies_json = r_serv_onion.get('cookies:json_cookies:{}'.format(cookies_uuid))
    if cookies_json:
        cookies_json = json.loads(cookies_json)
    else:
        cookies_json = []
    l_cookies = [ ( cookie_name, get_manual_cookie_val(cookies_uuid, cookie_name)) for cookie_name in get_manual_cookies_keys(cookies_uuid) ]
    return (cookies_json, l_cookies)

# # TODO: handle errors + add api handler
def save_cookies(user_id, json_cookies=None, l_cookies=[], cookies_uuid=None, level=1, description=None):
    if cookies_uuid is None or not exist_cookies_uuid(cookies_uuid):
        cookies_uuid = str(uuid.uuid4())

    if json_cookies:
        json_cookies = json.loads(json_cookies) # # TODO: catch Exception
        r_serv_onion.set('cookies:json_cookies:{}'.format(cookies_uuid), json.dumps(json_cookies))

    for cookie_dict in l_cookies:
        r_serv_onion.hset('cookies:manual_cookies:{}'.format(cookies_uuid), cookie_dict['name'], cookie_dict['value'])

    # cookies level # # TODO: edit level set on edit
    r_serv_onion.sadd('cookies:all', cookies_uuid)
    if level==0:
        r_serv_onion.sadd('cookies:user:{}'.format(user_id), cookies_uuid)
    else:
        r_serv_onion.sadd('cookies:global', cookies_uuid)

    # metadata
    r_serv_onion.hset('cookie_metadata:{}'.format(id), 'user_id', user_id)
    r_serv_onion.hset('cookie_metadata:{}'.format(id), 'level', level)
    r_serv_onion.hset('cookie_metadata:{}'.format(id), 'description', description)
    r_serv_onion.hset('cookie_metadata:{}'.format(id), 'date', datetime.date.today().strftime("%Y%m%d"))
    return cookies_uuid

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
