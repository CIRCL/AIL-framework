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

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
#import item_basic

config_loader = ConfigLoader.ConfigLoader()
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

def get_tracker_metedata(tracker_uuid, user_id=False, description=False, level=False, tags=False, mails=False, sparkline=False):
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
    if tags:
        dict_uuid['tags'] = get_tracker_tags(tracker_uuid)
    if sparkline:
        dict_uuid['sparkline'] = get_tracker_sparkline(tracker_uuid)
    dict_uuid['uuid'] = tracker_uuid
    return dict_uuid

def get_tracker_sparkline(tracker_uuid, num_day=6):
    date_range_sparkline = Date.get_date_range(num_day)
    sparklines_value = []
    for date_day in date_range_sparkline:
        nb_seen_this_day = r_serv_tracker.scard('tracker:item:{}:{}'.format(tracker_uuid, date_day))
        if nb_seen_this_day is None:
            nb_seen_this_day = 0
        sparklines_value.append(int(nb_seen_this_day))
    return sparklines_value

def add_tracked_item(tracker_uuid, item_id, item_date):
    # track item
    res = r_serv_tracker.sadd(f'tracker:item:{tracker_uuid}:{item_date}', item_id)
    # track nb item by date
    if res == 1:
        r_serv_tracker.zadd('tracker:stat:{}'.format(tracker_uuid), item_date, int(item_date))

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

    # create tracker tags list
    for tag in tags:
        r_serv_tracker.sadd('tracker:tags:{}'.format(tracker_uuid), escape(tag) )

    # create tracker tags mail notification list
    for mail in mails:
        r_serv_tracker.sadd('tracker:mail:{}'.format(tracker_uuid), escape(mail) )

    # create tracker sources filter
    for source in sources:
        # escape source ?
        r_serv_tracker.sadd(f'tracker:sources:{tracker_uuid}', escape(source) )

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

if __name__ == '__main__':
    #res = is_valid_yara_rule('rule dummy {  }')

    # res = create_tracker('test', 'word', 'admin@admin.test', 1, [], [], None, sources=['crawled', 'pastebin.com', 'rt/pastebin.com'])
    res = create_tracker('circl\.lu', 'regex', 'admin@admin.test', 1, [], [], None, sources=['crawled','pastebin.com'])
    print(res)

    #t_uuid = '1c2d35b0-9330-4feb-b454-da13007aa9f7'
    #res = get_tracker_sources('ail-yara-rules/rules/crypto/certificate.yar', 'yara')

    # sys.path.append(os.environ['AIL_BIN'])
    # from packages import Term
    # Term.delete_term('074ab4be-6049-45b5-a20e-8125a4e4f500')


    #print(res)
