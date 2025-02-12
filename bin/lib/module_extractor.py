#!/usr/bin/env python3
# -*-coding:UTF-8 -*
import json
import logging
import os
import sys

import yara

from hashlib import sha256
from operator import itemgetter

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ail_users import get_user_org
from lib.objects import ail_objects
from lib.objects.Titles import Title
from lib.exceptions import TimeoutException
from lib import correlations_engine
from lib import regex_helper
from lib.ConfigLoader import ConfigLoader

from lib import Tracker

from modules.CreditCards import CreditCards
from modules.Iban import Iban
from modules.Mail import Mail
from modules.Onion import Onion
from modules.Phone import Phone
from modules.Tools import Tools

logger = logging.getLogger()

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None

r_key = regex_helper.generate_redis_cache_key('extractor')


# SIGNAL ALARM
# import signal
# def timeout_handler(signum, frame):
#     raise TimeoutException
#
#
# signal.signal(signal.SIGALRM, timeout_handler)

# TODO UI Link

CORRELATION_TO_EXTRACT = {
    'item': ['cve', 'cryptocurrency', 'title', 'username'],
    'message': ['cve', 'cryptocurrency', 'username']
}

MODULES = {
    'infoleak:automatic-detection="credit-card"': CreditCards(queue=False),
    'infoleak:automatic-detection="iban"': Iban(queue=False),
    'infoleak:automatic-detection="mail"': Mail(queue=False),
    'infoleak:automatic-detection="onion"': Onion(queue=False),
    'infoleak:automatic-detection="phone-number"': Phone(queue=False),
    # APIkey ???
    # Credentials
    # Zerobins
    # CERTIFICATE + KEYS ???
    # SQL Injetction / Libinjection ???

}
tools = Tools(queue=False)
for tool_name in tools.get_tools():
    MODULES[f'infoleak:automatic-detection="{tool_name}-tool"'] = tools

def merge_overlap(extracted):
    merged = []
    curr_start, curr_end, curr_string_match, curr_obj_ref = extracted[0]
    curr_obj_ref = [(curr_obj_ref, curr_string_match)]

    for start, end, mstring, ref in extracted[1:]:
        # overlap
        if start <= curr_end:
            curr_string_match += mstring[curr_end - start:]
            curr_end = max(curr_end, end)
            curr_obj_ref.append((ref, mstring))
        else:
            merged.append((curr_start, curr_end, curr_string_match, curr_obj_ref))
            curr_start, curr_end, curr_string_match, curr_obj_ref = start, end, mstring, [(ref, mstring)]

    merged.append((curr_start, curr_end, curr_string_match, curr_obj_ref))
    return merged

def get_correl_match(extract_type, obj, content):
    extracted = []
    correl = correlations_engine.get_correlation_by_correl_type(obj.type, obj.get_subtype(r_str=True), obj.id, extract_type)
    to_extract = []
    map_subtype = {}
    map_value_id = {}
    for c in correl:
        subtype, value = c.split(':', 1)
        if extract_type == 'title':
            title = Title(value).get_content()
            to_extract.append(title)
            sha256_val = sha256(title.encode()).hexdigest()
        else:
            map_subtype[value] = subtype
            to_extract.append(value)
            sha256_val = sha256(value.encode()).hexdigest()
        map_value_id[sha256_val] = value
    if to_extract:
        objs = regex_helper.regex_finditer(r_key, '|'.join(to_extract), obj.get_global_id(), content, max_time=5)
        if extract_type == 'title' and objs:
            objs = [objs[0]]
        for ob in objs:
            if map_subtype.get(ob[2]):
                subtype = map_subtype[ob[2]]
                sha256_val = ob[2]
            else:
                subtype = ''
                sha256_val = sha256(ob[2].encode()).hexdigest()
            value_id = map_value_id.get(sha256_val)
            if not value_id:
                logger.critical(f'Error module extractor: {sha256_val}\n{extract_type}\n{subtype}\n{value_id}\n{map_value_id}\n{objs}')
                value_id = 'ERROR'
            extracted.append([ob[0], ob[1], ob[2], f'{extract_type}:{subtype}:{value_id}'])
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
    return '(?i)(?:^|(?<=[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]))' + word + '(?:$|(?=[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]))'

def convert_byte_offset_to_string(b_content, offset):
    byte_chunk = b_content[:offset + 1]
    try:
        string_chunk = byte_chunk.decode()
        offset = len(string_chunk) - 1
        return offset
    except UnicodeDecodeError as e:
        logger.error(f'Yara offset converter error, {str(e)}\n{offset}/{len(b_content)}')
        return convert_byte_offset_to_string(b_content, offset - 1)


# TODO RETRO HUNTS
# TODO TRACKER TYPE IN UI
def get_tracker_match(user_org, user_id, obj, content):
    extracted = []
    extracted_yara = []
    obj_gid = obj.get_global_id()
    trackers = Tracker.get_obj_trackers(obj.type, obj.get_subtype(r_str=True), obj.id)
    for tracker_uuid in trackers:
        tracker = Tracker.Tracker(tracker_uuid)
        if not tracker.check_level(user_org, user_id):
            continue

        tracker_type = tracker.get_type()
        # print(tracker_type)
        tracked = tracker.get_tracked()
        if tracker_type == 'regex':  # TODO Improve word detection -> word delimiter
            regex_match = regex_helper.regex_finditer(r_key, tracked, obj_gid, content, max_time=5)
            for match in regex_match:
                extracted.append([int(match[0]), int(match[1]), match[2], f'tracker:{tracker.uuid}'])
        elif tracker_type == 'yara':
            rule = tracker.get_rule()
            rule.match(data=content.encode(), callback=_get_yara_match,
                       which_callbacks=yara.CALLBACK_MATCHES, timeout=5)
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
                regex_match = regex_helper.regex_finditer(r_key, regex, obj_gid, content, max_time=5)
                # print(regex_match)
                for match in regex_match:
                    extracted.append([int(match[0]), int(match[1]), match[2], f'tracker:{tracker.uuid}'])

    # Retro Hunt
    retro_hunts = Tracker.get_obj_retro_hunts(obj.type, obj.get_subtype(r_str=True), obj.id)
    for retro_uuid in retro_hunts:
        retro_hunt = Tracker.RetroHunt(retro_uuid)
        if not retro_hunt.check_level(user_org):
            continue

        try:
            rule = retro_hunt.get_rule(r_compile=True)
        except yara.Error:
            retro_hunt.delete_objs()
            continue

        rule.match(data=content.encode(), callback=_get_yara_match,
                   which_callbacks=yara.CALLBACK_MATCHES, timeout=5)
        yara_match = r_cache.smembers(f'extractor:yara:match:{r_key}')
        r_cache.delete(f'extractor:yara:match:{r_key}')
        extracted = []
        for match in yara_match:
            start, end, value = match.split(':', 2)
            extracted_yara.append([int(start), int(end), value, f'retro_hunt:{retro_hunt.uuid}'])

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
# def extract(obj_id, content=None):
def extract(user_id, obj_type, subtype, obj_id, content=None):
    obj = ail_objects.get_object(obj_type, subtype, obj_id)
    if not obj.exists():
        return []
    obj_gid = obj.get_global_id()

    user_org = get_user_org(user_id)

    # CHECK CACHE
    cached = r_cache.get(f'extractor:cache:{obj_gid}:{user_org}:{user_id}')
    # cached = None
    if cached:
        r_cache.expire(f'extractor:cache:{obj_gid}:{user_org}:{user_id}', 300)
        return json.loads(cached)

    # signal.alarm(60)
    try:
        if not content:
            content = obj.get_content()
        extracted = get_tracker_match(user_org, user_id, obj, content)
        # print(item.get_tags())
        for tag in obj.get_tags():
            if MODULES.get(tag):
                # print(tag)
                module = MODULES.get(tag)
                matches = module.extract(obj, content, tag)
                if matches:
                    extracted = extracted + matches

        for obj_t in CORRELATION_TO_EXTRACT[obj.type]:
            matches = get_correl_match(obj_t, obj, content)
            if matches:
                extracted = extracted + matches

        # SORT By Start Pos
        if extracted:
            extracted = sorted(extracted, key=itemgetter(0))
            extracted = merge_overlap(extracted)

        # Save In Cache
        if extracted:
            extracted_dump = json.dumps(extracted)
            r_cache.set(f'extractor:cache:{obj_gid}:{user_org}:{user_id}', extracted_dump)
            r_cache.expire(f'extractor:cache:{obj_gid}:{user_org}:{user_id}', 300)  # TODO Reduce CACHE ???????????????
    except TimeoutException:
        extracted = []
    # finally:
    #     signal.alarm(0)

    return extracted

# TODO ADD LINK UI
def get_extracted_by_match(extracted):
    matches = {}
    for start, end, value, raw_objs in extracted:

        for raw in raw_objs:
            str_obj, str_match = raw

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
                elif ob_type == 'retro_hunt':  # TODO put me in object class
                    matches[str_obj]['subtype'] = 'retro_hunt'
                    matches[str_obj]['id'] = row_id
                    matches[str_obj]['icon'] = {'style': 'fas', 'icon': '\uf05b', 'color': '#008107', 'radius': 5}
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
                    try:
                        matches[str_obj]['icon'] = ail_objects.get_object_svg(ob_type, subtype, obj_id)
                        matches[str_obj]['link'] = ail_objects.get_object_link(ob_type, subtype, obj_id)
                    except TypeError:
                        logger.critical(f'module extractor invalid object: {ob_type} : {subtype} : {obj_id}')
                        matches[str_obj]['icon'] = {'style': 'fas', 'icon': '\uf00d', 'color': 'red', 'radius': 5}
                        matches[str_obj]['link'] = ''

                matches[str_obj]['matches'] = []

            match = [start, end, str_match]
            matches[str_obj]['matches'].append(match)
    return matches


# if __name__ == '__main__':
#     t0 = time.time()
#     obj_id = 'crawled/2023/02/21/circl.lu1c300acb-0cbe-480f-917e-9afe3ec958e8'
#     extract(obj_id)
#
#     # get_obj_correl('cve', obj_id, content)
#     # r = get_tracker_match(obj_id, content)
#     # print(r)
#
#     print(time.time() - t0)

