#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

import yara

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
import lib.objects.ail_objects
from lib.objects.Items import Item
from lib import correlations_engine
from lib import regex_helper
from lib.ConfigLoader import ConfigLoader

from lib import Tracker

from modules.CreditCards import CreditCards
from modules.Iban import Iban
from modules.Mail import Mail
from modules.Onion import Onion
from modules.Tools import Tools

creditCards = CreditCards()
ibans = Iban()
mails = Mail()
onions = Onion()
tools = Tools()

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None

r_key = regex_helper.generate_redis_cache_key('extractor')

MODULES = {
    'infoleak:automatic-detection="credit-card"': creditCards,
    'infoleak:automatic-detection="iban"': ibans,
    'infoleak:automatic-detection="mail"': mails,
    'infoleak:automatic-detection="onion"': onions,
    # APIkey ???
    # Credentials
    # Zerobins
    # CERTIFICATE + KEYS ???
    # SQL Injetction / Libinjection ???

}
for tool_name in tools.get_tools():
    MODULES[f'infoleak:automatic-detection="{tool_name}-tool"'] = tools

def get_correl_match(extract_type, obj_id, content, filter_subtypes=['']):
    correl = correlations_engine.get_correlation_by_correl_type('item', '', obj_id, extract_type)
    to_extract = []
    for c in correl:
        subtype, value = c.split(':', 1)
        # if subtype in filter_subtypes:
        to_extract.append(value)
    if to_extract:
        return regex_helper.regex_finditer(r_key, '|'.join(to_extract), obj_id, content)
    else:
        return []

def _get_yara_match(data):
    for row in data.get('strings'):
        start, i, value = row
        value = value.decode()
        end = start + len(value)
        r_cache.sadd(f'extractor:yara:match:{r_key}', f'{start}:{end}:{value}')
        r_cache.expire(f'extractor:yara:match:{r_key}', 300)
    return yara.CALLBACK_CONTINUE

# TODO RETRO HUNTS
def get_tracker_match(obj_id, content):
    trackers = Tracker.get_obj_all_trackers('item', '', obj_id)
    for tracker_uuid in trackers:
        tracker_type = Tracker.get_tracker_type(tracker_uuid)
        tracker = Tracker.get_tracker_by_uuid(tracker_uuid)
        if tracker_type == 'regex':
            return regex_helper.regex_finditer(r_key, tracker, obj_id, content)
        elif tracker_type == 'yara':
            rule = Tracker.get_yara_rule_by_uuid(tracker_uuid)
            rule.match(data=content, callback=_get_yara_match,
                       which_callbacks=yara.CALLBACK_MATCHES, timeout=30)
            yara_match = r_cache.smembers(f'extractor:yara:match:{r_key}')
            r_cache.delete(f'extractor:yara:match:{r_key}')
            extracted = []
            for match in yara_match:
                start, end, value = match.split(':', 2)
                extracted.append((int(start), int(end), value))
            return extracted

        # elif tracker_type == 'term': # TODO
        #
        # elif tracker_type == '':
    return []


def extract(obj_id, content=None):
    item = Item(obj_id)
    if not content:
        content = item.get_content()
    extracted = []

    extracted = extracted + get_tracker_match(obj_id, content)

    # print(item.get_tags())
    for tag in item.get_tags():
        if MODULES.get(tag):
            # print(tag)
            module = MODULES.get(tag)
            matches = module.extract(obj_id, content, tag)
            if matches:
                extracted = extracted + matches

    for obj_t in ['cve', 'cryptocurrency', 'username']: # Decoded, PGP->extract bloc
        matches = get_correl_match(obj_t, obj_id, content)
        if matches:
            extracted = extracted + matches

    from operator import itemgetter

    extracted = sorted(extracted, key=itemgetter(0))
    print(extracted)
    return extracted


if __name__ == '__main__':
    t0 = time.time()
    obj_id = 'crawled/2022/09/15/circl.lu179c7903-5b21-452e-9f25-4b61d9934e2b'
    obj_id = 'crawled/2022/09/15/circl.lu1e4f9721-06dc-404f-aabf-3c3bd0b533bd'
    obj_id = 'submitted/2022/09/13/submitted_ba3ee771-c91c-4f50-9d6a-8558cdac7aeb.gz'
    # obj_id = 'tests/2021/01/01/credit_cards.gz'
    # obj_id = 'crawled/2020/07/20/circl.luc9301321-f1b1-4d91-9082-5eb452b946c5'
    obj_id = 'submitted/2019/09/22/97172282-e4c2-4a1e-b82c-c4fb9490a56e.gz'
    obj_id = 'submitted/2019/09/20/4fb7f02d-1241-4ef4-b17e-80ae76038835.gz'

    extract(obj_id)

    # get_obj_correl('cve', obj_id, content)
    # r = get_tracker_match(obj_id, content)
    # print(r)

    print(time.time() - t0)

