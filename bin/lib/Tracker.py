#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import time
import redis
import uuid
import yara
import datetime

from flask import escape

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Date

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import item_basic

config_loader = ConfigLoader.ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")

r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_serv_tracker = config_loader.get_redis_conn("ARDB_Tracker")
config_loader = None

email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}'
email_regex = re.compile(email_regex)

special_characters = set('[<>~!?@#$%^&*|()_-+={}":;,.\'\n\r\t]/\\')
special_characters.add('\\s')

###############
#### UTILS ####
def is_valid_uuid_v4(UUID):
    if not UUID:
        return False
    UUID = UUID.replace('-', '')
    try:
        uuid_test = uuid.UUID(hex=UUID, version=4)
        return uuid_test.hex == UUID
    except:
        return False

def is_valid_regex(tracker_regex):
    try:
        re.compile(tracker_regex)
        return True
    except:
        return False

def is_valid_mail(email):
    result = email_regex.match(email)
    if result:
        return True
    else:
        return False

def verify_mail_list(mail_list):
    for mail in mail_list:
        if not is_valid_mail(mail):
            return ({'status': 'error', 'reason': 'Invalid email', 'value': mail}, 400)
    return None

##-- UTILS --##
###############

def get_tracker_by_uuid(tracker_uuid):
    return r_serv_tracker.hget('tracker:{}'.format(tracker_uuid), 'tracked')

def get_tracker_type(tracker_uuid):
    return r_serv_tracker.hget('tracker:{}'.format(tracker_uuid), 'type')

def get_tracker_level(tracker_uuid):
    return int(r_serv_tracker.hget('tracker:{}'.format(tracker_uuid), 'level'))

def get_tracker_user_id(tracker_uuid):
    return r_serv_tracker.hget('tracker:{}'.format(tracker_uuid), 'user_id')

def get_tracker_uuid_list(tracker, tracker_type):  ######################################################### USE ME
    return list(r_serv_tracker.smembers('all:tracker_uuid:{}:{}'.format(tracker_type, tracker)))

def get_tracker_tags(tracker_uuid):
    return list(r_serv_tracker.smembers('tracker:tags:{}'.format(tracker_uuid)))

def get_tracker_mails(tracker_uuid):
    return list(r_serv_tracker.smembers('tracker:mail:{}'.format(tracker_uuid)))

def get_tracker_uuid_sources(tracker_uuid):
    return list(r_serv_tracker.smembers(f'tracker:sources:{tracker_uuid}'))

def get_tracker_description(tracker_uuid):
    return r_serv_tracker.hget('tracker:{}'.format(tracker_uuid), 'description')

def get_tracker_first_seen(tracker_uuid):
    res = r_serv_tracker.zrange('tracker:stat:{}'.format(tracker_uuid), 0, 0)
    if res:
        return res[0]
    else:
        return None

def get_tracker_last_seen(tracker_uuid):
    res = r_serv_tracker.zrevrange('tracker:stat:{}'.format(tracker_uuid), 0, 0)
    if res:
        return res[0]
    else:
        return None

def get_tracker_metedata(tracker_uuid, user_id=False, description=False, level=False, tags=False, mails=False, sources=True, sparkline=False):
    dict_uuid = {}
    dict_uuid['tracker'] = get_tracker_by_uuid(tracker_uuid)
    dict_uuid['type'] = get_tracker_type(tracker_uuid)
    dict_uuid['date'] = r_serv_tracker.hget('tracker:{}'.format(tracker_uuid), 'date')
    dict_uuid['description'] = get_tracker_description(tracker_uuid)
    dict_uuid['first_seen'] = get_tracker_first_seen(tracker_uuid)
    dict_uuid['last_seen'] = get_tracker_last_seen(tracker_uuid)
    if user_id:
        dict_uuid['user_id'] = get_tracker_user_id(tracker_uuid)
    if level:
        dict_uuid['level'] = get_tracker_level(tracker_uuid)
    if mails:
        dict_uuid['mails'] = get_tracker_mails(tracker_uuid)
    if sources:
        dict_uuid['sources'] = get_tracker_uuid_sources(tracker_uuid)
    if tags:
        dict_uuid['tags'] = get_tracker_tags(tracker_uuid)
    if sparkline:
        dict_uuid['sparkline'] = get_tracker_sparkline(tracker_uuid)
    dict_uuid['uuid'] = tracker_uuid
    return dict_uuid

################################################################################
################################################################################
################################################################################
# # TODO: FIXME
def get_tracker_sparkline(tracker_uuid, num_day=6):
    date_range_sparkline = Date.get_date_range(num_day)
    sparklines_value = []
    for date_day in date_range_sparkline:
        nb_seen_this_day = r_serv_tracker.scard('tracker:item:{}:{}'.format(tracker_uuid, date_day))
        if nb_seen_this_day is None:
            nb_seen_this_day = 0
        sparklines_value.append(int(nb_seen_this_day))
    return sparklines_value

def get_tracker_items_by_daterange(tracker_uuid, date_from, date_to):
    all_item_id = set()
    if date_from and date_to:
        l_date_match = r_serv_tracker.zrange(f'tracker:stat:{tracker_uuid}', 0, -1, withscores=True)
        if l_date_match:
            dict_date_match = dict(l_date_match)
            for date_day in Date.substract_date(date_from, date_to):
                if date_day in dict_date_match:
                    all_item_id |= r_serv_tracker.smembers(f'tracker:item:{tracker_uuid}:{date_day}')
    return all_item_id

def add_tracked_item(tracker_uuid, item_id):
    item_date = item_basic.get_item_date(item_id)
    # track item
    # r_serv_tracker.sadd(f'obj:trackers:item:{item_id}', tracker_uuid)
    res = r_serv_tracker.sadd(f'tracker:item:{tracker_uuid}:{item_date}', item_id)
    # track nb item by date
    if res == 1:
        r_serv_tracker.zincrby('tracker:stat:{}'.format(tracker_uuid), int(item_date), 1)

def remove_tracked_item(item_id):
    item_date = item_basic.get_item_date(item_id)
    for tracker_uuid in get_item_all_trackers_uuid(item_id):
        r_serv_tracker.srem(f'obj:trackers:item:{item_id}', tracker_uuid)
        res = r_serv_tracker.srem(f'tracker:item:{tracker_uuid}:{item_date}', item_id)
        if res:
            r_serv_tracker.zincrby('tracker:stat:{}'.format(tracker_uuid), int(item_date), -1)

def get_item_all_trackers_uuid(obj_id):
    #obj_type = 'item'
    return r_serv_tracker.smembers(f'obj:trackers:item:{obj_id}')


def get_email_subject(tracker_uuid):
    tracker_description = get_tracker_description(tracker_uuid)
    if not tracker_description:
        return "AIL framework: Tracker Alert"
    else:
        return 'AIL framework: {}'.format(tracker_description)

def get_tracker_last_updated_by_type(tracker_type):
    epoch_update = r_serv_tracker.get('tracker:refresh:{}'.format(tracker_type))
    if not epoch_update:
        epoch_update = 0
    return float(epoch_update)

# # TODO: check type API
def trigger_trackers_refresh(tracker_type):
    r_serv_tracker.set(f'tracker:refresh:{tracker_type}', time.time())

######################
#### TRACKERS ACL ####

# # TODO: use new package => duplicate fct
def is_in_role(user_id, role):
    if r_serv_db.sismember('user_role:{}'.format(role), user_id):
        return True
    else:
        return False

def is_tracker_in_global_level(tracker, tracker_type):
    res = r_serv_tracker.smembers('all:tracker_uuid:{}:{}'.format(tracker_type, tracker))
    if res:
        for elem_uuid in res:
            if r_serv_tracker.hget('tracker:{}'.format(elem_uuid), 'level')=='1':
                return True
    return False

def is_tracker_in_user_level(tracker, tracker_type, user_id):
    res = r_serv_tracker.smembers('user:tracker:{}'.format(user_id))
    if res:
        for elem_uuid in res:
            if r_serv_tracker.hget('tracker:{}'.format(elem_uuid), 'tracked')== tracker:
                if r_serv_tracker.hget('tracker:{}'.format(elem_uuid), 'type')== tracker_type:
                    return True
    return False

def api_is_allowed_to_edit_tracker(tracker_uuid, user_id):
    if not is_valid_uuid_v4(tracker_uuid):
        return ({"status": "error", "reason": "Invalid uuid"}, 400)
    tracker_creator = r_serv_tracker.hget('tracker:{}'.format(tracker_uuid), 'user_id')
    if not tracker_creator:
        return ({"status": "error", "reason": "Unknown uuid"}, 404)
    if not is_in_role(user_id, 'admin') and user_id != tracker_creator:
        return ({"status": "error", "reason": "Access Denied"}, 403)
    return ({"uuid": tracker_uuid}, 200)


##-- ACL --##

#### FIX DB ####
def fix_tracker_stats_per_day(tracker_uuid):
    date_from = get_tracker_first_seen(tracker_uuid)
    date_to = get_tracker_last_seen(tracker_uuid)
    # delete stats
    r_serv_tracker.delete(f'tracker:stat:{tracker_uuid}')
    # create new stats
    for date_day in Date.substract_date(date_from, date_to):
        pass

##-- FIX DB --##

#### CREATE TRACKER ####
def api_validate_tracker_to_add(tracker , tracker_type, nb_words=1):
    if tracker_type=='regex':
        if not is_valid_regex(tracker):
            return ({"status": "error", "reason": "Invalid regex"}, 400)
    elif tracker_type=='word' or tracker_type=='set':
        # force lowercase
        tracker = tracker.lower()
        word_set = set(tracker)
        set_inter = word_set.intersection(special_characters)
        if set_inter:
            return ({"status": "error", "reason": f'special character(s) not allowed: {set_inter}', "message": "Please use a python regex or remove all special characters"}, 400)
        words = tracker.split()
        # not a word
        if tracker_type=='word' and len(words)>1:
            tracker_type = 'set'

        # ouput format: tracker1,tracker2,tracker3;2
        if tracker_type=='set':
            try:
                nb_words = int(nb_words)
            except:
                nb_words = 1
            if nb_words==0:
                nb_words = 1

            words_set = set(words)
            words_set = sorted(words_set)

            if nb_words > len(words_set):
                nb_words = len(words_set)

            tracker = ",".join(words_set)
            tracker = "{};{}".format(tracker, nb_words)

    elif tracker_type=='yara_custom':
        if not is_valid_yara_rule(tracker):
            return ({"status": "error", "reason": "Invalid custom Yara Rule"}, 400)
    elif tracker_type=='yara_default':
        if not is_valid_default_yara_rule(tracker):
            return ({"status": "error", "reason": "The Yara Rule doesn't exist"}, 400)
    else:
        return ({"status": "error", "reason": "Incorrect type"}, 400)
    return ({"status": "success", "tracker": tracker, "type": tracker_type}, 200)

def create_tracker(tracker, tracker_type, user_id, level, tags, mails, description, dashboard=0, tracker_uuid=None, sources=[]):
    # edit tracker
    if tracker_uuid:
        edit_tracker = True
        # check if type changed
        old_type = get_tracker_type(tracker_uuid)
        old_tracker = get_tracker_by_uuid(tracker_uuid)
        old_level = get_tracker_level(tracker_uuid)
        tracker_user_id = get_tracker_user_id(tracker_uuid)

    # Create new tracker
    else:
        edit_tracker = False
        # generate tracker uuid
        tracker_uuid = str(uuid.uuid4())
        old_type = None
        old_tracker = None

    # YARA
    if tracker_type == 'yara_custom' or tracker_type == 'yara_default':
        # create yara rule
        if tracker_type == 'yara_default' and old_type == 'yara':
            if not is_default_yara_rule(old_tracker):
                filepath = get_yara_rule_file_by_tracker_name(old_tracker)
                if filepath:
                    os.remove(filepath)
        tracker = save_yara_rule(tracker_type, tracker, tracker_uuid=tracker_uuid)
        tracker_type = 'yara'

    # create metadata
    r_serv_tracker.hset('tracker:{}'.format(tracker_uuid), 'tracked', tracker)
    r_serv_tracker.hset('tracker:{}'.format(tracker_uuid), 'type', tracker_type)
    r_serv_tracker.hset('tracker:{}'.format(tracker_uuid), 'date', datetime.date.today().strftime("%Y%m%d"))
    r_serv_tracker.hset('tracker:{}'.format(tracker_uuid), 'level', level)
    r_serv_tracker.hset('tracker:{}'.format(tracker_uuid), 'dashboard', dashboard)
    if not edit_tracker:
        r_serv_tracker.hset('tracker:{}'.format(tracker_uuid), 'user_id', user_id)

    if description:
        r_serv_tracker.hset('tracker:{}'.format(tracker_uuid), 'description', description)

    # type change
    if edit_tracker:
        r_serv_tracker.srem('all:tracker:{}'.format(old_type), old_tracker)
        r_serv_tracker.srem('all:tracker_uuid:{}:{}'.format(old_type, old_tracker), tracker_uuid)
        if level != old_level:
            if level == 0:
                r_serv_tracker.srem('global:tracker', tracker_uuid)
            elif level == 1:
                r_serv_tracker.srem('user:tracker:{}'.format(tracker_user_id), tracker_uuid)
        if tracker_type != old_type:
            if old_level == 0:
                r_serv_tracker.srem('user:tracker:{}:{}'.format(tracker_user_id, old_type), tracker_uuid)
            elif old_level == 1:
                r_serv_tracker.srem('global:tracker:{}'.format(old_type), tracker_uuid)
            if old_type=='yara':
                if not is_default_yara_rule(old_tracker):
                    filepath = get_yara_rule_file_by_tracker_name(old_tracker)
                    if filepath:
                        os.remove(filepath)

    # create all tracker set
    r_serv_tracker.sadd('all:tracker:{}'.format(tracker_type), tracker)

    # create tracker - uuid map
    r_serv_tracker.sadd('all:tracker_uuid:{}:{}'.format(tracker_type, tracker), tracker_uuid)

    # add display level set
    if level == 0: # user only
        r_serv_tracker.sadd('user:tracker:{}'.format(user_id), tracker_uuid)
        r_serv_tracker.sadd('user:tracker:{}:{}'.format(user_id, tracker_type), tracker_uuid)
    elif level == 1: # global
        r_serv_tracker.sadd('global:tracker', tracker_uuid)
        r_serv_tracker.sadd('global:tracker:{}'.format(tracker_type), tracker_uuid)

    if edit_tracker:
        r_serv_tracker.delete(f'tracker:tags:{tracker_uuid}')
        r_serv_tracker.delete(f'tracker:mail:{tracker_uuid}')
        r_serv_tracker.delete(f'tracker:sources:{tracker_uuid}')

    # create tracker tags list
    for tag in tags:
        r_serv_tracker.sadd(f'tracker:tags:{tracker_uuid}', escape(tag))

    # create tracker tags mail notification list
    for mail in mails:
        r_serv_tracker.sadd(f'tracker:mail:{tracker_uuid}', escape(mail))

    # create tracker sources filter
    for source in sources:
        # escape source ?
        r_serv_tracker.sadd(f'tracker:sources:{tracker_uuid}', escape(source))

    # toggle refresh module tracker list/set
    r_serv_tracker.set('tracker:refresh:{}'.format(tracker_type), time.time())
    if tracker_type != old_type: # toggle old type refresh
        r_serv_tracker.set('tracker:refresh:{}'.format(old_type), time.time())
    return tracker_uuid

def api_add_tracker(dict_input, user_id):
    tracker = dict_input.get('tracker', None)
    if not tracker:
        return ({"status": "error", "reason": "Tracker not provided"}, 400)
    tracker_type = dict_input.get('type', None)
    if not tracker_type:
        return ({"status": "error", "reason": "Tracker type not provided"}, 400)
    nb_words = dict_input.get('nb_words', 1)
    description = dict_input.get('description', '')
    description = escape(description)

    res = api_validate_tracker_to_add(tracker , tracker_type, nb_words=nb_words)
    if res[1]!=200:
        return res
    tracker = res[0]['tracker']
    tracker_type = res[0]['type']

    tags = dict_input.get('tags', [])
    mails = dict_input.get('mails', [])
    res = verify_mail_list(mails)
    if res:
        return res

    sources = dict_input.get('sources', [])
    res = item_basic.verify_sources_list(sources)
    if res:
        return res

    ## TODO: add dashboard key
    level = dict_input.get('level', 1)
    try:
        level = int(level)
        if level not in range(0, 1):
            level = 1
    except:
        level = 1

    tracker_uuid = dict_input.get('uuid', None)
    # check edit ACL
    if tracker_uuid:
        res = api_is_allowed_to_edit_tracker(tracker_uuid, user_id)
        if res[1] != 200:
            return res
    else:
        # check if tracker already tracked in global
        if level==1:
            if is_tracker_in_global_level(tracker, tracker_type) and not tracker_uuid:
                return ({"status": "error", "reason": "Tracker already exist"}, 409)
        else:
            if is_tracker_in_user_level(tracker, tracker_type, user_id) and not tracker_uuid:
                return ({"status": "error", "reason": "Tracker already exist"}, 409)

    tracker_uuid = create_tracker(tracker , tracker_type, user_id, level, tags, mails, description, tracker_uuid=tracker_uuid, sources=sources)

    return ({'tracker': tracker, 'type': tracker_type, 'uuid': tracker_uuid}, 200)

##-- CREATE TRACKER --##

##############
#### YARA ####
def get_yara_rules_dir():
    return os.path.join(os.environ['AIL_BIN'], 'trackers', 'yara')

def get_yara_rules_default_dir():
    return os.path.join(os.environ['AIL_BIN'], 'trackers', 'yara', 'ail-yara-rules', 'rules')

# # TODO: cache + update
def get_all_default_yara_rules_types():
    yara_dir = get_yara_rules_default_dir()
    all_yara_types = next(os.walk(yara_dir))[1]
    # save in cache ?
    return all_yara_types

# # TODO: cache + update
def get_all_default_yara_files():
    yara_dir = get_yara_rules_default_dir()
    all_default_yara_files = {}
    for rules_type in get_all_default_yara_rules_types():
        all_default_yara_files[rules_type] = os.listdir(os.path.join(yara_dir, rules_type))
    return all_default_yara_files

def get_all_default_yara_rules_by_type(yara_types):
    all_default_yara_files = get_all_default_yara_files()
    if yara_types in all_default_yara_files:
        return all_default_yara_files[yara_types]
    else:
        return []

def get_all_tracked_yara_files(filter_disabled=False):
    yara_files = r_serv_tracker.smembers('all:tracker:yara')
    if not yara_files:
        yara_files = []
    if filter_disabled:
        pass
    return yara_files

def reload_yara_rules():
    yara_files = get_all_tracked_yara_files()
    # {uuid: filename}
    rule_dict = {}
    for yar_path in yara_files:
        l_tracker_uuid = get_tracker_uuid_list(yar_path, 'yara')
        for tracker_uuid in l_tracker_uuid:
            rule_dict[tracker_uuid] = os.path.join(get_yara_rules_dir(), yar_path)
    rules = yara.compile(filepaths=rule_dict)
    return rules

# # TODO:
# Avoid useless CHECK
# Empty list == ALL SOURCES
# FIXME MOOVE ME
def get_tracker_sources(tracker, tracker_type):
    l_sources = set()
    for tracker_uuid in get_tracker_uuid_list(tracker, tracker_type):
        sources = get_tracker_uuid_sources(tracker_uuid)
        if sources:
            for source in get_tracker_uuid_sources(tracker_uuid):
                l_sources.add(source)
        else:
            l_sources = []
            break
    return l_sources

def is_valid_yara_rule(yara_rule):
    try:
        yara.compile(source=yara_rule)
        return True
    except:
        return False

def is_default_yara_rule(tracked_yara_name):
    yara_dir = get_yara_rules_dir()
    filename = os.path.join(yara_dir, tracked_yara_name)
    filename = os.path.realpath(filename)
    try:
        if tracked_yara_name.split('/')[0] == 'custom-rules':
            return False
    except:
        return False
    if not os.path.commonprefix([filename, yara_dir]) == yara_dir:
        return False
    else:
        if os.path.isfile(filename):
            return True
    return False

def is_valid_default_yara_rule(yara_rule, verbose=True):
    yara_dir = get_yara_rules_default_dir()
    filename = os.path.join(yara_dir, yara_rule)
    filename = os.path.realpath(filename)
    # incorrect filename
    if not os.path.commonprefix([filename, yara_dir]) == yara_dir:
        if verbose:
            print('error: file transversal')
            print(yara_dir)
            print(filename)
        return False
    else:
        if os.path.isfile(filename):
            return True
        else:
            return False

def save_yara_rule(yara_rule_type, yara_rule, tracker_uuid=None):
    if yara_rule_type == 'yara_custom':
        if not  tracker_uuid:
            tracker_uuid = str(uuid.uuid4())
        filename = os.path.join('custom-rules', tracker_uuid + '.yar')
        with open(os.path.join(get_yara_rules_dir(), filename), 'w') as f:
            f.write(str(yara_rule))
    if yara_rule_type == 'yara_default':
        filename = os.path.join('ail-yara-rules', 'rules', yara_rule)
    return filename

def get_yara_rule_file_by_tracker_name(tracked_yara_name):
    yara_dir = get_yara_rules_dir()
    filename = os.path.join(yara_dir, tracked_yara_name)
    filename = os.path.realpath(filename)
    if not os.path.commonprefix([filename, yara_dir]) == yara_dir:
        print('error: file transversal')
        print(yara_dir)
        print(filename)
        return None
    return filename

def get_yara_rule_content(yara_rule):
    yara_dir = get_yara_rules_dir()
    filename = os.path.join(yara_dir, yara_rule)
    filename = os.path.realpath(filename)

    # incorrect filename
    if not os.path.commonprefix([filename, yara_dir]) == yara_dir:
        return '' # # TODO: throw exception

    with open(filename, 'r') as f:
        rule_content = f.read()
    return rule_content

def api_get_default_rule_content(default_yara_rule):
    yara_dir = get_yara_rules_default_dir()
    filename = os.path.join(yara_dir, default_yara_rule)
    filename = os.path.realpath(filename)

    # incorrect filename
    if not os.path.commonprefix([filename, yara_dir]) == yara_dir:
        return ({'status': 'error', 'reason': 'file transversal detected'}, 400)

    if not os.path.isfile(filename):
        return ({'status': 'error', 'reason': 'yara rule not found'}, 400)

    with open(filename, 'r') as f:
        rule_content = f.read()
    return ({'rule_name': default_yara_rule, 'content': rule_content}, 200)

##-- YARA --##

######################
#### RETRO - HUNT ####

# state: pending/running/completed/paused

# task keys:
## tracker:retro_hunt:task:{task_uuid}          state
#                                               start_time
#                                               end_time
#                                               date_from
#                                               date_to
#                                               creator
#                                               timeout
#                                               date
#                                               type

## ? ? ?
# set tags
# set mails
# limit mail

# SET Retro Hunts

def get_all_retro_hunt_tasks():
    return r_serv_tracker.smembers('tracker:retro_hunt:task:all')

def get_all_pending_retro_hunt_tasks():
    return r_serv_tracker.smembers('tracker:retro_hunt:task:pending')

def get_all_running_retro_hunt_tasks():
    return r_serv_tracker.smembers('tracker:retro_hunt:task:running')

def get_all_paused_retro_hunt_tasks():
    return r_serv_tracker.smembers('tracker:retro_hunt:task:paused')

## Change STATES ##

def get_all_completed_retro_hunt_tasks():
    return r_serv_tracker.smembers('tracker:retro_hunt:task:completed')

def get_retro_hunt_task_to_start():
    task_uuid = r_serv_tracker.spop('tracker:retro_hunt:task:pending')
    if task_uuid:
        set_retro_hunt_task_state(task_uuid, 'running')
    return task_uuid

def pause_retro_hunt_task(task_uuid):
    set_retro_hunt_task_state(task_uuid, 'paused')
    r_cache.hset(f'tracker:retro_hunt:task:{task_uuid}', 'pause', time.time())

def check_retro_hunt_pause(task_uuid):
    is_paused = r_cache.hget(f'tracker:retro_hunt:task:{task_uuid}', 'pause')
    if is_paused:
        return True
    else:
        return False

def resume_retro_hunt_task(task_uuid):
    r_cache.hdel(f'tracker:retro_hunt:task:{task_uuid}', 'pause')
    set_retro_hunt_task_state(task_uuid, 'pending')

## Metadata ##

def get_retro_hunt_task_name(task_uuid):
    return r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'name')

def get_retro_hunt_task_state(task_uuid):
    return r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'state')

def set_retro_hunt_task_state(task_uuid, new_state):
    curr_state = get_retro_hunt_task_state(task_uuid)
    if curr_state:
        r_serv_tracker.srem(f'tracker:retro_hunt:task:{curr_state}', task_uuid)
    r_serv_tracker.sadd(f'tracker:retro_hunt:task:{new_state}', task_uuid)
    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'state', new_state)

def get_retro_hunt_task_type(task_uuid):
    return r_serv_tracker(f'tracker:retro_hunt:task:{task_uuid}', 'type')

# # TODO: yararule
def get_retro_hunt_task_rule(task_uuid, r_compile=False):
    #rule_type = 'yara'
    rule = r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'rule')
    if r_compile:
        #if rule_type == 'yara'
        rule = os.path.join(get_yara_rules_dir(), rule)
        rule_dict = {task_uuid : os.path.join(get_yara_rules_dir(), rule)}
        rule = yara.compile(filepaths=rule_dict)
    return rule

def get_retro_hunt_task_timeout(task_uuid):
    res = r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'timeout')
    if res:
        return int(res)
    else:
        return 30 # # TODO: FIXME use instance limit

def get_retro_hunt_task_date_from(task_uuid):
    return r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'date_from')

def get_retro_hunt_task_date_to(task_uuid):
    return r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'date_to')

def get_retro_hunt_task_creator(task_uuid):
    return r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'creator')

def get_retro_hunt_last_analyzed(task_uuid):
    return r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'last')

# Keep history to relaunch on error/pause
def set_retro_hunt_last_analyzed(task_uuid, last_id):
    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'last', last_id)

def get_retro_hunt_task_sources(task_uuid, r_sort=False):
    sources = r_serv_tracker.smembers(f'tracker:retro_hunt:task:sources:{task_uuid}')
    if not sources:
        sources = set(item_basic.get_all_items_sources(filter_dir=False))
    if r_sort:
        sources = sorted(sources)
    return sources

def get_retro_hunt_task_tags(task_uuid):
    return r_serv_tracker.smembers(f'tracker:retro_hunt:task:tags:{task_uuid}')

def get_retro_hunt_task_mails(task_uuid):
    return r_serv_tracker.smembers(f'tracker:retro_hunt:task:mails:{task_uuid}')

# # TODO: ADD TYPE + TIMEOUT
def get_retro_hunt_task_metadata(task_uuid, date=False, progress=False, creator=False, sources=None, tags=None, description=False, nb_match=False):
    task_metadata = {'uuid': task_uuid}
    task_metadata['state'] = get_retro_hunt_task_state(task_uuid)
    task_metadata['name'] = get_retro_hunt_task_name(task_uuid)
    task_metadata['rule'] = get_retro_hunt_task_rule(task_uuid)
    if creator:
        task_metadata['creator'] = get_retro_hunt_task_creator(task_uuid)
    if date:
        task_metadata['date'] = r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'date')
        task_metadata['date_from'] = get_retro_hunt_task_date_from(task_uuid)
        task_metadata['date_to'] = get_retro_hunt_task_date_to(task_uuid)
    if description:
        task_metadata['description'] = r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'description')
    if nb_match:
        task_metadata['nb_match'] = get_retro_hunt_nb_match(task_uuid)
    if progress:
        task_metadata['progress'] = get_retro_hunt_task_progress(task_uuid)
    if sources:
        task_metadata['sources'] = get_retro_hunt_task_sources(task_uuid, r_sort=True)
    if tags:
        task_metadata['tags'] = get_retro_hunt_task_tags(task_uuid)
    return task_metadata

def get_all_retro_hunt_tasks_with_metadata():
    l_retro_hunt = []
    for task_uuid in get_all_retro_hunt_tasks():
        l_retro_hunt.append(get_retro_hunt_task_metadata(task_uuid, date=True, progress=True, tags=True, nb_match=True))
    return l_retro_hunt

def get_retro_hunt_task_progress(task_uuid):
    if get_retro_hunt_task_state(task_uuid) == 'completed':
        progress = 100
    else:
        progress = r_cache.hget(f'tracker:retro_hunt:task:{task_uuid}', 'progress')
        if not progress:
            progress = compute_retro_hunt_task_progress(task_uuid)
    return progress

def set_cache_retro_hunt_task_progress(task_uuid, progress):
    r_cache.hset(f'tracker:retro_hunt:task:{task_uuid}', 'progress', progress)

def set_cache_retro_hunt_task_id(task_uuid, id):
    r_cache.hset(f'tracker:retro_hunt:task:{task_uuid}', 'id', id)

def clear_retro_hunt_task_cache(task_uuid):
    r_cache.delete(f'tracker:retro_hunt:task:{task_uuid}')

# Others

#                                               date
#                                               type
# tags
# mails
# name
# description

# # # TODO: TYPE
def create_retro_hunt_task(name, rule, date_from, date_to, creator, sources=[], tags=[], mails=[], timeout=30, description=None, task_uuid=None):
    if not task_uuid:
        task_uuid = str(uuid.uuid4())

    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'name', escape(name))

    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'rule', rule)

    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'date', datetime.date.today().strftime("%Y%m%d"))
    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'date_from', date_from)
    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'date_to', date_to)

    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'creator', creator)
    if description:
        r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'description', description)
    if timeout:
        r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'timeout', int(timeout))
    for source in sources:
        r_serv_tracker.sadd(f'tracker:retro_hunt:task:sources:{task_uuid}', escape(source))
    for tag in tags:
        r_serv_tracker.sadd(f'tracker:retro_hunt:task:tags:{task_uuid}', escape(tag))
    for mail in mails:
        r_serv_tracker.sadd(f'tracker:retro_hunt:task:mails:{task_uuid}', escape(mail))

    r_serv_tracker.sadd('tracker:retro_hunt:task:all', task_uuid)
    # add to pending tasks
    r_serv_tracker.sadd('tracker:retro_hunt:task:pending', task_uuid)
    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'state', 'pending')
    return task_uuid

# # TODO: delete rule
def delete_retro_hunt_task(task_uuid):
    if r_serv_tracker.sismember('tracker:retro_hunt:task:running', task_uuid):
        return None

    r_serv_tracker.srem('tracker:retro_hunt:task:pending', task_uuid)
    r_serv_tracker.delete(f'tracker:retro_hunt:task:{task_uuid}')
    r_serv_tracker.delete(f'tracker:retro_hunt:task:sources:{task_uuid}')
    r_serv_tracker.delete(f'tracker:retro_hunt:task:tags:{task_uuid}')
    r_serv_tracker.delete(f'tracker:retro_hunt:task:mails:{task_uuid}')

    for item_date in get_retro_hunt_all_item_dates(task_uuid):
        r_serv_tracker.delete(f'tracker:retro_hunt:task:item:{task_uuid}:{item_date}')

    r_serv_tracker.srem('tracker:retro_hunt:task:all', task_uuid)
    r_serv_tracker.srem('tracker:retro_hunt:task:pending', task_uuid)
    r_serv_tracker.srem('tracker:retro_hunt:task:paused', task_uuid)
    r_serv_tracker.srem('tracker:retro_hunt:task:completed', task_uuid)

    clear_retro_hunt_task_cache(task_uuid)
    return task_uuid

def get_retro_hunt_task_current_date(task_uuid):
    last = get_retro_hunt_last_analyzed(task_uuid)
    if last:
        curr_date = item_basic.get_item_date(last)
    else:
        curr_date = get_retro_hunt_task_date_from(task_uuid)
    return curr_date

def get_retro_hunt_task_nb_src_done(task_uuid, sources=[]):
    if not sources:
        sources = list(get_retro_hunt_task_sources(task_uuid, r_sort=True))
    else:
        sources = list(sources)
    last_id = get_retro_hunt_last_analyzed(task_uuid)
    if last_id:
        last_source = item_basic.get_source(last_id)
        try:
            nb_src_done = sources.index(last_source)
        except ValueError:
            nb_src_done = 0
    else:
        nb_src_done = 0
    return nb_src_done

def get_retro_hunt_dir_day_to_analyze(task_uuid, date, filter_last=False, sources=[]):
    if not sources:
        sources = get_retro_hunt_task_sources(task_uuid, r_sort=True)

    # filter last
    if filter_last:
        last = get_retro_hunt_last_analyzed(task_uuid)
        if last:
            curr_source = item_basic.get_source(last)
            # remove processed sources
            set_sources = sources.copy()
            for source in sources:
                if source != curr_source:
                    set_sources.remove(source)
                else:
                    break
            sources = set_sources

    # return all dirs by day
    date = f'{date[0:4]}/{date[4:6]}/{date[6:8]}'
    dirs = set()
    for source in sources:
        dirs.add(os.path.join(source, date))
    return dirs

# # TODO: move me
def get_items_to_analyze(dir, last=None):
    full_dir = os.path.join(os.environ['AIL_HOME'], 'PASTES', dir) # # TODO: # FIXME: use item config dir
    if os.path.isdir(full_dir):
        all_items = sorted([os.path.join(dir, f) for f in os.listdir(full_dir) if os.path.isfile(os.path.join(full_dir, f))])
        # remove processed items
        if last:
            items_set = all_items.copy()
            for item in all_items:
                if item != last:
                    items_set.remove(item)
                else:
                    break
            all_items = items_set
        return all_items
    else:
        return []

def compute_retro_hunt_task_progress(task_uuid, date_from=None, date_to=None, sources=[], curr_date=None, nb_src_done=0):
    # get nb days
    if not date_from:
        date_from = get_retro_hunt_task_date_from(task_uuid)
    if not date_to:
        date_to = get_retro_hunt_task_date_to(task_uuid)
    nb_days = Date.get_nb_days_by_daterange(date_from, date_to)

    # nb days completed
    if not curr_date:
        curr_date = get_retro_hunt_task_current_date(task_uuid)
    nb_days_done = Date.get_nb_days_by_daterange(date_from, curr_date) - 1

    # sources
    if not sources:
        nb_sources = len(get_retro_hunt_task_sources(task_uuid))
    else:
        nb_sources = len(sources)

    # get progress
    progress = ((nb_days_done * nb_sources) + nb_src_done) * 100 / (nb_days * nb_sources)
    return int(progress)

     # # TODO: # FIXME: # Cache

def save_retro_hunt_match(task_uuid, id, object_type='item'):
    item_date = item_basic.get_item_date(id)
    res = r_serv_tracker.sadd(f'tracker:retro_hunt:task:item:{task_uuid}:{item_date}', id)
    # track nb item by date
    if res == 1:
        r_serv_tracker.zincrby(f'tracker:retro_hunt:task:stat:{task_uuid}', int(item_date), 1)

def get_retro_hunt_all_item_dates(task_uuid):
    return r_serv_tracker.zrange(f'tracker:retro_hunt:task:stat:{task_uuid}', 0, -1)

def get_retro_hunt_nb_match(task_uuid):
    nb_match = r_serv_tracker.hget(f'tracker:retro_hunt:task:{task_uuid}', 'nb_match')
    if not nb_match:
        l_date_value = r_serv_tracker.zrange(f'tracker:retro_hunt:task:stat:{task_uuid}', 0, -1, withscores=True)
        nb_match = 0
        for tuple in l_date_value:
            nb_match += int(tuple[1])
    return int(nb_match)

def set_retro_hunt_nb_match(task_uuid):
    l_date_value = r_serv_tracker.zrange(f'tracker:retro_hunt:task:stat:{task_uuid}', 0, -1, withscores=True)
    nb_match = 0
    for tuple in l_date_value:
        nb_match += int(tuple[1])
    r_serv_tracker.hset(f'tracker:retro_hunt:task:{task_uuid}', 'nb_match', nb_match)

def get_retro_hunt_items_by_daterange(task_uuid, date_from, date_to):
    all_item_id = set()
    if date_from and date_to:
        l_date_match = r_serv_tracker.zrange(f'tracker:retro_hunt:task:stat:{task_uuid}', 0, -1, withscores=True)
        if l_date_match:
            dict_date_match = dict(l_date_match)
            for date_day in Date.substract_date(date_from, date_to):
                if date_day in dict_date_match:
                    all_item_id |= r_serv_tracker.smembers(f'tracker:retro_hunt:task:item:{task_uuid}:{date_day}')
    return all_item_id

def get_retro_hunt_nb_item_by_day(l_task_uuid, date_from=None, date_to=None):
    list_stats = []
    for task_uuid in l_task_uuid:
        dict_task_data = []
        retro_name = get_retro_hunt_task_name(task_uuid)
        l_date_match = r_serv_tracker.zrange(f'tracker:retro_hunt:task:stat:{task_uuid}', 0, -1, withscores=True)
        if l_date_match:
            dict_date_match = dict(l_date_match)
            if not date_from:
                date_from = min(dict_date_match)
            if not date_to:
                date_to = max(dict_date_match)

            date_range = Date.substract_date(date_from, date_to)
            for date_day in date_range:
                nb_seen_this_day = int(dict_date_match.get(date_day, 0))
                dict_task_data.append({"date": date_day,"value": int(nb_seen_this_day)})
            list_stats.append({"name": retro_name,"Data": dict_task_data})
    return list_stats

## API ##
def api_check_retro_hunt_task_uuid(task_uuid):
    if not is_valid_uuid_v4(task_uuid):
        return ({"status": "error", "reason": "Invalid uuid"}, 400)
    if not r_serv_tracker.exists(f'tracker:retro_hunt:task:{task_uuid}'):
        return ({"status": "error", "reason": "Unknown uuid"}, 404)
    return None

def api_get_retro_hunt_items(dict_input):
    task_uuid = dict_input.get('uuid', None)
    res = api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return res

    date_from = dict_input.get('date_from', None)
    date_to = dict_input.get('date_to', None)
    if date_from is None:
        date_from = get_retro_hunt_task_date_from(task_uuid)
        if date_from:
            date_from = date_from[0]
    if date_to is None:
        date_to = date_from
    if date_from > date_to:
        date_from = date_to

    all_items_id = get_retro_hunt_items_by_daterange(task_uuid, date_from, date_to)
    all_items_id = item_basic.get_all_items_metadata_dict(all_items_id)

    res_dict = {}
    res_dict['uuid'] = task_uuid
    res_dict['date_from'] = date_from
    res_dict['date_to'] = date_to
    res_dict['items'] = all_items_id
    return (res_dict, 200)

def api_pause_retro_hunt_task(task_uuid):
    res = api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return res
    task_state = get_retro_hunt_task_state(task_uuid)
    if task_state not in ['pending', 'running']:
        return ({"status": "error", "reason": f"Task {task_uuid} not paused, current state: {task_state}"}, 400)
    pause_retro_hunt_task(task_uuid)
    return (task_uuid, 200)

def api_resume_retro_hunt_task(task_uuid):
    res = api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return res
    task_state = get_retro_hunt_task_state(task_uuid)
    if not r_serv_tracker.sismember('tracker:retro_hunt:task:paused', task_uuid):
        return ({"status": "error", "reason": f"Task {task_uuid} not paused, current state: {get_retro_hunt_task_state(task_uuid)}"}, 400)
    resume_retro_hunt_task(task_uuid)
    return (task_uuid, 200)

def api_validate_rule_to_add(rule, rule_type):
    if rule_type=='yara_custom':
        if not is_valid_yara_rule(rule):
            return ({"status": "error", "reason": "Invalid custom Yara Rule"}, 400)
    elif rule_type=='yara_default':
        if not is_valid_default_yara_rule(rule):
            return ({"status": "error", "reason": "The Yara Rule doesn't exist"}, 400)
    else:
        return ({"status": "error", "reason": "Incorrect type"}, 400)
    return ({"status": "success", "rule": rule, "type": rule_type}, 200)

def api_create_retro_hunt_task(dict_input, creator):
    # # TODO: API: check mandatory arg
    # # TODO: TIMEOUT

    # timeout=30
    rule = dict_input.get('rule', None)
    if not rule:
        return ({"status": "error", "reason": "Retro Hunt Rule not provided"}, 400)
    task_type = dict_input.get('type', None)
    if not task_type:
        return ({"status": "error", "reason": "type not provided"}, 400)

    # # TODO: limit
    name = dict_input.get('name', '')
    name = escape(name)
    name = name[:60]
    # # TODO: limit
    description = dict_input.get('description', '')
    description = escape(description)
    description = description[:1000]

    res = api_validate_rule_to_add(rule , task_type)
    if res[1]!=200:
        return res

    tags = dict_input.get('tags', [])
    mails = dict_input.get('mails', [])
    res = verify_mail_list(mails)
    if res:
        return res

    sources = dict_input.get('sources', [])
    res = item_basic.verify_sources_list(sources)
    if res:
        return res

    date_from = dict_input.get('date_from', '')
    date_to = dict_input.get('date_to', '')
    res = Date.api_validate_str_date_range(date_from, date_to)
    if res:
        return res

    task_uuid = str(uuid.uuid4())

    # RULE
    rule = save_yara_rule(task_type, rule, tracker_uuid=task_uuid)
    task_type = 'yara'

    task_uuid = create_retro_hunt_task(name, rule, date_from, date_to, creator, sources=sources,
                                        tags=tags, mails=mails, timeout=30, description=description, task_uuid=task_uuid)

    return ({'name': name, 'rule': rule, 'type': task_type, 'uuid': task_uuid}, 200)

def api_delete_retro_hunt_task(task_uuid):
    res = api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return res
    if r_serv_tracker.sismember('tracker:retro_hunt:task:running', task_uuid):
        return ({"status": "error", "reason": "You can't delete a running task"}, 400)
    else:
        return (delete_retro_hunt_task(task_uuid), 200)

#if __name__ == '__main__':
    #res = is_valid_yara_rule('rule dummy {  }')

    # res = create_tracker('test', 'word', 'admin@admin.test', 1, [], [], None, sources=['crawled', 'pastebin.com', 'rt/pastebin.com'])
    #res = create_tracker('circl\.lu', 'regex', 'admin@admin.test', 1, [], [], None, sources=['crawled','pastebin.com'])
    #print(res)

    #t_uuid = '1c2d35b0-9330-4feb-b454-da13007aa9f7'
    #res = get_tracker_sources('ail-yara-rules/rules/crypto/certificate.yar', 'yara')

    # sys.path.append(os.environ['AIL_BIN'])
    # from packages import Term
    # Term.delete_term('074ab4be-6049-45b5-a20e-8125a4e4f500')


    #res = get_items_to_analyze('archive/pastebin.com_pro/2020/05/15', last='archive/pastebin.com_pro/2020/05/15/zkHEgqjQ.gz')
    #get_retro_hunt_task_progress('0', nb_src_done=2)

    #res = set_cache_retro_hunt_task_progress('0', 100)
    #res = get_retro_hunt_task_nb_src_done('0', sources=['pastebin.com_pro', 'alerts/pastebin.com_pro', 'crawled'])
    #print(res)

    # sources = ['pastebin.com_pro', 'alerts/pastebin.com_pro', 'crawled']
    # rule = 'custom-rules/4a8a3d04-f0b6-43ce-8e00-bdf47a8df241.yar'
    # name = 'retro_hunt_test_1'
    # description = 'circl retro hunt first test'
    # tags =  ['retro_circl', 'circl']
    # creator = 'admin@admin.test'
    # date_from = '20200610'
    # date_to = '20210630'

    #res = create_retro_hunt_task(name, rule, date_from, date_to, creator, sources=sources, tags=tags, description=description)


    #get_retro_hunt_nb_item_by_day(['80b402ef-a8a9-4e97-adb6-e090edcfd571'], date_from=None, date_to=None, num_day=31)

    #res = get_retro_hunt_nb_item_by_day(['c625f971-16e6-4331-82a7-b1e1b9efdec1'], date_from='20200610', date_to='20210630')

    #res = delete_retro_hunt_task('598687b6-f765-4f8b-861a-09ad76d0ab34')

    #print(res)
