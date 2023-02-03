#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import datetime
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

BACKGROUND_UPDATES = {
    'v1.5': {
        'nb_updates': 5,
        'message': 'Tags and Screenshots'
    },
    'v2.4': {
        'nb_updates': 1,
        'message': ' Domains Tags and Correlations'
    },
    'v2.6': {
        'nb_updates': 1,
        'message': 'Domains Tags and Correlations'
    },
    'v2.7': {
        'nb_updates': 1,
        'message': 'Domains Tags'
    },
    'v3.4': {
        'nb_updates': 1,
        'message': 'Domains Languages'
    },
    'v3.7': {
        'nb_updates': 1,
        'message': 'Trackers first_seen/last_seen'
    }
}


def get_ail_version():
    return r_db.get('ail:version')


def get_ail_float_version():
    version = get_ail_version()
    if version:
        version = float(version[1:])
    else:
        version = 0
    return version


def get_ail_all_updates(date_separator='-'):
    dict_update = r_db.hgetall('ail:update_date')
    if date_separator:
        for version in dict_update:
            u_date = dict_update[version]
            dict_update[version] = f'{u_date[0:4]}{date_separator}{u_date[4:6]}{date_separator}{u_date[6:8]}'
    return dict_update


def add_ail_update(version):
    # Add new AIL version
    r_db.hset('ail:update_date', version, datetime.datetime.now().strftime("%Y%m%d"))
    # Set current ail version
    if float(version[1:]) > get_ail_float_version():
        r_db.set('ail:version', version)


def check_version(version):
    if version[0] != 'v':
        return False
    try:
        int(version[1])
        int(version[-1])
        int(version[1:].replace('.', ''))
    except:
        return False
    if '..' in version:
        return False
    return True


#### UPDATE BACKGROUND ####

def exits_background_update_to_launch():
    return r_db.scard('ail:update:to_update') != 0


def is_version_in_background_update(version):
    return r_db.sismember('ail:update:to_update', version)


def get_all_background_updates_to_launch():
    return r_db.smembers('ail:update:to_update')


def get_current_background_update():
    return r_db.get('ail:update:update_in_progress')


def get_current_background_update_script():
    return r_db.get('ail:update:current_background_script')


def get_current_background_update_script_path(version, script_name):
    return os.path.join(os.environ['AIL_HOME'], 'update', version, script_name)


def get_current_background_nb_update_completed():
    return r_db.scard('ail:update:update_in_progress:completed')


def get_current_background_update_progress():
    progress = r_db.get('ail:update:current_background_script_stat')
    if not progress:
        progress = 0
    return int(progress)


def get_background_update_error():
    return r_db.get('ail:update:error')


def add_background_updates_to_launch(version):
    return r_db.sadd('ail:update:to_update', version)


def start_background_update(version):
    r_db.delete('ail:update:error')
    r_db.set('ail:update:update_in_progress', version)


def set_current_background_update_script(script_name):
    r_db.set('ail:update:current_background_script', script_name)
    r_db.set('ail:update:current_background_script_stat', 0)


def set_current_background_update_progress(progress):
    r_db.set('ail:update:current_background_script_stat', progress)


def set_background_update_error(error):
    r_db.set('ail:update:error', error)


def end_background_update_script():
    r_db.sadd('ail:update:update_in_progress:completed')


def end_background_update(version):
    r_db.delete('ail:update:update_in_progress')
    r_db.delete('ail:update:current_background_script')
    r_db.delete('ail:update:current_background_script_stat')
    r_db.delete('ail:update:update_in_progress:completed')
    r_db.srem('ail:update:to_update', version)


def clear_background_update():
    r_db.delete('ail:update:error')
    r_db.delete('ail:update:update_in_progress')
    r_db.delete('ail:update:current_background_script')
    r_db.delete('ail:update:current_background_script_stat')
    r_db.delete('ail:update:update_in_progress:completed')


def get_update_background_message(version):
    return BACKGROUND_UPDATES[version]['message']


# TODO: Detect error in subprocess
def get_update_background_metadata():
    dict_update = {}
    version = get_current_background_update()
    if version:
        dict_update['version'] = version
        dict_update['script'] = get_current_background_update_script()
        dict_update['script_progress'] = get_current_background_update_progress()
        dict_update['nb_update'] = BACKGROUND_UPDATES[dict_update['version']]['nb_updates']
        dict_update['nb_completed'] = get_current_background_nb_update_completed()
        dict_update['progress'] = int(dict_update['nb_completed'] * 100 / dict_update['nb_update'])
        dict_update['error'] = get_background_update_error()
    return dict_update


##-- UPDATE BACKGROUND --##


if __name__ == '__main__':
    res = check_version('v3.1..1')
    print(res)
