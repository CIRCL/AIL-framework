#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import yara

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
#import item_basic

config_loader = ConfigLoader.ConfigLoader()
r_serv_tracker = config_loader.get_redis_conn("ARDB_Tracker")
config_loader = None

def get_tracker_uuid_list(tracker, tracker_type):
    return list(r_serv_tracker.smembers('all:tracker_uuid:{}:{}'.format(tracker_type, tracker)))

def get_tracker_tags(tracker_uuid):
    return list(r_serv_tracker.smembers('tracker:tags:{}'.format(tracker_uuid)))

def get_tracker_mails(tracker_uuid):
    return list(r_serv_tracker.smembers('tracker:mail:{}'.format(tracker_uuid)))

def get_tracker_description(tracker_uuid):
    return r_serv_tracker.hget('tracker:{}'.format(tracker_uuid), 'description')

def add_tracked_item(tracker_uuid, item_id, item_date):
    # track item
    r_serv_tracker.sadd('tracker:item:{}:{}'.format(tracker_uuid, item_date), item_id)
    # track nb item by date
    r_serv_tracker.zadd('tracker:stat:{}'.format(tracker_uuid), item_date, int(item_date))

def get_email_subject(tracker_uuid):
    tracker_description = get_tracker_description(tracker_uuid)
    if not tracker_description:
        return "AIL framework: Tracker Alert"
    else:
        return 'AIL framework: {}'.format(tracker_description)

def get_tracker_last_updated_by_type(tracker_type):
    epoch_update = r_serv_tracker.get('tracker:refresh:{}'.format(term_type))
    if not epoch_update:
        epoch_update = 0
    return float(epoch_update)

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

def get_all_tracked_yara_files():
    yara_files = r_serv_tracker.smembers('all:tracker:yara')
    if not yara_files:
        yara_files = []
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

def is_valid_yara_rule(yara_rule):
    try:
        yara.compile(source=yara_rule)
        return True
    except:
        return False

def is_valid_default_yara_rule(yara_rule):
    yara_dir = get_yara_rules_default_dir()
    filename = os.path.join(yara_dir, yara_rule)
    filename = os.path.realpath(filename)

    # incorrect filename
    if not os.path.commonprefix([filename, yara_dir]) == yara_dir:
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
##-- YARA --##


if __name__ == '__main__':
    res = is_valid_yara_rule('rule dummy {  }')
    print(res)
