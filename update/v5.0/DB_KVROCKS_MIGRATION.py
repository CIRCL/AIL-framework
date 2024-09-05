#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""


"""
import os
import sys

import importlib.util

from lib.ail_core import get_ail_uuid

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib import Tag
from lib import ail_users
from lib.objects import Decodeds
from lib.objects import Domains
from lib.objects import Items
from lib.objects.CryptoCurrencies import CryptoCurrency
from lib.objects.Pgps import Pgp
from lib.objects.Screenshots import Screenshot, get_all_screenshots
from lib.objects.Usernames import Username
from packages import Date

# # # # CONFIGS # # # #
config_loader = ConfigLoader()
r_kvrocks = config_loader.get_db_conn("Kvrocks_DB")
r_obj = config_loader.get_db_conn("Kvrocks_Objects")

r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_serv_tracker = config_loader.get_redis_conn("ARDB_Tracker")
r_serv_tags = config_loader.get_redis_conn("ARDB_Tags")
r_crawler = config_loader.get_redis_conn("ARDB_Onion")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
r_serv_trend = config_loader.get_redis_conn("ARDB_Trending")
r_statistics = config_loader.get_redis_conn("ARDB_Statistics")
config_loader = None
# # - - CONFIGS - - # #

from core import ail_2_ail
spec = importlib.util.find_spec('core.ail_2_ail')
old_ail_2_ail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_ail_2_ail)

old_ail_2_ail.r_serv_sync = r_serv_db

from lib import Tracker

from lib import Investigations
spec = importlib.util.find_spec('lib.Investigations')
old_Investigations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_Investigations)

old_Investigations.r_tracking = r_serv_tracker

from lib import crawlers

def get_item_date(item_id):
    dirs = item_id.split('/')
    return f'{dirs[-4]}{dirs[-3]}{dirs[-2]}'

################################################################

def core_migration():
    print('CORE MIGRATION...')

    # AIL UUID
    ail_uuid = r_serv_db.get('ail:uuid')
    r_kvrocks.set('ail:uuid', ail_uuid)

    # AIL update #
    ail_version = r_serv_db.get('ail:version')
    r_kvrocks.set('ail:version', ail_version)
    dict_update = r_serv_db.hgetall('ail:update_date')
    for version in dict_update:
        r_kvrocks.hset('ail:update_date', version, dict_update[version])

    versions_to_update = r_serv_db.smembers('ail:to_update')
    for version in versions_to_update:
        r_kvrocks.sadd('ail:update:to_update', version)

    update_error = r_serv_db.get('ail:update_error')
    if update_error:
        r_kvrocks.set('ail:update:error', update_error)

    update_in_progress = r_serv_db.get('ail:update_in_progress')
    if update_in_progress:
        r_kvrocks.set('ail:update:update_in_progress', update_in_progress)

    # d4 passivedns
    d4_enabled = bool(r_serv_db.hget('d4:passivedns', 'enabled'))
    d4_update_time = r_serv_db.hget('d4:passivedns', 'update_time')
    r_kvrocks.hset('d4:passivedns', 'enabled', str(d4_enabled))
    r_kvrocks.hset('d4:passivedns', 'update_time', d4_update_time)


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
    ail_users._create_roles()

    for user_id in r_serv_db.hkeys('user:all'):
        role = r_serv_db.hget(f'user_metadata:{user_id}', 'role')
        password_hash = r_serv_db.hget('user:all', user_id)
        token = r_serv_db.hget(f'user_metadata:{user_id}', 'token')
        chg_passwd = r_serv_db.hget(f'user_metadata:{user_id}', 'change_passwd')
        if not chg_passwd:
            chg_passwd = None

        ail_users.create_user(user_id, password=password_hash, chg_passwd=chg_passwd, org_uuid=get_ail_uuid(), role=role)
        print(user_id, token)

    for invite_row in r_crawler.smembers('telegram:invite_code'):
        r_obj.sadd('telegram:invite_code', invite_row)

# # # # # # # # # # # # # # # #
#       AIL 2 AIL
def ail_2_ail_migration():
    print('AIL_2_AIL MIGRATION...')

    # AIL Queues
    for queue_uuid in old_ail_2_ail.get_all_sync_queue():
        # print(queue_uuid)
        meta = old_ail_2_ail.get_sync_queue_metadata(queue_uuid)

        name = meta['name']
        tags = meta['tags']
        description = meta['description']
        max_size = meta['max_size']
        ail_2_ail.create_sync_queue(name, tags=tags, description=description, max_size=max_size, _queue_uuid=queue_uuid)

    # AIL Instances
    for ail_uuid in old_ail_2_ail.get_all_ail_instance():
        # print(ail_uuid)
        meta = old_ail_2_ail.get_ail_instance_metadata(ail_uuid, client_sync_mode=True,
                                                       server_sync_mode=True, sync_queues=True)
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

    ail_2_ail.set_last_updated_sync_config()

###############################
#                             #
#      TRACKER MIGRATION      # # TODO
#                             #
###############################

def get_tracker_level(tracker_uuid):
    level = r_serv_tracker.hget(f'tracker:{tracker_uuid}', 'level')
    if not level:
        level = 0
    return int(level)

def get_tracker_metadata(tracker_uuid):
    meta = {'uuid': tracker_uuid,
            'tracked': r_serv_tracker.hget('tracker:{tracker_uuid}', 'tracked'),
            'type': r_serv_tracker.hget('tracker:{tracker_uuid}', 'type'),
            'date': r_serv_tracker.hget(f'tracker:{tracker_uuid}', 'date'),
            'first_seen': r_serv_tracker.hget(f'tracker:{tracker_uuid}', 'first_seen'),
            'last_seen': r_serv_tracker.hget(f'tracker:{tracker_uuid}', 'last_seen'),
            'user_id': r_serv_tracker.hget('tracker:{tracker_uuid}', 'user_id'),
            'level': get_tracker_level(tracker_uuid),
            'mails': list(r_serv_tracker.smembers('tracker:mail:{tracker_uuid}')),
            'sources': list(r_serv_tracker.smembers(f'tracker:sources:{tracker_uuid}')),
            'tags': list(r_serv_tracker.smembers(f'tracker:tags:{tracker_uuid}')),
            'description': r_serv_tracker.hget(f'tracker:{tracker_uuid}', 'description'),
            'webhook': r_serv_tracker.hget(f'tracker:{tracker_uuid}', 'webhook')}
    return meta

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

# trackers + retro_hunts
def trackers_migration():
    print('TRACKERS MIGRATION...')
    for tracker_uuid in old_Tracker.get_all_tracker_uuid():
        meta = get_tracker_metadata(tracker_uuid)
        Tracker._re_create_tracker(meta['type'], meta['uuid'], meta['tracked'], 'TEST_ORG', meta['user_id'], meta['level'],
                                   tags=meta['tags'], mails=meta['mails'], description=meta['description'],
                                   webhook=meta['webhook'], sources=meta['sources'],
                                   first_seen=meta['first_seen'], last_seen=meta['last_seen'])

        tracker = Tracker.Tracker(tracker_uuid)
        # object migration
        for item_id in old_Tracker.get_tracker_items_by_daterange(tracker_uuid, meta['first_seen'], meta['last_seen']):
            print(item_id)
            item_date = get_item_date(item_id)
            tracker.add('item', '', item_id, date=item_date)

    print('RETRO HUNT MIGRATION...')

    for task_uuid in old_Tracker.get_all_retro_hunt_tasks():
        retro_hunt = Tracker.RetroHunt(retro_hunt)
        # TODO Create filters
        # TODO GET OLD META
        meta = retro_hunt.get_meta(options={'creator', 'date', 'description', 'filter', 'progress', 'tags'})
        last_id = old_Tracker.get_retro_hunt_last_analyzed(task_uuid)
        timeout = old_Tracker.get_retro_hunt_task_timeout(task_uuid)
        Tracker._re_create_retro_hunt_task(meta['name'], meta['rule'], meta['date'], meta['date_from'], meta['date_to'], meta['creator'], meta['sources'], meta['tags'], [], timeout, meta['description'], task_uuid, state=meta['state'], nb_match=meta['nb_match'], last_id=last_id)

        for obj_id in old_Tracker.get_retro_hunt_items_by_daterange(task_uuid, meta['date_from'], meta['date_to']):
            retro_hunt.add('item', '', obj_id)


###############################
#                             #
#  INVESTIGATION MIGRATION    #
#                             #
###############################

def investigations_migration():
    print('INVESTIGATION MIGRATION...')
    for investigation_uuid in old_Investigations.get_all_investigations():
        old_investigation = old_Investigations.Investigation(investigation_uuid)
        meta = old_investigation.get_metadata()
        Investigations._re_create_investigation(meta['uuid'], get_ail_uuid(), meta['user_creator'], 1, meta['date'], meta['name'], meta['threat_level'], meta['analysis'], meta['info'], meta['tags'], meta['last_change'], meta['timestamp'], meta['misp_events'])
        new_investigation = Investigations.Investigation(meta['uuid'])
        for dict_obj in old_investigation.get_objects():
            new_investigation.register_object(dict_obj['id'], dict_obj['type'], dict_obj['subtype'])
        new_investigation.set_last_change(meta['last_change'])

###############################
#                             #
#       TAGS MIGRATION        #
#                             #
###############################

def get_all_items_tags():
    return r_serv_tags.smembers('list_tags:item')

def get_all_items_tags_by_day(tag, date):
    return r_serv_tags.smembers(f'{tag}:{date}')

def get_tag_first_seen(tag, r_int=False):
    res = r_serv_tags.hget(f'tag_metadata:{tag}', 'first_seen')
    if r_int:
        if res is None:
            return 99999999
        else:
            return int(res)
    return res

def get_tags_first_seen():
    first_seen = int(Date.get_today_date_str())
    for tag in get_all_items_tags():
        tag_first = get_tag_first_seen(tag, r_int=True)
        if tag_first < first_seen:
            first_seen = tag_first
    return str(first_seen)

def get_active_taxonomies():
    return r_serv_tags.smembers('active_taxonomies')

def get_active_galaxies():
    return r_serv_tags.smembers('active_galaxies')

def tags_migration():
    for taxonomy in get_active_taxonomies():
        Tag.enable_taxonomy(taxonomy)

    for galaxy in get_active_galaxies():
        Tag.enable_galaxy(galaxy)

    # Items tags
    for tag in get_all_items_tags():
        print(tag)
        tag_first = get_tag_first_seen(tag)
        if tag_first:
            for date in Date.get_date_range_today(tag_first):
                print(date)
                for item_id in get_all_items_tags_by_day(tag, date):
                    item = Items.Item(item_id)
                    item.add_tag(tag)

# # TODO: BUILD FIRST/LAST object DATE
###############################
#                             #
#       ITEMS MIGRATION       #
#                             #
###############################

def get_item_father(item_id):
    return r_serv_metadata.hget(f'paste_metadata:{item_id}', 'father')

def get_item_duplicate(item_id, r_list=True):
    res = r_serv_metadata.smembers(f'dup:{item_id}')
    if r_list:
        if res:
            return list(res)
        else:
            return []
    return res

def get_item_duplicates_dict(item_id):
    dict_duplicates = {}
    for duplicate in get_item_duplicate(item_id):
        duplicate = duplicate[1:-1].replace('\'', '').replace(' ', '').split(',')
        duplicate_id = duplicate[1]
        if duplicate_id not in dict_duplicates:
            dict_duplicates[duplicate_id] = {}
        algo = duplicate[0]
        if algo == 'tlsh':
            similarity = 100 - int(duplicate[2])
        else:
            similarity = int(duplicate[2])
        dict_duplicates[duplicate_id][algo] = similarity
    return dict_duplicates


def items_migration():
    print('ITEMS MIGRATION...')
    # MIGRATE IMPORTED URLEXTRACT Father
    for item_id in Items.get_items_by_source('urlextract'):
        father_id = get_item_father(item_id)
        if father_id:
            item = Items.Item(item_id)
            item.set_parent(father_id)

    # DUPLICATES
    for tag in ['infoleak:automatic-detection="credential"']:
        print(f'Duplicate migration: {tag}')
        tag_first = get_tag_first_seen(tag)
        if tag_first:
            for date in Date.get_date_range_today(tag_first):
                print(date)
                for item_id in get_all_items_tags_by_day(tag, date):
                    item = Items.Item(item_id)
                    duplicates_dict = get_item_duplicates_dict(item_id)
                    for id_2 in duplicates_dict:
                        for algo in duplicates_dict[id_2]:
                            print(algo, duplicates_dict[id_2][algo], id_2)
                            item.add_duplicate(algo, duplicates_dict[id_2][algo], id_2)

    # ITEM FIRST/LAST DATE
    Items._manual_set_items_date_first_last()


###############################
#                             #
#     CRAWLERS MIGRATION      #
#                             #
###############################

def get_all_cookiejar():
    return r_crawler.smembers('cookiejar:all')

def get_cookiejar_level(cookiejar_uuid):
    level = r_crawler.hget(f'cookiejar_metadata:{cookiejar_uuid}', 'level')
    try:
        level = int(level)
    except:
        level = 0
    return level

def get_cookiejar_metadata(cookiejar_uuid):
    dict_cookiejar = {}
    if r_crawler.exists(f'cookiejar_metadata:{cookiejar_uuid}'):
        dict_cookiejar['uuid'] = cookiejar_uuid
        dict_cookiejar['description'] = r_crawler.hget(f'cookiejar_metadata:{cookiejar_uuid}', 'description')
        dict_cookiejar['date'] = r_crawler.hget(f'cookiejar_metadata:{cookiejar_uuid}', 'date')
        dict_cookiejar['user'] = r_crawler.hget(f'cookiejar_metadata:{cookiejar_uuid}', 'user_id')
        dict_cookiejar['level'] = get_cookiejar_level(cookiejar_uuid)
    return dict_cookiejar

def get_cookiejar_cookies_uuid(cookiejar_uuid):
    res = r_crawler.smembers(f'cookiejar:{cookiejar_uuid}:cookies:uuid')
    if not res:
        res = []
    return res

def get_cookie_dict(cookie_uuid):
    cookie_dict = {}
    for key_name in r_crawler.hkeys(f'cookiejar:cookie:{cookie_uuid}'):
        cookie_dict[key_name] = r_crawler.hget(f'cookiejar:cookie:{cookie_uuid}', key_name)
    return cookie_dict

# Return last crawled domains by type
#   domain;epoch
def get_last_crawled_domains(domain_type):
    return r_crawler.lrange(f'last_{domain_type}', 0, -1)

def get_domains_blacklist(domain_type):
    return r_crawler.smembers(f'blacklist_{domain_type}')

def crawler_migration():
    print('CRAWLER MIGRATION...')

    for domain_type in ['onion', 'regular']:
        for domain in get_domains_blacklist(domain_type):
            crawlers.blacklist_domain(domain)

    for cookiejar_uuid in get_all_cookiejar():
        meta = get_cookiejar_metadata(cookiejar_uuid)
        if meta:
            # print(meta)
            cookiejar = crawlers.Cookiejar(meta['uuid'])
            if not cookiejar.exists():
                crawlers.create_cookiejar(get_ail_uuid(), meta['user'], description=meta['description'], level=meta['level'],
                                          cookiejar_uuid=meta['uuid'])
                cookiejar._set_date(meta['date'])

                for cookie_uuid in get_cookiejar_cookies_uuid(meta['uuid']):
                    cookie_dict = get_cookie_dict(cookie_uuid)
                    if cookie_dict:
                        # print(cookie_dict)
                        crawlers.api_create_cookie(get_ail_uuid(), meta['user'], 'admin', cookiejar_uuid, cookie_dict)

    auto_crawler_web = r_crawler.smembers('auto_crawler_url:regular')
    auto_crawler_onion = r_crawler.smembers('auto_crawler_url:onion')
    if auto_crawler_onion or auto_crawler_web:
        with open('old_auto_crawler_domains.txt', 'w') as f:
            f.write('OLD Crawler Scheduler:\n\n')
            for domain in auto_crawler_onion:
                f.write(f'{domain}\n')
            for domain in auto_crawler_web:
                f.write(f'{domain}\n')

###############################
#                             #
#      DOMAINS MIGRATION      #
#                             #
###############################

# Start -> 2019-01-01

# BY TYPE - FIRST DATE DOWN / UP

def get_domain_down_by_date(domain_type, date):
    return r_crawler.smembers(f'{domain_type}_down:{date}')

def get_item_link(item_id):
    return r_serv_metadata.hget(f'paste_metadata:{item_id}', 'real_link')

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
    domain_length = len(domain)
    if len(item_id) > (domain_length+48):
        if item_id[-36-domain_length:-36] == domain:
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
        epoch = int(epoch)  # force int
        dict_history["epoch"] = epoch
        try:
            int(root_id)
            dict_history['status'] = False
        except ValueError:
            dict_history['status'] = True
            dict_history['root'] = root_id
        history.append(dict_history)
    return history

def get_domain_tags(domain):
    return r_serv_metadata.smembers(f'tag:{domain}')

def domain_migration():
    print('Domains MIGRATION...')

    for domain_type in ['onion', 'regular']:
        for dom in get_domains_up_by_type(domain_type):
            if domain_type == 'onion':
                if not crawlers.is_valid_onion_domain(dom):
                    print(dom)
                    continue
            ports = get_domain_ports(domain_type, dom)
            first_seen = get_domain_first_seen(domain_type, dom)
            last_check = get_domain_last_check(domain_type, dom)
            last_origin = get_domain_last_origin(domain_type, dom)
            languages = get_domain_languages(dom)

            domain = Domains.Domain(dom)
            domain.update_daterange(first_seen)
            domain.update_daterange(last_check)
            if last_origin:
                domain.set_last_origin(last_origin)
            for language in languages:
                print(language)
                domain.add_language(language)
            for tag in get_domain_tags(domain):
                domain.add_tag(tag)

            print(dom)

            # CREATE DOMAIN HISTORY
            for port in ports:
                for history in get_domain_history_by_port(domain_type, dom, port):
                    epoch = history['epoch']
                    # DOMAIN DOWN
                    if not history.get('status'):  # domain DOWN
                        domain.add_history(epoch)
                        print(f'DOWN {epoch}')
                    # DOMAIN UP
                    else:
                        root_id = history.get('root')
                        if root_id:
                            domain.add_history(epoch, root_item=root_id)
                            print(f'UP {root_id}')
                            crawled_items = get_crawled_items(dom, root_id)
                            for item_id in crawled_items:
                                item = Items.Item(item_id)
                                url = get_item_link(item_id)
                                parent_id = get_item_father(item_id)
                                if parent_id and url:
                                    print(f'{url}    {item_id}')
                                    item.set_crawled(url, parent_id)

    for domain_type in ['onion', 'regular']:
        for date in Date.get_date_range_today('20190101'):
            for dom in get_domain_down_by_date(domain_type, date):
                if domain_type == 'onion':
                    if not crawlers.is_valid_onion_domain(dom):
                        print(dom)
                        continue
                first_seen = get_domain_first_seen(domain_type, dom)
                last_check = get_domain_last_check(domain_type, dom)
                last_origin = get_domain_last_origin(domain_type, dom)

                domain = Domains.Domain(dom)
                domain.update_daterange(first_seen)
                domain.update_daterange(last_check)
                if last_origin:
                    domain.set_last_origin(last_origin)
                domain.add_history(0, None, date=date)


###############################
#                             #
#      DECODED MIGRATION      #
#                             #
###############################
def get_estimated_type(decoded_id):
    return r_serv_metadata.hget(f'metadata_hash:{decoded_id}', 'estimated_type')

def get_hash_size(decoded_id):
    return r_serv_metadata.hget(f'metadata_hash:{decoded_id}', 'size')

def get_decoded_items_list_by_decoder(decoder_type, decoded_id):
    return r_serv_metadata.zrange(f'{decoder_type}_hash:{decoded_id}', 0, -1)

def get_decodeds_tags(decoded_id):
    return r_serv_metadata.smembers(f'tag:{decoded_id}')

def decodeds_migration():
    print('Decoded MIGRATION...')
    algo_names = ['base64', 'binary', 'hexadecimal']

    Decodeds._delete_old_json_descriptor()
    for decoded_id in Decodeds.get_all_decodeds_files():
        mimetype = get_estimated_type(decoded_id)
        # ignore invalid object
        if mimetype is None:
            continue
        print()
        print(decoded_id)

        decoded = Decodeds.Decoded(decoded_id)
        decoded._add_create()
        decoded.set_mimetype(mimetype)

        size = get_hash_size(decoded_id)
        if not size:
            filepath = decoded.get_filepath(mimetype=mimetype)
            size = os.path.getsize(filepath)
        decoded.set_size(size)

        for tag in get_decodeds_tags(decoded_id):
            decoded.add_tag(tag)

        for algo in algo_names:
            for item_id in get_decoded_items_list_by_decoder(algo, decoded_id):
                print(item_id, algo)
                date = get_item_date(item_id)
                decoded.add(algo, date, item_id, mimetype=mimetype)

###############################
#                             #
#    SCREENSHOTS MIGRATION    #
#                             #
###############################

# old correlation
def get_screenshot_items_list(screenshot_id):
    print(f'screenshot:{screenshot_id}')
    return r_crawler.smembers(f'screenshot:{screenshot_id}')

# old correlation
def get_screenshot_domain(screenshot_id):
    return r_crawler.smembers(f'screenshot_domain:{screenshot_id}')

def get_screenshot_tags(screenshot_id):
    return r_serv_metadata.smembers(f'tag:{screenshot_id}')

# Tags + Correlations
def screenshots_migration():
    print('SCREENSHOTS MIGRATION...')
    screenshots = get_all_screenshots()
    for screenshot_id in screenshots:
        print(screenshot_id)

        screenshot = Screenshot(screenshot_id)

        for tag in get_screenshot_tags(screenshot_id):
            screenshot.add_tag(tag)
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
    # dates
    for item_id in get_item_correlation_obj(obj_type, subtype, obj_id):
        date = get_item_date(item_id)
        Obj.add(date, item_id)


dict_obj_subtypes = {'cryptocurrency': ['bitcoin', 'bitcoin-cash', 'dash', 'ethereum', 'litecoin', 'monero', 'zcash'],
                     'pgpdump': ['key', 'mail', 'name'],
                     'username': ['telegram', 'twitter', 'jabber']}

def subtypes_obj_migration():
    print('SUBTYPE MIGRATION...')
    pgp_symmetrical_key = '0x0000000000000000'

    for obj_type in dict_obj_subtypes:
        print(f'{obj_type} MIGRATION...')
        for subtype in dict_obj_subtypes[obj_type]:
            for obj_id in get_all_subtype_id(obj_type, subtype):
                if obj_type == 'pgp' and subtype == 'key' and obj_id == pgp_symmetrical_key:
                    pass
                else:
                    pgp_obj = get_subtype_object(obj_type, subtype, obj_id)
                    migrate_subtype_obj(pgp_obj, obj_type, subtype, obj_id)

    # ADD PGP Symmetrical tag to item
    # for item_id in get_item_correlation_obj('pgpdump', 'key', pgp_symmetrical_key):
    #     item = Items.Item(item_id)
    #     item.add_tag(f'infoleak:automatic-detection="pgp-symmetric";{item_id}')

# # # # # # # # # # # # # # # #
#       STATISTICS
#
# Credential:
# HSET 'credential_by_tld:'+date, tld, 1

# def get_all_provider():
#     return r_serv_trend.smembers('all_provider_set')
#
# def get_item_source_stats_by_date(date, source):
#     stats = {'num': r_serv_trend.hget(f'{source}_num', date),
#              'size': r_serv_trend.hget(f'{source}_size', date),
#              'avg': r_serv_trend.hget(f'{source}_avg', date)}
#     return stats
#
# def get_item_stats_size_avg_by_date(date):
#     return r_serv_trend.zrange(f'top_avg_size_set_{date}', 0, -1, withscores=True)
#
# def get_item_stats_nb_by_date(date):
#     return r_serv_trend.zrange(f'providers_set_{date}', 0, -1, withscores=True)
#
# def get_top_stats_module(module_name, date):
#     return r_serv_trend.zrange(f'top_{module_name}_set_{date}', 0, -1, withscores=True)
#
# def get_module_tld_stats_by_date(module, date):
#     return r_serv_trend.hgetall(f'{module}_by_tld:{date}')
#
# def get_iban_country_stats_by_date(date):
#     return r_serv_trend.hgetall(f'iban_by_country:{date}')
#
# def statistics_migration():
#     # paste_by_modules_timeout
#
#     # Date full history => lot of keys
#
#
#     # top_size_set_{date}
#     # top_avg_size_set_{date}
#
#     # 'providers_set_{date}
#
#
#
#     sources = get_all_provider()
#     for date in Date.get_date_range_today('20180101'):
#
#         size_avg = get_item_stats_size_avg_by_date(date)
#
#         nb_items = get_item_stats_nb_by_date(date)
#
#         # top_size_set_{date}
#         # top_avg_size_set_{date}
#
#         # 'providers_set_{date}
#
#         # ITEM STATS
#         for source in sources:
#             source_stat = get_item_source_stats_by_date(date, source)
#             Statistics._create_item_stats_size_nb(date, source, source_stat['num'],
#                                                   source_stat['size'], source_stat['avg'])
#
#
#
#         # MODULE STATS
#         for module in ['credential', 'mail', 'SQLInjection']:
#             stats = get_module_tld_stats_by_date(module, date)
#             for tld in stats:
#                 if tld:
#                     print(module, date, tld, stats[tld])
#                     Statistics.add_module_tld_stats_by_date(module, date, tld, stats[tld])
#         stats = get_iban_country_stats_by_date(date)
#         for tld in stats:
#             if tld:
#                 print('iban', date, tld, stats[tld])
#                 Statistics.add_module_tld_stats_by_date('iban', date, tld, stats[tld])
#         for module in ['credential']:
#             # TOP STATS
#             top_module = get_top_stats_module(module, date)
#             for keyword, total_sum in top_module:
#                 print(date, module, keyword, total_sum)
#                 Statistics._add_module_stats(module, total_sum, keyword, date)


###############################
#                             #
#       CVES MIGRATION        #
#                             #
###############################

from modules.CveModule import CveModule

def cves_migration():
    module = CveModule()
    tag = 'infoleak:automatic-detection="cve"'
    first = Tag.get_tag_first_seen(tag)
    last = Tag.get_tag_last_seen(tag)
    if first and last:
        for date in Date.substract_date(first, last):
            for item_id in Tag.get_tag_objects(tag, 'item', date=date):
                module.compute(f'{item_id} 0')


if __name__ == '__main__':

    core_migration()
    user_migration()
    tags_migration()
    items_migration()
    crawler_migration()
    domain_migration()                      # TO RE-TEST
    decodeds_migration()
    screenshots_migration()
    subtypes_obj_migration()
    ail_2_ail_migration()
    trackers_migration()
    investigations_migration()

    # Create CVE Correlation
    cves_migration()
