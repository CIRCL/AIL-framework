#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""


"""
import os
import sys

import importlib.util

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib import Users

# # # # CONFIGS # # # #
config_loader = ConfigLoader()
r_kvrocks = config_loader.get_redis_conn("Kvrocks_DB")

r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_serv_tracker = config_loader.get_redis_conn("ARDB_Tracker")
config_loader = None
# # - - CONFIGS - - # #

from core import ail_2_ail
spec = importlib.util.find_spec('ail_2_ail')
old_ail_2_ail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_ail_2_ail)

old_ail_2_ail.r_serv_sync = r_serv_db

from lib import Tracker
spec = importlib.util.find_spec('Tracker')
old_Tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_Tracker)

old_Tracker.r_serv_tracker = r_serv_tracker

from lib import Investigations
spec = importlib.util.find_spec('Investigations')
old_Investigations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_Investigations)

old_Investigations.r_tracking = r_serv_tracker


# # TODO: desable features - credentials - stats ? - sentiment analysis

# CREATE FUNCTION BY DB/FEATURES

# /!\ ISSUE WITH FILE DUPLICATES => NEED TO BE REFACTORED

def core_migration():
    print('CORE MIGRATION...')

    # AIL UUID
    ail_uuid = r_serv_db.get('ail:uuid')
    r_kvrocks.set('ail:uuid', ail_uuid)

    # AIL update # # TODO: TO TEST
    ail_version = r_serv_db.get('ail:version')
    r_kvrocks.set('ail:version', ail_version)
    dict_update = r_serv_db.hgetall('ail:update_date')
    for version in dict_update:
        r_kvrocks.hset('ail:update_date', version, dict_update[version])

    versions_to_update =  r_serv_db.smembers('ail:to_update')
    for version in versions_to_update:
        r_kvrocks.sadd('ail:update:to_update', version)
    update_error = r_serv_db.get('ail:update_error')
    update_in_progress = r_serv_db.get('ail:update_in_progress')
    r_kvrocks.set('ail:update:error', update_error)
    r_kvrocks.set('ail:update:update_in_progress', update_in_progress)

    # d4 passivedns
    d4_enabled = r_serv_db.hget('d4:passivedns', 'enabled')
    d4_update_time =  r_serv_db.hget('d4:passivedns', 'update_time')
    r_kvrocks.hset('d4:passivedns', 'enabled', bool(d4_enabled))
    r_kvrocks.hset('d4:passivedns', 'update_time', d4_update_time)

    # ail:misp
    # ail:thehive
    # hive:auto-alerts
    # list_export_tags
    # misp:auto-events
    # whitelist_hive
    # whitelist_misp


    # # TODO: TO CHECK
    # config:all_global_section +
    # config:global:crawler +
    # mess_not_saved_export


# # # # # # # # # # # # # # # #
#       USERS
#
# HSET 'user:all'                    user_id            passwd_hash
# HSET 'user:tokens'                 token              user_id
# HSET 'user_metadata:{user_id}'    'token'             token
#                                   'role'              role
#                                   'change_passwd'     'True'
# SET  'user_role:{role}'            user_id
#
def user_migration():
    print('USER MIGRATION...')

    # create role_list
    Users._create_roles_list()

    for user_id in r_serv_db.hkeys('user:all'):
        role = r_serv_db.hget(f'user_metadata:{user_id}', 'role')
        password_hash = r_serv_db.hget('user:all', user_id)
        token = r_serv_db.hget(f'user_metadata:{user_id}', 'token')
        chg_passwd = r_serv_db.hget(f'user_metadata:{user_id}', 'change_passwd')
        if not chg_passwd:
            chg_passwd = None

        Users.create_user(user_id, password=None, chg_passwd=chg_passwd, role=role)
        Users.edit_user_password(user_id, password_hash, chg_passwd=chg_passwd)
        Users._delete_user_token(user_id)
        Users._set_user_token(user_id, token)

# # # # # # # # # # # # # # # #
#       AIL 2 AIL
def ail_2_ail_migration():
    print('AIL_2_AIL MIGRATION...')

    # AIL Queues
    for queue_uuid in old_ail_2_ail.get_all_sync_queue():
        #print(queue_uuid)
        meta = old_ail_2_ail.get_sync_queue_metadata(queue_uuid)

        name = meta['name']
        tags = meta['tags']
        description = meta['description']
        max_size = meta['max_size']
        ail_2_ail.create_sync_queue(name, tags=tags, description=description, max_size=max_size, _queue_uuid=queue_uuid)

    # AIL Instances
    for ail_uuid in old_ail_2_ail.get_all_ail_instance():
        #print(ail_uuid)
        meta = old_ail_2_ail.get_ail_instance_metadata(ail_uuid, client_sync_mode=True, server_sync_mode=True, sync_queues=True)
        url = meta['url']
        api_key = meta['api_key']
        description = meta['description']
        pull = meta['pull']
        push = meta['push']
        ail_2_ail.create_ail_instance(ail_uuid, url, api_key=api_key, description=description, pull=pull, push=push)

        version = old_ail_2_ail.get_ail_server_version(ail_uuid)
        if version:
            ail_2_ail.set_ail_server_version(ail_uuid, version)
        ping = old_ail_2_ail.get_ail_server_ping(ail_uuid)
        if ping:
            ail_2_ail.set_ail_server_ping(ail_uuid, ping)
        error = old_ail_2_ail.get_ail_server_error(ail_uuid)
        if error:
            ail_2_ail.save_ail_server_error(ail_uuid, error)

        for queue_uuid in meta['sync_queues']:
            ail_2_ail.register_ail_to_sync_queue(ail_uuid, queue_uuid)

            for dict_obj in reversed(old_ail_2_ail.get_sync_queue_objects_by_queue_uuid(queue_uuid, ail_uuid, push=True)):
                ail_2_ail.add_object_to_sync_queue(queue_uuid, ail_uuid, dict_obj, push=True, pull=False, json_obj=False)

            for dict_obj in reversed(old_ail_2_ail.get_sync_queue_objects_by_queue_uuid(queue_uuid, ail_uuid, push=False)):
                ail_2_ail.add_object_to_sync_queue(queue_uuid, ail_uuid, dict_obj, push=False, pull=True, json_obj=False)

    # server
    # queue
    # item in queue
    ail_2_ail.set_last_updated_sync_config()

# trackers + retro_hunts
def trackers_migration():
    print('TRACKERS MIGRATION...')
    for tracker_uuid in old_Tracker.get_all_tracker_uuid():
        meta = old_Tracker.get_tracker_metadata(tracker_uuid, user_id=True, description=True, level=True, tags=True, mails=True, sources=True, sparkline=False, webhook=True)
        Tracker._re_create_tracker(meta['tracker'], meta['type'], meta['user_id'], meta['level'], meta['tags'], meta['mails'], meta['description'], meta['webhook'], 0, meta['uuid'], meta['sources'], meta['first_seen'], meta['last_seen'])

        # object migration # # TODO: in background
        for item_id in old_Tracker.get_tracker_items_by_daterange(tracker_uuid, meta['first_seen'], meta['last_seen']):
            Tracker.add_tracked_item(tracker_uuid, item_id)

    print('RETRO HUNT MIGRATION...')

    for task_uuid in old_Tracker.get_all_retro_hunt_tasks():
        meta = old_Tracker.get_retro_hunt_task_metadata(task_uuid, date=True, progress=True, creator=True, sources=True, tags=True, description=True, nb_match=True)
        last_id = old_Tracker.get_retro_hunt_last_analyzed(task_uuid)
        timeout = old_Tracker.get_retro_hunt_task_timeout(task_uuid)
        Tracker._re_create_retro_hunt_task(meta['name'], meta['rule'], meta['date'], meta['date_from'], meta['date_to'], meta['creator'], meta['sources'], meta['tags'], [], timeout, meta['description'], task_uuid, state=meta['state'], nb_match=meta['nb_match'], last_id=last_id)

        # # TODO: IN background ?
        for id in old_Tracker.get_retro_hunt_items_by_daterange(task_uuid, meta['date_from'], meta['date_to']):
            Tracker.save_retro_hunt_match(task_uuid, id)


def investigations_migration():
    print('INVESTIGATION MIGRATION...')
    for investigation_uuid in old_Investigations.get_all_investigations():
        old_investigation = old_Investigations.Investigation(investigation_uuid)
        meta = old_investigation.get_metadata()
        Investigations._re_create_investagation(meta['uuid'], meta['user_creator'], meta['date'], meta['name'], meta['threat_level'], meta['analysis'], meta['info'], meta['tags'], meta['last_change'], meta['timestamp'], meta['misp_events'])
        new_investigation = Investigations.Investigation(meta['uuid'])
        for dict_obj in old_investigation.get_objects():
            new_investigation.register_object(dict_obj['id'], dict_obj['type'], dict_obj['subtype'])
        new_investigation.set_last_change(meta['last_change'])

def item_submit_migration():
    pass

# /!\ KEY COLISION
# # TODO: change db
def tags_migration():

    pass

def items_migration():
    pass

def crawler_migration():

    pass

def domain_migration():
    pass

# # TODO: refractor keys
def correlations_migration():
    pass

# # # # # # # # # # # # # # # #
#       STATISTICS
#
# Credential:
# HSET 'credential_by_tld:'+date, tld, 1
def statistics_migration():
    pass

if __name__ == '__main__':

    core_migration()
    user_migration()
    #ail_2_ail_migration()
    trackers_migration()
    #investigations_migration()









    ##########################################################
