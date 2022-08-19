#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""


"""
import os
import sys
import time

import importlib.util

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib import Users
from lib.objects import Decodeds
from lib.objects import Domains
from lib.objects import Items
from lib.objects.CryptoCurrencies import CryptoCurrency
from lib.objects.Pgps import Pgp
from lib.objects.Screenshots import Screenshot, get_all_screenshots
from lib.objects.Usernames import Username

# # # # CONFIGS # # # #
config_loader = ConfigLoader()
r_kvrocks = config_loader.get_db_conn("Kvrocks_DB")

r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_serv_tracker = config_loader.get_redis_conn("ARDB_Tracker")
r_serv_tags = config_loader.get_redis_conn("ARDB_Tags")
r_crawler = config_loader.get_redis_conn("ARDB_Onion")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None
# # - - CONFIGS - - # #

from core import ail_2_ail
spec = importlib.util.find_spec('ail_2_ail')
old_ail_2_ail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_ail_2_ail)

old_ail_2_ail.r_serv_sync = r_serv_db

from packages import Tag
spec = importlib.util.find_spec('Tag')
old_Tag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_Tag)

old_Tag.r_serv_tags = r_serv_tags

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

from lib import crawlers
spec = importlib.util.find_spec('crawlers')
old_crawlers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_crawlers)

old_crawlers.r_serv_onion = r_crawler

# # TODO: desable features - credentials - stats ? - sentiment analysis

# CREATE FUNCTION BY DB/FEATURES

# /!\ ISSUE WITH FILE DUPLICATES => NEED TO BE REFACTORED


def get_item_date(item_id):
    dirs = item_id.split('/')
    return f'{dirs[-4]}{dirs[-3]}{dirs[-2]}'

################################################################

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

    # Crawler Manager
    manager_url = old_crawlers.get_splash_manager_url()
    manager_api_key = old_crawlers.get_splash_api_key()
    crawlers.save_splash_manager_url_api(manager_url, manager_api_key)
    crawlers.reload_splash_and_proxies_list()

    # ail:misp
    # ail:thehive
    # hive:auto-alerts
    # list_export_tags
    # misp:auto-events
    # whitelist_hive
    # whitelist_misp


    # # TODO: TO CHECK


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
# # TODO: change db -> olds modules + blueprints
# # TODO: HANDLE LOCAL TAGS
# # TODO: HANDLE LOCAL TAGS
# # TODO: HANDLE LOCAL TAGS
# # TODO: HANDLE LOCAL TAGS
# # TODO: HANDLE LOCAL TAGS
def tags_migration():

    # HANDLE LOCAL TAGS

    print(old_Tag.get_all_tags())


    #
    #   /!\ OBJECTS TAGS ISSUE /!\
    #          -> only one layer
    #
    #   issue with subtypes + between objects with same ID
    #
    #
    #
    #



    pass


# # TODO: MIGRATE item_basic.add_map_obj_id_item_id ??????????????????????
###############################
#                             #
#       ITEMS MIGRATION       #
#                             #
###############################

def get_item_father(item_id):
    return r_serv_metadata.hget(f'paste_metadata:{item_id}', 'father')

def items_migration():
    print('ITEMS MIGRATION...')
    # MIGRATE IMPORTED URLEXTRACT Father
    for item_id in Items.get_items_by_source('urlextract'):
        father_id = get_item_father(item_id)
        if father_id:
            item = Items.Item(item_id)
            item.set_father(father_id)



# TODO: migrate cookies
# TODO: migrate auto crawlers

###############################
#                             #
#     CRAWLERS MIGRATION      #
#                             #
###############################

# Retun last crawled domains by type
#   domain;epoch
def get_last_crawled_domains(domain_type):
    return r_crawler.lrange(f'last_{domain_type}', 0 ,-1)

def crawler_migration():
    print('CRAWLER MIGRATION...')

    # for domain_type in ['onion', 'regular']:
    #     for row in get_last_crawled_domains(domain_type):
    #         dom_row, epoch = row.rsplit(';', 1)
    #         domain, port = dom_row.rsplit(':', 1)
    #         print(domain, port, epoch)
    #         #crawlers.add_last_crawled_domain(domain_type, domain, port, epoch)

    for cookiejar_uuid in old_crawlers.get_all_cookiejar():
        meta = old_crawlers.get_cookiejar_metadata(cookiejar_uuid, level=True)
        #print(meta)
        #crawlers.create_cookiejar(meta['user_id'], level=meta['level'], description=meta['description'], cookiejar_uuid=cookiejar_uuid)
        #_set_cookiejar_date(meta['date'])

        for meta_cookie, cookie_uuid in old_crawlers.get_cookiejar_cookies_list(cookiejar_uuid, add_cookie_uuid=True):
            print(cookie_uuid)
            #crawlers.add_cookie_to_cookiejar(cookiejar_uuid, meta_cookie, cookie_uuid=cookie_uuid)

    # TODO: auto crawler -> to Fix / change


    # TODO: crawlers queues

###############################
#                             #
#      DOMAINS MIGRATION      #
#                             #
###############################

# # TODO: DOMAIN DOWN -> start onion_down:20190101

# Start -> 2019-01-01

# BY TYPE - FIRST DATE DOWN / UP

def get_item_link(item_id):
    return r_serv_metadata.hget(f'paste_metadata:{item_id}', 'real_link')

def get_item_father(item_id):
    return r_serv_metadata.hget(f'paste_metadata:{item_id}', 'father')

def get_item_children(item_id):
    return r_serv_metadata.smembers(f'paste_children:{item_id}')

def get_domains_up_by_type(domain_type):
    return r_crawler.smembers(f'full_{domain_type}_up')

def get_domain_first_seen(domain_type, domain):
    return r_crawler.hget(f'{domain_type}_metadata:{domain}', 'first_seen')

def get_domain_last_check(domain_type, domain):
    return r_crawler.hget(f'{domain_type}_metadata:{domain}', 'last_check')

def get_domain_last_origin(domain_type, domain):
    return r_crawler.hget(f'{domain_type}_metadata:{domain}', 'paste_parent')

def get_domain_ports(domain_type, domain):
    l_ports = r_crawler.hget(f'{domain_type}_metadata:{domain}', 'ports')
    if l_ports:
        return l_ports.split(";")
    return []

def get_domain_languages(dom):
    return r_crawler.smembers(f'domain:language:{dom}')

def is_crawled_item(domain, item_id):
    domain_lenght = len(domain)
    if len(item_id) > (domain_lenght+48):
        if item_id[-36-domain_lenght:-36] == domain:
            return True
    return False

def get_crawled_items(domain, root_id):
    crawled_items = get_crawled_items_children(domain, root_id)
    crawled_items.append(root_id)
    return crawled_items

def get_crawled_items_children(domain, root_id):
    crawled_items = []
    for item_id in get_item_children(root_id):
        if is_crawled_item(domain, item_id):
            crawled_items.append(item_id)
            crawled_items.extend(get_crawled_items_children(domain, item_id))
    return crawled_items

def get_domain_history_by_port(domain_type, domain, port):
    history_tuple = r_crawler.zrange(f'crawler_history_{domain_type}:{domain}:{port}', 0, -1, withscores=True)
    history = []
    for root_id, epoch in history_tuple:
        dict_history = {}
        epoch = int(epoch) # force int
        dict_history["epoch"] = epoch
        try:
            int(root_id)
            dict_history['status'] = False
        except ValueError:
            dict_history['status'] = True
            dict_history['root'] = root_id
        history.append(dict_history)
    return history

def domain_migration():
    print('Domains MIGRATION...')

    for domain_type in ['onion', 'regular']:
        for dom in get_domains_up_by_type(domain_type):

            ports = get_domain_ports(domain_type, dom)
            first_seen = get_domain_first_seen(domain_type, dom)
            last_check = get_domain_last_check(domain_type, dom)
            last_origin = get_domain_last_origin(domain_type, dom)
            languages = get_domain_languages(dom)

            domain = Domains.Domain(dom)
            # domain.update_daterange(first_seen)
            # domain.update_daterange(last_check)
            # domain._set_ports(ports)
            # if last_origin:
            #     domain.set_last_origin(last_origin)
            for language in languages:
                print(language)
            #     domain.add_language(language)
            #print('------------------')
            #print('------------------')
            #print('------------------')
            #print('------------------')
            #print('------------------')
            print(dom)
            #print(first_seen)
            #print(last_check)
            #print(ports)

            # # TODO: FIXME filter invalid hostname


             # CREATE DOMAIN HISTORY
            for port in ports:
                for history in get_domain_history_by_port(domain_type, dom, port):
                    epoch = history['epoch']
                    # DOMAIN DOWN
                    if not history.get('status'): # domain DOWN
                        # domain.add_history(epoch, port)
                        print(f'DOWN {epoch}')
                    # DOMAIN UP
                    else:
                        root_id = history.get('root')
                        if root_id:
                            # domain.add_history(epoch, port, root_item=root_id)
                            #print(f'UP {root_id}')
                            crawled_items = get_crawled_items(dom, root_id)
                            for item_id in crawled_items:
                                url = get_item_link(item_id)
                                item_father = get_item_father(item_id)
                                if item_father and url:
                                    #print(f'{url}    {item_id}')
                                    pass
                                    # domain.add_crawled_item(url, port, item_id, item_father)


                    #print()



###############################
#                             #
#      DECODEDS MIGRATION     #
#                             #
###############################
def get_estimated_type(decoded_id):
    return r_serv_metadata.hget(f'metadata_hash:{decoded_id}', 'estimated_type')

def get_decoded_items_list_by_decoder(decoder_type, decoded_id): ###################
    #return r_serv_metadata.zrange('nb_seen_hash:{}'.format(sha1_string), 0, -1)
    return r_serv_metadata.zrange(f'{decoder_type}_hash:{decoded_id}', 0, -1)



def decodeds_migration():
    print('Decoded MIGRATION...')
    decoder_names = ['base64', 'binary', 'hexadecimal']

    Decodeds._delete_old_json_descriptor()
    for decoded_id in Decodeds.get_all_decodeds():
        mimetype = get_estimated_type(decoded_id)
        # ignore invalid object
        if mimetype is None:
            continue
        print()
        print(decoded_id)

        decoded = Decodeds.Decoded(decoded_id)
        filepath = decoded.get_filepath(mimetype=mimetype)
        decoded._save_meta(filepath, mimetype)

        for decoder_type in decoder_names:
            for item_id in get_decoded_items_list_by_decoder(decoder_type, decoded_id):
                print(item_id, decoder_type)
                date = get_item_date(item_id)
            #for decoder_type in :

                decoded.add(decoder_type, date, item_id, mimetype)

###############################
#                             #
#    SCREENSHOTS MIGRATION    #
#                             #
###############################

# old correlation
def get_screenshot_items_list(screenshot_id): ######################### # TODO: DELETE SOLO SCREENSHOTS
    print(f'screenshot:{screenshot_id}')
    return r_crawler.smembers(f'screenshot:{screenshot_id}')
# old correlation
def get_screenshot_domain(screenshot_id):
    return r_crawler.smembers(f'screenshot_domain:{screenshot_id}')

# Tags + Correlations
# # TODO: save orphelin screenshot ?????
def screenshots_migration():
    print('SCREENSHOTS MIGRATION...')
    screenshots = get_all_screenshots()
    #screenshots = ['5fcc292ea8a699aa7a9ce93a704b78b8f493620ccdb2a5cebacb1069a4327211']
    for screenshot_id in screenshots:
        print(screenshot_id)

        screenshot = Screenshot(screenshot_id)

        tags = old_Tag.get_obj_tag(screenshot_id) ################## # TODO:
        if tags:
            print(screenshot_id)
            print(tags)

        # Correlations
        for item_id in get_screenshot_items_list(screenshot_id):
            print(item_id)
            screenshot.add_correlation('item', '', item_id)
        for domain_id in get_screenshot_domain(screenshot_id):
            print(domain_id)
            screenshot.add_correlation('domain', '', domain_id)

###############################
#                             #
#      SUBTYPES MIGRATION     #
#                             #
###############################

def get_item_correlation_obj(obj_type, subtype, obj_id):
    return r_serv_metadata.smembers(f'set_{obj_type}_{subtype}:{obj_id}')

def get_obj_subtype_first_seen(obj_type, subtype, obj_id):
    return r_serv_metadata.hget(f'{obj_type}_metadata_{subtype}:{obj_id}', 'first_seen')

def get_obj_subtype_last_seen(obj_type, subtype, obj_id):
    return r_serv_metadata.hget(f'{obj_type}_metadata_{subtype}:{obj_id}', 'last_seen')

def get_all_subtype_id(obj_type, subtype):
    print(f'{obj_type}_all:{subtype}')
    print(r_serv_metadata.zrange(f'{obj_type}_all:{subtype}', 0, -1))
    return r_serv_metadata.zrange(f'{obj_type}_all:{subtype}', 0, -1)

def get_subtype_object(obj_type, subtype, obj_id):
    if obj_type == 'cryptocurrency':
        return CryptoCurrency(obj_id, subtype)
    elif obj_type == 'pgpdump':
        return Pgp(obj_id, subtype)
    elif obj_type == 'username':
        return Username(obj_id, subtype)

def migrate_subtype_obj(Obj, obj_type, subtype, obj_id):
    first_seen = get_obj_subtype_first_seen(obj_type, subtype, obj_id)
    last_seen = get_obj_subtype_last_seen(obj_type, subtype, obj_id)

    # dates
    for item_id in get_item_correlation_obj(obj_type, subtype, obj_id):
        date = get_item_date(item_id)
        Obj.add(date, item_id)

dict_obj_subtypes = {'cryptocurrency': ['bitcoin', 'bitcoin-cash', 'dash', 'ethereum', 'litecoin', 'monero', 'zcash'],
                    'pgpdump': ['key', 'mail', 'name'],
                    'username': ['telegram', 'twitter', 'jabber']}

def subtypes_obj_migration():
    print('SUBPTYPE MIGRATION...')

    for obj_type in dict_obj_subtypes:
        print(f'{obj_type} MIGRATION...')
        for subtype in dict_obj_subtypes[obj_type]:
            for obj_id in get_all_subtype_id(obj_type, subtype):
                Obj = get_subtype_object(obj_type, subtype, obj_id)
                migrate_subtype_obj(Obj, obj_type, subtype, obj_id)

# # # # # # # # # # # # # # # #
#       STATISTICS
#
# Credential:
# HSET 'credential_by_tld:'+date, tld, 1
def statistics_migration():
    pass

if __name__ == '__main__':

    #core_migration()
    #user_migration()
    #items_migration()
    #crawler_migration()
    #domain_migration()
    #decodeds_migration()
    #screenshots_migration()
    #subtypes_obj_migration()
    #ail_2_ail_migration()
    #trackers_migration()
    #investigations_migration()









    ##########################################################
