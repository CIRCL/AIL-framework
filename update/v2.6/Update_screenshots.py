#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
from lib import ConfigLoader

def get_domain(item_id):
    item_id = item_id.split('/')
    item_id = item_id[-1]
    return item_id[:-36]

def get_all_item(s_sha256):
    return r_serv_onion.smembers(f'screenshot:{s_sha256}')

def sanitize_domain(domain):
    faup.decode(domain)
    domain_sanitized = faup.get()
    domain_sanitized = domain_sanitized['domain']
    try:
        domain_sanitized = domain_sanitized.decode()
    except:
        pass
    return domain_sanitized.lower()

def update_db(s_sha256):
    screenshot_items = get_all_item(s_sha256)
    if screenshot_items:
        for item_id in screenshot_items:
            item_id = item_id.replace(PASTES_FOLDER+'/', '', 1)  # remove root path
            domain = get_domain(item_id)

            domain_sanitized = sanitize_domain(domain)
            if domain != domain_sanitized:
                r_serv_onion.sadd('incorrect_domain', domain)
                domain = domain_sanitized

            r_serv_onion.sadd('domain_screenshot:{}'.format(domain), s_sha256)
            r_serv_onion.sadd('screenshot_domain:{}'.format(s_sha256), domain)
    else:
        pass
        # broken screenshot
        r_serv_onion.sadd('broken_screenshot', s_sha256)


if __name__ == '__main__':

    start_deb = time.time()
    faup = Faup()

    config_loader = ConfigLoader.ConfigLoader()

    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes"))
    SCREENSHOT_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "crawled_screenshot"), 'screenshot')

    r_serv_db = config_loader.get_redis_conn("ARDB_DB")
    r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
    config_loader = None

    r_serv_db.set('ail:update_in_progress', 'v2.6')
    r_serv_db.set('ail:current_background_update', 'v2.6')

    r_serv_db.set('ail:current_background_script_stat', 20)
    r_serv_db.set('ail:current_background_script', 'screenshot update')

    nb = 0

    if os.path.isdir(SCREENSHOT_FOLDER):
        for root, dirs, files in os.walk(SCREENSHOT_FOLDER, topdown=False):
            # print(dirs)
            for name in files:
                nb = nb + 1
                screenshot_sha256 = os.path.join(root, name)
                screenshot_sha256 = screenshot_sha256[:-4]  # remove .png
                screenshot_sha256 = screenshot_sha256.replace(SCREENSHOT_FOLDER, '', 1)
                screenshot_sha256 = screenshot_sha256.replace('/', '')
                update_db(screenshot_sha256)
                # print('Screenshot updated: {}'.format(nb))
                if nb % 1000 == 0:
                    r_serv_db.set('ail:current_background_script', 'screenshot updated: {}'.format(nb))

    r_serv_db.set('ail:current_background_script_stat', 100)

    end = time.time()
    print('ALL screenshot updated: {} in {} s'.format(nb, end - start_deb))
