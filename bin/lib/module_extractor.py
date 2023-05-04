#!/usr/bin/env python3
# -*-coding:UTF-8 -*
import json
import os
import sys
import time

import yara

from operator import itemgetter

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import ail_objects
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

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None

r_key = regex_helper.generate_redis_cache_key('extractor')

# TODO UI Link

MODULES = {
    'infoleak:automatic-detection="credit-card"': CreditCards(queue=False),
    'infoleak:automatic-detection="iban"': Iban(queue=False),
    'infoleak:automatic-detection="mail"': Mail(queue=False),
    'infoleak:automatic-detection="onion"': Onion(queue=False),
    # APIkey ???
    # Credentials
    # Zerobins
    # CERTIFICATE + KEYS ???
    # SQL Injetction / Libinjection ???

}
tools = Tools(queue=False)
for tool_name in tools.get_tools():
    MODULES[f'infoleak:automatic-detection="{tool_name}-tool"'] = tools

def get_correl_match(extract_type, obj_id, content):
    extracted = []
    correl = correlations_engine.get_correlation_by_correl_type('item', '', obj_id, extract_type)
    to_extract = []
    map_subtype = {}
    for c in correl:
        subtype, value = c.split(':', 1)
        map_subtype[value] = subtype
        to_extract.append(value)
    if to_extract:
        objs = regex_helper.regex_finditer(r_key, '|'.join(to_extract), obj_id, content)
        for obj in objs:
            if map_subtype[obj[2]]:
                subtype = map_subtype[obj[2]]
            else:
                subtype = ''
            extracted.append([obj[0], obj[1], obj[2], f'{extract_type}:{subtype}:{obj[2]}'])
    return extracted

def _get_yara_match(data):
    for string_match in data.get('strings'):
        for string_match_instance in string_match.instances:
            start = string_match_instance.offset
            value = string_match_instance.matched_data.decode()
            end = start + string_match_instance.matched_length
            r_cache.sadd(f'extractor:yara:match:{r_key}', f'{start}:{end}:{value}')
            r_cache.expire(f'extractor:yara:match:{r_key}', 300)
    return yara.CALLBACK_CONTINUE

def _get_word_regex(word):
    return '(?:^|(?<=[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]))' + word + '(?:$|(?=[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]))'

def convert_byte_offset_to_string(b_content, offset):
    byte_chunk = b_content[:offset + 1]
    string_chunk = byte_chunk.decode()
    offset = len(string_chunk) - 1
    return offset


# TODO RETRO HUNTS
# TODO TRACKER TYPE IN UI
def get_tracker_match(obj_id, content):
    extracted = []
    extracted_yara = []
    trackers = Tracker.get_obj_trackers('item', '', obj_id)
    for tracker_uuid in trackers:
        tracker = Tracker.Tracker(tracker_uuid)
        tracker_type = tracker.get_type()
        # print(tracker_type)
        tracked = tracker.get_tracked()
        if tracker_type == 'regex':  # TODO Improve word detection -> word delimiter
            regex_match = regex_helper.regex_finditer(r_key, tracked, obj_id, content)
            for match in regex_match:
                extracted.append([int(match[0]), int(match[1]), match[2], f'tracker:{tracker.uuid}'])
        elif tracker_type == 'yara':
            rule = tracker.get_rule()
            rule.match(data=content.encode(), callback=_get_yara_match,
                       which_callbacks=yara.CALLBACK_MATCHES, timeout=30)
            yara_match = r_cache.smembers(f'extractor:yara:match:{r_key}')
            r_cache.delete(f'extractor:yara:match:{r_key}')
            extracted = []
            for match in yara_match:
                start, end, value = match.split(':', 2)
                extracted_yara.append([int(start), int(end), value, f'tracker:{tracker.uuid}'])

        elif tracker_type == 'word' or tracker_type == 'set':
            if tracker_type == 'set':
                tracked = tracked.rsplit(';', 1)[0]
                words = tracked.split(',')
            else:
                words = [tracked]
            for word in words:
                regex = _get_word_regex(word)
                regex_match = regex_helper.regex_finditer(r_key, regex, obj_id, content)
                # print(regex_match)
                for match in regex_match:
                    extracted.append([int(match[0]), int(match[1]), match[2], f'tracker:{tracker.uuid}'])

    # Convert byte offset to string offset
    if extracted_yara:
        b_content = content.encode()
        if len(b_content) == len(content):
            extracted[0:0] = extracted_yara
        else:
            for yara_m in extracted_yara:
                start = convert_byte_offset_to_string(b_content, yara_m[0])
                end = convert_byte_offset_to_string(b_content, yara_m[1])
                extracted.append([int(start), int(end), yara_m[2], yara_m[3]])

    return extracted

# Type:subtype:id
# tag:iban
# tracker:uuid

def extract(obj_id, content=None):
    item = Item(obj_id)
    if not item.exists():
        return []

    # CHECK CACHE
    cached = r_cache.get(f'extractor:cache:{obj_id}')
    if cached:
        r_cache.expire(f'extractor:cache:{obj_id}', 300)
        return json.loads(cached)

    if not content:
        content = item.get_content()

    extracted = get_tracker_match(obj_id, content)

    # print(item.get_tags())
    for tag in item.get_tags():
        if MODULES.get(tag):
            # print(tag)
            module = MODULES.get(tag)
            matches = module.extract(obj_id, content, tag)
            if matches:
                extracted = extracted + matches

    for obj_t in ['cve', 'cryptocurrency', 'username']:  # Decoded, PGP->extract bloc
        matches = get_correl_match(obj_t, obj_id, content)
        if matches:
            extracted = extracted + matches

    # SORT By Start Pos
    extracted = sorted(extracted, key=itemgetter(0))
    # print(extracted)

    # Save In Cache
    if extracted:
        extracted_dump = json.dumps(extracted)
        r_cache.set(f'extractor:cache:{obj_id}', extracted_dump)
        r_cache.expire(f'extractor:cache:{obj_id}', 300)  # TODO Reduce CACHE ???????????????

    return extracted

# TODO ADD LINK UI
def get_extracted_by_match(extracted):
    matches = {}
    for start, end, value, str_obj in extracted:

        if str_obj not in matches:
            matches[str_obj] = {}
            ob_type, row_id = str_obj.split(':', 1)
            if ob_type == 'tag':  # TODO put me in object class
                matches[str_obj]['subtype'] = 'tag'
                matches[str_obj]['id'] = row_id
                matches[str_obj]['icon'] = {'style': 'fas', 'icon': '\uf02b', 'color': '#28a745', 'radius': 5}
                matches[str_obj]['link'] = ''
            elif ob_type == 'tracker':  # TODO put me in object class
                matches[str_obj]['subtype'] = 'tracker'
                matches[str_obj]['id'] = row_id
                matches[str_obj]['icon'] = {'style': 'fas', 'icon': '\uf05b', 'color': '#ffc107', 'radius': 5}
                matches[str_obj]['link'] = ''
            else:
                row_id = row_id.split(':', 1)
                if len(row_id) == 2:
                    subtype = row_id[0]
                    obj_id = row_id[1]
                else:
                    subtype = ''
                    obj_id = row_id[0]
                matches[str_obj]['subtype'] = subtype
                matches[str_obj]['id'] = obj_id
                matches[str_obj]['icon'] = ail_objects.get_object_svg(ob_type, subtype, obj_id)
                matches[str_obj]['link'] = ail_objects.get_object_link(ob_type, subtype, obj_id)

            matches[str_obj]['matches'] = []

        match = [start, end, value]
        matches[str_obj]['matches'].append(match)
    return matches


# if __name__ == '__main__':
#     t0 = time.time()
#     obj_id = 'crawled/2022/09/15/circl.lu179c7903-5b21-452e-9f25-4b61d9934e2b'
#     obj_id = 'crawled/2022/09/15/circl.lu1e4f9721-06dc-404f-aabf-3c3bd0b533bd'
#     obj_id = 'submitted/2022/09/13/submitted_ba3ee771-c91c-4f50-9d6a-8558cdac7aeb.gz'
#     # obj_id = 'tests/2021/01/01/credit_cards.gz'
#     # obj_id = 'crawled/2020/07/20/circl.luc9301321-f1b1-4d91-9082-5eb452b946c5'
#     obj_id = 'submitted/2019/09/22/97172282-e4c2-4a1e-b82c-c4fb9490a56e.gz'
#     obj_id = 'submitted/2019/09/20/4fb7f02d-1241-4ef4-b17e-80ae76038835.gz'
#     obj_id = 'crawled/2023/02/21/circl.lu1c300acb-0cbe-480f-917e-9afe3ec958e8'
#
#     extract(obj_id)
#
#     # get_obj_correl('cve', obj_id, content)
#     # r = get_tracker_match(obj_id, content)
#     # print(r)
#
#     print(time.time() - t0)

