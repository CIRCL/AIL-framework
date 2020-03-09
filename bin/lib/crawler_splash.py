#!/usr/bin/python3

"""
API Helper
===================


"""

import json
import os
import re
import redis
import sys

from datetime import datetime, timedelta
from urllib.parse import urlparse

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))

# # # #
# Cookies Fields:
#   - name
#   - value
#   - path
#   - domain
# # # #
def create_cookie_dict(cookie):
    url = urlparse(cookie['Host raw'])
    #scheme = url.scheme
    is_secure = cookie['Send for'] == 'Encrypted connections only'
    if 'HTTP only raw' in cookie:
        if cookie['HTTP only raw'] == "true":
            is_secure = False
    domain = url.netloc.split(':', 1)[0]
    dict_cookie = {'path': cookie['Path raw'],
                   'name': cookie['Name raw'],
                   'httpOnly': cookie['HTTP only raw'] == 'true',
                   'secure': is_secure,
                   'expires': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                   'domain': domain,
                   'value': cookie['Content raw']
                  }
    return dict_cookie

def load_cookies(l_cookies):
    all_cookies = []

    for cookie_dict in l_cookies:
        all_cookies.append(create_cookie_dict(cookie_dict))
    return all_cookies

def get_cookies():
    l_cookies = []
    return l_cookies

if __name__ == "__main__":
    all_cookies = load_cookies(get_cookies())
    print(json.dumps(all_cookies))
