#!/usr/bin/env python3
# -*-coding:UTF-8 -*
import json
import logging
import os
import sys
import time

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

r_key = regex_helper.generate_redis_cache_key('extractor')  # TODO MOVE IN extractor function

EXTRACTION_MAX_SECONDS = 60
REGEX_MAX_SECONDS = 5


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


def deadline_exceeded(start_time, max_seconds=EXTRACTION_MAX_SECONDS):
    return (time.monotonic() - start_time) >= max_seconds


def _remaining_time(start_time, max_seconds=EXTRACTION_MAX_SECONDS):
    return max(0.0, max_seconds - (time.monotonic() - start_time))


def _regex_finditer_safe(regex, obj_gid, content, start_time, max_seconds=EXTRACTION_MAX_SECONDS,
                         regex_max_seconds=REGEX_MAX_SECONDS):
    if deadline_exceeded(start_time, max_seconds=max_seconds):
        return []
    remaining = _remaining_time(start_time, max_seconds=max_seconds)
    if remaining <= 0:
        return []
    timeout = min(regex_max_seconds, max(0.1, remaining))
    return regex_helper.regex_finditer(r_key, regex, obj_gid, content, max_time=timeout)


def get_correl_match(extract_type, obj, content, start_time=None, max_seconds=EXTRACTION_MAX_SECONDS):
    extracted = []
    if start_time and deadline_exceeded(start_time, max_seconds=max_seconds):
        return extracted
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
        objs = _regex_finditer_safe('|'.join(to_extract), obj.get_global_id(), content, start_time or time.monotonic(),
                                    max_seconds=max_seconds)
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
                # logger.critical(f'Error module extractor: {sha256_val}\n{extract_type}\n{subtype}\n{value_id}\n{map_value_id}\n{objs}')
                # print(f'Error module extractor: {sha256_val}\n{extract_type}\n{subtype}\n{value_id}\n{map_value_id}\n{objs}')
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
        # logger.error(f'Yara offset converter error, {str(e)}\n{offset}/{len(b_content)}')
        # print(f'Yara offset converter error, {str(e)}\n{offset}/{len(b_content)}')
        return convert_byte_offset_to_string(b_content, offset - 1)


def _get_trackers_match(trackers_uuids, user_org, user_id, obj_gid, content, priority=None, start_time=None,
                        max_seconds=EXTRACTION_MAX_SECONDS):
    extracted = []
    extracted_yara = []
    regex_cache = {}
    _start_time = start_time or time.monotonic()
    for tracker_uuid in trackers_uuids:
        if deadline_exceeded(_start_time, max_seconds=max_seconds):
            logger.warning('module_extractor: global extraction timeout reached while processing trackers')
            break
        tracker = Tracker.Tracker(tracker_uuid)
        if not tracker.check_level(user_org, user_id):
            continue

        tracker_type = tracker.get_type()
        # print(tracker_type)
        tracked = tracker.get_tracked()
        if tracker_type == 'regex':  # TODO Improve word detection -> word delimiter
            if tracked in regex_cache:
                regex_match = regex_cache[tracked]
            else:
                regex_match = _regex_finditer_safe(tracked, obj_gid, content, _start_time, max_seconds=max_seconds)
                regex_cache[tracked] = regex_match
            for match in regex_match:
                extracted.append([int(match[0]), int(match[1]), match[2], f'tracker:{tracker.uuid}'])
        elif tracker_type == 'yara':
            if deadline_exceeded(_start_time, max_seconds=max_seconds):
                break
            rule = tracker.get_rule()
            timeout = min(REGEX_MAX_SECONDS, max(0.1, _remaining_time(_start_time, max_seconds=max_seconds)))
            rule.match(data=content.encode(), callback=_get_yara_match,
                       which_callbacks=yara.CALLBACK_MATCHES, timeout=timeout)
            yara_match = r_cache.smembers(f'extractor:yara:match:{r_key}')  # set in _get_yara_match callback
            r_cache.delete(f'extractor:yara:match:{r_key}')
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
                if deadline_exceeded(_start_time, max_seconds=max_seconds):
                    break
                regex = _get_word_regex(word)
                if regex in regex_cache:
                    regex_match = regex_cache[regex]
                else:
                    regex_match = _regex_finditer_safe(regex, obj_gid, content, _start_time, max_seconds=max_seconds)
                    regex_cache[regex] = regex_match
                # print(regex_match)
                for match in regex_match:
                    extracted.append([int(match[0]), int(match[1]), match[2], f'tracker:{tracker.uuid}'])
        elif tracker_type == 'typosquatting':
            typo_domains = Tracker.get_tracked_typosquatting_domains(tracked)
            if typo_domains:
                escaped_domains = [regex_helper.regex_escape(typo_domain) for typo_domain in typo_domains]
                escaped_domains.sort(key=len, reverse=True)
                regex = _get_word_regex(f"(?:{'|'.join(escaped_domains)})")
                if regex in regex_cache:
                    regex_match = regex_cache[regex]
                else:
                    regex_match = _regex_finditer_safe(regex, obj_gid, content, _start_time, max_seconds=max_seconds)
                    regex_cache[regex] = regex_match
                for match in regex_match:
                    extracted.append([int(match[0]), int(match[1]), match[2], f'tracker:{tracker.uuid}'])
    return extracted, extracted_yara


def _extract_retro_hunts(retro_hunts_uuids, user_org, content, priority=None, start_time=None,
                         max_seconds=EXTRACTION_MAX_SECONDS):
    extracted_yara = []
    _start_time = start_time or time.monotonic()
    for retro_uuid in retro_hunts_uuids:
        if deadline_exceeded(_start_time, max_seconds=max_seconds):
            logger.warning('module_extractor: global extraction timeout reached while processing retro hunts')
            break
        retro_hunt = Tracker.RetroHunt(retro_uuid)
        if not retro_hunt.check_level(user_org):
            continue

        try:
            rule = retro_hunt.get_rule(r_compile=True)
        except yara.Error:
            retro_hunt.delete_objs()
            continue

        timeout = min(REGEX_MAX_SECONDS, max(0.1, _remaining_time(_start_time, max_seconds=max_seconds)))
        rule.match(data=content.encode(), callback=_get_yara_match,
                   which_callbacks=yara.CALLBACK_MATCHES, timeout=timeout)
        yara_match = r_cache.smembers(f'extractor:yara:match:{r_key}')  # set in _get_yara_match callback
        r_cache.delete(f'extractor:yara:match:{r_key}')
        for match in yara_match:
            start, end, value = match.split(':', 2)
            extracted_yara.append([int(start), int(end), value, f'retro_hunt:{retro_hunt.uuid}'])
    return extracted_yara


# TODO TRACKER TYPE IN UI
def get_tracker_match(user_org, user_id, obj, content, priority=None, match_uuid=None, start_time=None,
                      max_seconds=EXTRACTION_MAX_SECONDS):
    start_time = start_time or time.monotonic()
    obj_gid = obj.get_global_id()

    if match_uuid:
        extracted = []
        if Tracker.is_tracker(match_uuid):
            extracted, extracted_yara = _get_trackers_match([match_uuid], user_org, user_id, obj_gid, content,
                                                            start_time=start_time, max_seconds=max_seconds)
        # retro_hunt
        else:
            extracted_yara = _extract_retro_hunts([match_uuid], user_org, content, start_time=start_time,
                                                  max_seconds=max_seconds)

    else:
        trackers_uuids = Tracker.get_obj_trackers(obj.type, obj.get_subtype(r_str=True), obj.id)
        retro_hunts_uuids = Tracker.get_obj_retro_hunts(obj_gid)

        # check if priority is tracker or retro
        if priority:
            if priority in trackers_uuids:
                extracted, extracted_yara = _get_trackers_match(trackers_uuids, user_org, user_id, obj_gid, content,
                                                                priority=priority, start_time=start_time,
                                                                max_seconds=max_seconds)
                extracted_retro_yara = _extract_retro_hunts(retro_hunts_uuids, user_org, content, priority=priority,
                                                            start_time=start_time, max_seconds=max_seconds)
            else:
                extracted_retro_yara = _extract_retro_hunts(retro_hunts_uuids, user_org, content, priority=priority,
                                                            start_time=start_time, max_seconds=max_seconds)
                extracted, extracted_yara = _get_trackers_match(trackers_uuids, user_org, user_id, obj_gid, content,
                                                                start_time=start_time, max_seconds=max_seconds)
        else:
            extracted, extracted_yara = _get_trackers_match(trackers_uuids, user_org, user_id, obj_gid, content,
                                                            start_time=start_time, max_seconds=max_seconds)
            extracted_retro_yara = _extract_retro_hunts(retro_hunts_uuids, user_org, content, start_time=start_time,
                                                        max_seconds=max_seconds)
        if extracted_yara and extracted_retro_yara:
            extracted_yara[0:0] = extracted_retro_yara
        elif extracted_retro_yara:
            extracted_yara = extracted_retro_yara

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
def extract(user_id, obj_type, subtype, obj_id, content=None, priority=None, match_uuid=None):
    start_time = time.monotonic()
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
        extracted = []
        if not deadline_exceeded(start_time):
            extracted = get_tracker_match(user_org, user_id, obj, content, match_uuid=match_uuid,
                                          start_time=start_time)
        else:
            logger.warning(f'module_extractor: global extraction timeout reached before tracker extraction for {obj_gid}')
        if not match_uuid:
            # print(item.get_tags())
            for tag in obj.get_tags():
                if deadline_exceeded(start_time):
                    logger.warning(f'module_extractor: global extraction timeout reached while processing modules for {obj_gid}')
                    break
                if MODULES.get(tag):
                    # print(tag)
                    module = MODULES.get(tag)
                    matches = module.extract(obj, content, tag)
                    if matches:
                        extracted = extracted + matches

            for obj_t in CORRELATION_TO_EXTRACT[obj.type]:
                if deadline_exceeded(start_time):
                    logger.warning(f'module_extractor: global extraction timeout reached while processing correlations for {obj_gid}')
                    break
                matches = get_correl_match(obj_t, obj, content, start_time=start_time)
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
                    tracker = Tracker.Tracker(row_id)
                    tracked = tracker.get_tracked()
                    if tracked:
                        matches[str_obj]['name'] = tracked
                    description = tracker.get_description()
                    if description:
                        matches[str_obj]['description'] = description
                elif ob_type == 'retro_hunt':  # TODO put me in object class
                    matches[str_obj]['subtype'] = 'retro_hunt'
                    matches[str_obj]['id'] = row_id
                    matches[str_obj]['icon'] = {'style': 'fas', 'icon': '\uf05b', 'color': '#008107', 'radius': 5}
                    matches[str_obj]['link'] = ''
                    retro_hunt = Tracker.RetroHunt(row_id)
                    name = retro_hunt.get_name()
                    if name:
                        matches[str_obj]['name'] = name
                    description = retro_hunt.get_description()
                    if description:
                        matches[str_obj]['description'] = description
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
                        # logger.critical(f'module extractor invalid object: {ob_type} : {subtype} : {obj_id}')
                        # print(f'module extractor invalid object: {ob_type} : {subtype} : {obj_id}')
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
