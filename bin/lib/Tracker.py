#!/usr/bin/env python3
# -*-coding:UTF-8 -*
import json
import os
import logging
import logging.config
import re
import sys
import time
import uuid
import yara
import datetime
import base64

import math

from collections import defaultdict
from markupsafe import escape
from textblob import TextBlob
from nltk.tokenize import RegexpTokenizer

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from packages import Date
from lib.ail_core import get_objects_tracked, get_object_all_subtypes, get_objects_retro_hunted
from lib import ail_logger
from lib import ail_orgs
from lib import ConfigLoader
from lib import item_basic
from lib import Tag

# LOGS
logging.config.dictConfig(ail_logger.get_config(name='modules'))
logger = logging.getLogger()

config_loader = ConfigLoader.ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_tracker = config_loader.get_db_conn("Kvrocks_Trackers")
config_loader = None

# NLTK tokenizer
TOKENIZER = None

def init_tokenizer():
    global TOKENIZER
    TOKENIZER = RegexpTokenizer('[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]+',
                                gaps=True, discard_empty=True)

def get_special_characters():
    special_characters = set('[<>~!?@#$%^&*|()_-+={}":;,.\'\n\r\t]/\\')
    special_characters.add('\\s')
    return special_characters

###############
#### UTILS ####
def is_valid_uuid_v4(curr_uuid):
    if not curr_uuid:
        return False
    curr_uuid = curr_uuid.replace('-', '')
    try:
        uuid_test = uuid.UUID(hex=curr_uuid, version=4)
        return uuid_test.hex == curr_uuid
    except:
        return False

def is_valid_regex(tracker_regex):
    try:
        re.compile(tracker_regex)
        return True
    except:
        return False

def is_valid_mail(email):
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}'
    email_regex = re.compile(email_regex)
    result = email_regex.match(email)
    if result:
        return True
    else:
        return False

def verify_mail_list(mail_list):
    for mail in mail_list:
        if not is_valid_mail(mail):
            return {'status': 'error', 'reason': 'Invalid email', 'value': mail}, 400
    return None

## -- UTILS -- ##
#################

###################
####  TRACKER  ####

class Tracker:
    def __init__(self, tracker_uuid):
        self.uuid = tracker_uuid

    def get_uuid(self):
        return self.uuid

    def exists(self):
        return r_tracker.exists(f'tracker:{self.uuid}')

    def _get_field(self, field):
        return r_tracker.hget(f'tracker:{self.uuid}', field)

    def _set_field(self, field, value):
        r_tracker.hset(f'tracker:{self.uuid}', field, value)

    def get_date(self):
        return self._get_field('date')

    def get_last_change(self, r_str=False):
        last_change = self._get_field('last_change')
        if r_str and last_change:
            last_change = datetime.datetime.fromtimestamp(float(last_change)).strftime('%Y-%m-%d %H:%M:%S')
        return last_change

    def get_first_seen(self):
        return self._get_field('first_seen')

    def get_last_seen(self):
        return self._get_field('last_seen')

    def _set_first_seen(self, date):
        self._set_field('first_seen', date)

    def _set_last_seen(self, date):
        self._set_field('last_seen', date)

    def _exist_date(self, date):
        return r_tracker.exists(f'tracker:objs:{self.uuid}:{date}')

    # TODO: ADD CACHE ???
    def update_daterange(self, date=None):
        first_seen = self.get_first_seen()
        # Added Object
        if date:
            date = int(date)
            first_seen = self.get_first_seen()
            # if op == 'add':
            if not first_seen:
                self._set_first_seen(date)
                self._set_last_seen(date)
            else:
                first_seen = int(first_seen)
                last_seen = int(self.get_last_seen())
                if date < first_seen:
                    self._set_first_seen(date)
                if date > last_seen:
                    self._set_last_seen(date)
        else:
            last_seen = self.get_last_seen()
            if first_seen and last_seen:
                valid_first_seen = self._exist_date(first_seen)
                valid_last_seen = self._exist_date(last_seen)
                # update first seen
                if not valid_first_seen:
                    for date in Date.get_daterange(first_seen, last_seen):
                        if self._exist_date(date):
                            self._set_first_seen(date)
                            valid_first_seen = True
                            break
                # update last seen
                if not valid_last_seen:
                    for date in reversed(Date.get_daterange(first_seen, last_seen)):
                        if self._exist_date(date):
                            self._set_first_seen(date)
                            valid_last_seen = True
                            break
                if not valid_first_seen or not valid_last_seen:
                    r_tracker.hdel(f'tracker:{self.uuid}', 'first_seen')
                    r_tracker.hdel(f'tracker:{self.uuid}', 'last_seen')

    def get_description(self):
        return self._get_field('description')

    ## LEVEL ##

    def get_level(self):
        level = self._get_field('level')
        if not level:
            level = 0
        return int(level)

    def set_level(self, level, org_uuid):
        tracker_type = self.get_type()
        if level == 0:  # user only
            user_id = self.get_user()
            r_tracker.sadd(f'user:tracker:{user_id}', self.uuid)
            r_tracker.sadd(f'user:tracker:{user_id}:{tracker_type}', self.uuid)
        elif level == 1:  # global
            r_tracker.sadd('global:tracker', self.uuid)
            r_tracker.sadd(f'global:tracker:{tracker_type}', self.uuid)
        elif level == 2:  # org only
            r_tracker.sadd(f'org:tracker:{org_uuid}', self.uuid)
            r_tracker.sadd(f'org:tracker:{org_uuid}:{tracker_type}', self.uuid)
            self.add_to_org(org_uuid)
        self._set_field('level', level)

    def reset_level(self, old_level, new_level, new_org_uuid):
        if old_level == 0:
            user_id = self.get_user()
            r_tracker.srem(f'user:tracker:{user_id}', self.uuid)
            r_tracker.srem(f'user:tracker:{user_id}:{self.get_type()}', self.uuid)
        elif old_level == 1:
            r_tracker.srem('global:tracker', self.uuid)
            r_tracker.srem(f'global:tracker:{self.get_type()}', self.uuid)
        # Org
        elif old_level == 2:
            old_org = self.get_org()
            r_tracker.srem(f'org:tracker:{old_org}', self.uuid)
            r_tracker.srem(f'org:tracker:{old_org}:{self.get_type()}', self.uuid)
            ail_orgs.remove_obj_to_org(old_org, 'tracker', self.uuid)
        self.set_level(new_level, new_org_uuid)

    def check_level(self, user_org, user_id):
        level = self.get_level()
        if level == 1:
            return True
        elif level == 0:
            return self.get_user() == user_id
        elif level == 2:
            return self.get_org() == user_org

    def is_level_user(self):
        return self.get_level() == 0

    def is_level_org(self):
        return self.get_level() == 2

    def is_level_global(self):
        return self.get_level() == 1

    ## ORG ##

    def get_creator_org(self):
        return self._get_field('creator_org')

    def get_org(self):
        return self._get_field('org')

    def add_to_org(self, org_uuid):
        self._set_field('org', org_uuid)
        ail_orgs.add_obj_to_org(org_uuid, 'tracker', self.uuid)

    ## -ORG- ##

    def get_filters(self):
        filters = self._get_field('filters')
        if not filters:
            return {}
        else:
            return json.loads(filters)

    def set_filters(self, filters):
        if filters:
            self._set_field('filters', json.dumps(filters))

    def del_filters(self, tracker_type, to_track):
        filters = self.get_filters()
        if not filters:
            filters = get_objects_tracked()
        for obj_type in filters:
            r_tracker.srem(f'trackers:objs:{tracker_type}:{obj_type}', to_track)
            r_tracker.srem(f'trackers:uuid:{tracker_type}:{to_track}', f'{self.uuid}:{obj_type}')
        r_tracker.hdel(f'tracker:{self.uuid}', 'filters')

    def get_tracked(self):
        return self._get_field('tracked')

    def get_type(self):
        return self._get_field('type')

    def get_tags(self):
        return r_tracker.smembers(f'tracker:tags:{self.uuid}')

    def _set_tags(self, tags):
        for tag in tags:
            r_tracker.sadd(f'tracker:tags:{self.uuid}', tag)
            Tag.create_custom_tag(tag)  # TODO CUSTOM TAGS

    def _del_tags(self):
        return r_tracker.delete(f'tracker:tags:{self.uuid}')

    def mail_export(self):
        return r_tracker.exists(f'tracker:mail:{self.uuid}')

    def get_mails(self):
        return r_tracker.smembers(f'tracker:mail:{self.uuid}')

    def _set_mails(self, mails):
        for mail in mails:
            r_tracker.sadd(f'tracker:mail:{self.uuid}', escape(mail))

    def _del_mails(self):
        r_tracker.delete(f'tracker:mail:{self.uuid}')

    def get_user(self):
        return self._get_field('user_id')

    def webhook_export(self):
        webhook = self.get_webhook()
        return webhook is not None and webhook

    def get_webhook(self):
        return r_tracker.hget(f'tracker:{self.uuid}', 'webhook')

    def get_sparkline(self, nb_day=6):
        date_range_sparkline = Date.get_date_range(nb_day)
        sparkline = []
        for date in date_range_sparkline:
            nb_seen_this_day = self.get_nb_objs_by_date(date)
            if nb_seen_this_day is None:
                nb_seen_this_day = 0
            sparkline.append(int(nb_seen_this_day))
        return sparkline

    def get_rule(self):
        yar_path = self.get_tracked()
        return yara.compile(filepath=os.path.join(get_yara_rules_dir(), yar_path))

    def get_meta(self, options):
        if not options:
            options = set()
        meta = {'uuid': self.uuid,
                'tracked': self.get_tracked(),  # TODO TO CHECK
                'type': self.get_type(),
                'date': self.get_date(),
                'first_seen': self.get_first_seen(),
                'last_seen': self.get_last_seen()}
        if 'org' in options:
            meta['org'] = self.get_org()
            if 'org_name' in options:
                meta['org_name'] = ail_orgs.Organisation(self.get_org()).get_name()
        if 'user' in options:
            meta['user'] = self.get_user()
        if 'level' in options:
            meta['level'] = self.get_level()
        if 'description' in options:
            meta['description'] = self.get_description()
        if 'nb_objs' in options:
            meta['nb_objs'] = self.get_nb_objs()
        if 'tags' in options:
            meta['tags'] = self.get_tags()
        if 'filters' in options:
            meta['filters'] = self.get_filters()
        if 'mails' in options:
            meta['mails'] = self.get_mails()
        if 'webhooks' in options:
            meta['webhook'] = self.get_webhook()
        if 'sparkline' in options:
            meta['sparkline'] = self.get_sparkline(6)
        return meta

    def _add_to_dashboard(self, obj_type, subtype, obj_id):
        mess = f'{self.uuid}:{int(time.time())}:{obj_type}:{subtype}:{obj_id}'
        if self.is_level_user():
            user = self.get_user()
            r_tracker.lpush(f'trackers:user:{user}', mess)
            r_tracker.ltrim(f'trackers:user:{user}', 0, 9)
        else:
            r_tracker.lpush('trackers:dashboard', mess)
            r_tracker.ltrim(f'trackers:dashboard', 0, 9)

    def get_nb_objs_by_type(self, obj_type):
        return r_tracker.scard(f'tracker:objs:{self.uuid}:{obj_type}')

    def get_objs_by_type(self, obj_type):
        return r_tracker.smembers(f'tracker:objs:{self.uuid}:{obj_type}')

    def get_nb_objs(self):
        objs = {}
        for obj_type in get_objects_tracked():
            nb = self.get_nb_objs_by_type(obj_type)
            if nb:
                objs[obj_type] = nb
        return objs

    def get_objs(self):
        objs = []
        for obj_type in get_objects_tracked():
            for obj in self.get_objs_by_type(obj_type):
                subtype, obj_id = obj.split(':', 1)
                objs.append((obj_type, subtype, obj_id))
        return objs

    def get_nb_objs_by_date(self, date):
        return r_tracker.scard(f'tracker:objs:{self.uuid}:{date}')

    def get_objs_by_date(self, date, obj_types=[]):
        objs = r_tracker.smembers(f'tracker:objs:{self.uuid}:{date}')
        if obj_types:
            l_objs = set()
            for obj in objs:
                obj_type = obj.split(':', 1)[0]
                if obj_type in obj_types:
                    l_objs.add(obj)
            return l_objs
        else:
            return objs

    def get_objs_by_daterange(self, date_from, date_to, obj_types):
        objs = set()
        for date in Date.get_daterange(date_from, date_to):
            objs |= self.get_objs_by_date(date, obj_types=obj_types)
        return objs

    def get_obj_dates(self, obj_type, subtype, obj_id):
        return r_tracker.smembers(f'obj:tracker:{obj_type}:{subtype}:{obj_id}:{self.uuid}')

    # - TODO Data Retention TO Implement - #
    # Or Daily/Monthly Global DB Cleanup:
    #    Iterate on each tracker:
    #       Iterate on each Obj:
    #           Iterate on each date:
    #               Delete from tracker range if date limit exceeded
    # - TODO
    def add(self, obj_type, subtype, obj_id, date=None):
        if not subtype:
            subtype = ''
        if not date:
            date = Date.get_today_date_str()

        new_obj_date = r_tracker.sadd(f'tracker:objs:{self.uuid}:{date}', f'{obj_type}:{subtype}:{obj_id}')
        r_tracker.sadd(f'obj:trackers:{obj_type}:{subtype}:{obj_id}', self.uuid)

        # Only save object match date - Needed for the DB Cleaner
        r_tracker.sadd(f'obj:tracker:{obj_type}:{subtype}:{obj_id}:{self.uuid}', date)
        r_tracker.sadd(f'tracker:objs:{self.uuid}:{obj_type}', f'{subtype}:{obj_id}')

        if new_obj_date:
            self.update_daterange(date)

        self._add_to_dashboard(obj_type, subtype, obj_id)

    def remove(self, obj_type, subtype, obj_id):
        if not subtype:
            subtype = ''

        for date in self.get_obj_dates(obj_type, subtype, obj_id):
            r_tracker.srem(f'tracker:objs:{self.uuid}:{date}', f'{obj_type}:{subtype}:{obj_id}')
            r_tracker.srem(f'obj:tracker:{obj_type}:{subtype}:{obj_id}:{self.uuid}', date)

        r_tracker.srem(f'obj:trackers:{obj_type}:{subtype}:{obj_id}', self.uuid)
        r_tracker.srem(f'tracker:objs:{self.uuid}:{obj_type}', f'{subtype}:{obj_id}')
        self.update_daterange()

    # TODO escape custom tags
    # TODO escape mails ????
    def create(self, tracker_type, to_track, org, user_id, level, description=None, filters={}, tags=[], mails=[], webhook=None):
        if self.exists():
            raise Exception('Error: Tracker already exists')

        # YARA
        if tracker_type == 'yara_custom' or tracker_type == 'yara_default':
            to_track = save_yara_rule(tracker_type, to_track, tracker_uuid=self.uuid)
            tracker_type = 'yara'

        elif tracker_type == 'typosquatting':

            from ail_typo_squatting import runAll

            domain = to_track.split(" ")[0]
            typo_generation = runAll(domain=domain, limit=math.inf, formatoutput="text", pathOutput="-", verbose=False) # TODO REPLACE LIMIT BY -1
            for typo in typo_generation:
                r_tracker.sadd(f'tracker:typosquatting:{to_track}', typo)

        # create metadata
        self._set_field('tracked', to_track)
        self._set_field('type', tracker_type)
        self._set_field('date', datetime.date.today().strftime("%Y%m%d"))
        self._set_field('creator_org', org)
        self._set_field('user_id', user_id)
        if description:
            self._set_field('description', escape(description))
        if webhook:
            self._set_field('webhook', webhook)

        # create all tracker set
        r_tracker.sadd(f'all:tracker:{tracker_type}', to_track)
        # create tracker - uuid map
        r_tracker.sadd(f'all:tracker_uuid:{tracker_type}:{to_track}', self.uuid)
        r_tracker.sadd('trackers:all', self.uuid)
        r_tracker.sadd(f'trackers:all:{tracker_type}', self.uuid)

        # TRACKER LEVEL
        self.set_level(level, org)

        # create tracker tags list
        if tags:
            self._set_tags(tags)

        # create tracker mail notification list
        if mails:
            self._set_mails(mails)

        # Filters
        if not filters:
            filters = {}
            for obj_type in get_objects_tracked():
                filters[obj_type] = {}
        else:
            self.set_filters(filters)
        for obj_type in filters:
            r_tracker.sadd(f'trackers:objs:{tracker_type}:{obj_type}', to_track)
            r_tracker.sadd(f'trackers:uuid:{tracker_type}:{to_track}', f'{self.uuid}:{obj_type}')

        self._set_field('last_change', time.time())

        # toggle refresh module tracker list/set
        trigger_trackers_refresh(tracker_type)
        return self.uuid

    def edit(self, tracker_type, to_track, level, org, description=None, filters={}, tags=[], mails=[], webhook=None):

        # edit tracker
        old_type = self.get_type()
        old_to_track = self.get_tracked()
        old_level = self.get_level()
        user_id = self.get_user()

        # YARA
        if tracker_type == 'yara_custom' or tracker_type == 'yara_default':
            # create yara rule
            if tracker_type == 'yara_default' and old_type == 'yara':
                if not is_default_yara_rule(old_to_track):
                    filepath = get_yara_rule_file_by_tracker_name(old_to_track)
                    if filepath:
                        os.remove(filepath)
            to_track = save_yara_rule(tracker_type, to_track, tracker_uuid=self.uuid)
            tracker_type = 'yara'

        # TODO TYPO EDIT
        elif tracker_type == 'typosquatting':
            pass

        if tracker_type != old_type:
            # LEVEL
            self.reset_level(old_level, level, org)
            # Delete OLD YARA Rule File
            if old_type == 'yara':
                if not is_default_yara_rule(old_to_track):
                    filepath = get_yara_rule_file_by_tracker_name(old_to_track)
                    if filepath:
                        os.remove(filepath)
            if old_type == 'typosquatting':
                r_tracker.delete(f'tracker:typosquatting:{old_to_track}')
            self._set_field('type', tracker_type)

            # create all tracker set
            r_tracker.srem(f'all:tracker:{old_type}', old_to_track)
            r_tracker.sadd(f'all:tracker:{tracker_type}', to_track)
            # create tracker - uuid map
            r_tracker.srem(f'all:tracker_uuid:{old_type}:{old_to_track}', self.uuid)
            r_tracker.sadd(f'all:tracker_uuid:{tracker_type}:{to_track}', self.uuid)
            # create all tracker set by type
            r_tracker.srem(f'trackers:all:{old_type}', self.uuid)
            r_tracker.sadd(f'trackers:all:{tracker_type}', self.uuid)

        # Same Type

        # LEVEL
        self.reset_level(old_level, level, org)

        # To Track Edited
        if to_track != old_to_track:
            self._set_field('tracked', to_track)

        self._set_field('description', description)
        self._set_field('webhook', webhook)

        # Tags
        nb_old_tags = r_tracker.scard(f'tracker:tags:{self.uuid}')
        if nb_old_tags > 0 or tags:
            self._del_tags()
            self._set_tags(tags)

        # Mails
        nb_old_mails = r_tracker.scard(f'tracker:mail:{self.uuid}')
        if nb_old_mails > 0 or mails:
            self._del_mails()
            self._set_mails(mails)

        # Filters
        self.del_filters(old_type, old_to_track)
        if not filters:
            filters = {}
            for obj_type in get_objects_tracked():
                filters[obj_type] = {}
        else:
            self.set_filters(filters)
        for obj_type in filters:
            r_tracker.sadd(f'trackers:objs:{tracker_type}:{obj_type}', to_track)
            r_tracker.sadd(f'trackers:uuid:{tracker_type}:{to_track}', f'{self.uuid}:{obj_type}')

        self._set_field('last_change', time.time())

        # Refresh Trackers
        trigger_trackers_refresh(tracker_type)
        if tracker_type != old_type:
            trigger_trackers_refresh(old_type)
        return self.uuid

    def delete(self):
        for obj in self.get_objs():
            self.remove(obj[0], obj[1], obj[2])

        tracker_type = self.get_type()
        tracked = self.get_tracked()

        if tracker_type == 'typosquatting':
            r_tracker.delete(f'tracker:typosquatting:{tracked}')
        elif tracker_type == 'yara':
            if not is_default_yara_rule(tracked):
                filepath = get_yara_rule_file_by_tracker_name(tracked)
                if filepath:
                    os.remove(filepath)

        # Filters
        filters = get_objects_tracked()
        for obj_type in filters:
            r_tracker.srem(f'trackers:objs:{tracker_type}:{obj_type}', tracked)
            r_tracker.srem(f'trackers:uuid:{tracker_type}:{tracked}', f'{self.uuid}:{obj_type}')

        self._del_mails()
        self._del_tags()

        level = self.get_level()

        if level == 0:  # user only
            user = self.get_user()
            r_tracker.srem(f'user:tracker:{user}', self.uuid)
            r_tracker.srem(f'user:tracker:{user}:{tracker_type}', self.uuid)
        elif level == 1:  # global
            r_tracker.srem('global:tracker', self.uuid)
            r_tracker.srem(f'global:tracker:{tracker_type}', self.uuid)
        elif level == 2:
            org = self.get_org()
            r_tracker.srem(f'org:tracker:{org}', self.uuid)
            r_tracker.srem(f'org:tracker:{org}:{tracker_type}', self.uuid)

        r_tracker.srem(f'all:tracker:{tracker_type}', tracked)
        # tracker - uuid map
        r_tracker.srem(f'all:tracker_uuid:{tracker_type}:{tracked}', self.uuid)
        r_tracker.srem('trackers:all', self.uuid)
        r_tracker.srem(f'trackers:all:{tracker_type}', self.uuid)
        ail_orgs.remove_obj_to_org(self.get_org(), 'tracker', self.uuid)
        # meta
        r_tracker.delete(f'tracker:{self.uuid}')
        trigger_trackers_refresh(tracker_type)


def create_tracker(tracker_type, to_track, org, user_id, level, description=None, filters={}, tags=[], mails=[], webhook=None, tracker_uuid=None):
    if not tracker_uuid:
        tracker_uuid = str(uuid.uuid4())
    tracker = Tracker(tracker_uuid)
    return tracker.create(tracker_type, to_track, org, user_id, level, description=description, filters=filters, tags=tags,
                          mails=mails, webhook=webhook)

def _re_create_tracker(tracker_type, tracker_uuid, to_track, org, user_id, level, description=None, filters={}, tags=[], mails=[], webhook=None, first_seen=None, last_seen=None):
    create_tracker(tracker_type, to_track, org, user_id, level, description=description, filters=filters,
                   tags=tags, mails=mails, webhook=webhook, tracker_uuid=tracker_uuid)

def get_trackers_types():
    return ['word', 'set', 'regex', 'typosquatting', 'yara']

def get_trackers():
    return r_tracker.smembers(f'trackers:all')

def get_trackers_by_type(tracker_type):
    return r_tracker.smembers(f'trackers:all:{tracker_type}')

def _get_tracked_by_obj_type(tracker_type, obj_type):
    return r_tracker.smembers(f'trackers:objs:{tracker_type}:{obj_type}')

def get_trackers_by_tracked_obj_type(tracker_type, obj_type, tracked):
    trackers_uuid = set()
    for res in r_tracker.smembers(f'trackers:uuid:{tracker_type}:{tracked}'):
        tracker_uuid, tracker_obj_type = res.split(':', 1)
        if tracker_obj_type == obj_type:
            trackers_uuid.add(tracker_uuid)
    return trackers_uuid

def get_trackers_by_tracked(tracker_type, tracked):
    return r_tracker.smembers(f'all:tracker_uuid:{tracker_type}:{tracked}')

def get_user_trackers_by_tracked(tracker_type, tracked, user_id):
    user_trackers = get_user_trackers(user_id, tracker_type=tracker_type)
    trackers_uuid = get_trackers_by_tracked(tracker_type, tracked)
    return trackers_uuid.intersection(user_trackers)

def get_trackers_tracked_by_type(tracker_type):
    return r_tracker.smembers(f'all:tracker:{tracker_type}')

def get_global_trackers(tracker_type=None):
    if tracker_type:
        return r_tracker.smembers(f'global:tracker:{tracker_type}')
    else:
        return r_tracker.smembers('global:tracker')

def get_user_trackers(user_id, tracker_type=None):
    if tracker_type:
        return r_tracker.smembers(f'user:tracker:{user_id}:{tracker_type}')
    else:
        return r_tracker.smembers(f'user:tracker:{user_id}')

def get_org_trackers(org, tracker_type=None):
    if tracker_type:
        return r_tracker.smembers(f'org:tracker:{org}:{tracker_type}')
    else:
        return r_tracker.smembers(f'org:tracker:{org}')

def get_nb_global_trackers(tracker_type=None):
    if tracker_type:
        return r_tracker.scard(f'global:tracker:{tracker_type}')
    else:
        return r_tracker.scard('global:tracker')

def get_nb_user_trackers(user_id, tracker_type=None):
    if tracker_type:
        return r_tracker.scard(f'user:tracker:{user_id}:{tracker_type}')
    else:
        return r_tracker.scard(f'user:tracker:{user_id}')

def get_nb_org_trackers(org, tracker_type=None):
    if tracker_type:
        return r_tracker.scard(f'org:tracker:{org}:{tracker_type}')
    else:
        return r_tracker.scard(f'org:tracker:{org}')


def get_user_trackers_meta(user_id, tracker_type=None):
    metas = []
    for tracker_uuid in get_user_trackers(user_id, tracker_type=tracker_type):
        tracker = Tracker(tracker_uuid)
        metas.append(tracker.get_meta(options={'description', 'mails', 'org', 'org_name', 'sparkline', 'tags'}))
    return metas

def get_global_trackers_meta(tracker_type=None):
    metas = []
    for tracker_uuid in get_global_trackers(tracker_type=tracker_type):
        tracker = Tracker(tracker_uuid)
        metas.append(tracker.get_meta(options={'description', 'mails', 'org', 'org_name', 'sparkline', 'tags'}))
    return metas

def get_org_trackers_meta(user_org, tracker_type=None):
    metas = []
    for tracker_uuid in get_org_trackers(user_org, tracker_type=tracker_type):
        tracker = Tracker(tracker_uuid)
        metas.append(tracker.get_meta(options={'description', 'mails', 'org', 'org_name', 'sparkline', 'tags'}))
    return metas

def get_users_trackers_meta(user_id):
    trackers = []
    for tracker_uuid in get_trackers():
        tracker = Tracker(tracker_uuid)
        if tracker.is_level_user():
            if tracker.get_user() != user_id:
                trackers.append(tracker.get_meta(options={'description', 'mails', 'org', 'org_name', 'sparkline', 'tags'}))
    return trackers

def get_orgs_trackers_meta(user_org):
    trackers = []
    for tracker_uuid in get_trackers():
        tracker = Tracker(tracker_uuid)
        if tracker.is_level_org():
            if tracker.get_org() != user_org:
                trackers.append(tracker.get_meta(options={'description', 'mails', 'org', 'org_name', 'sparkline', 'tags'}))
    return trackers

def get_trackers_graph_by_day(l_trackers, num_day=31, date_from=None, date_to=None):
    if date_from and date_to:
        date_range = Date.substract_date(date_from, date_to)
    else:
        date_range = Date.get_date_range(num_day)
    list_tracker_stats = []
    for tracker_uuid in l_trackers:
        dict_tracker_data = []
        tracker = Tracker(tracker_uuid)
        for date_day in date_range:
            nb_seen_this_day = tracker.get_nb_objs_by_date(date_day)
            if nb_seen_this_day is None:
                nb_seen_this_day = 0
            dict_tracker_data.append({"date": date_day, "value": int(nb_seen_this_day)})
        list_tracker_stats.append({"name": tracker.get_tracked(), "Data": dict_tracker_data})
    return list_tracker_stats

def get_trackers_dashboard(user_org, user_id):
    trackers = []
    for raw in r_tracker.lrange('trackers:dashboard', 0, -1):
        tracker_uuid, timestamp, obj_gid = raw.split(':', 2)
        tracker = Tracker(tracker_uuid)
        if not tracker.check_level(user_org, user_id):
            continue
        meta = tracker.get_meta(options={'description', 'tags'})
        if not meta.get('type'):
            meta['type'] = 'Tracker DELETED'
        timestamp = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        meta['timestamp'] = timestamp
        meta['obj'] = obj_gid
        meta['tags'] = list(meta['tags'])
        trackers.append(meta)
    return trackers

def get_user_dashboard(user_id):  # TODO SORT + REMOVE OLDER ROWS (trim)
    trackers = []
    for raw in r_tracker.lrange(f'trackers:user:{user_id}', 0, -1):
        tracker_uuid, timestamp, obj_gid = raw.split(':', 2)
        tracker = Tracker(tracker_uuid)
        meta = tracker.get_meta(options={'tags'})
        timestamp = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        meta['timestamp'] = timestamp
        meta['obj'] = obj_gid
        trackers.append(meta)

    return trackers

def get_trackers_stats(user_org, user_id):
    stats = {'all': 0}
    for tracker_type in get_trackers_types():
        nb_global = get_nb_global_trackers(tracker_type=tracker_type)
        nb_user = get_nb_user_trackers(user_id, tracker_type=tracker_type)
        nb_org = get_nb_org_trackers(user_org, tracker_type=tracker_type)
        stats[tracker_type] = nb_global + nb_user + nb_org
        stats['all'] += nb_global + nb_user + nb_org
    return stats


## Cache ##
# TODO API: Check Tracker type
def trigger_trackers_refresh(tracker_type):
    r_cache.set(f'tracker:refresh:{tracker_type}', time.time())

def get_tracker_last_updated_by_type(tracker_type):
    epoch_update = r_cache.get(f'tracker:refresh:{tracker_type}')
    if not epoch_update:
        epoch_update = 0
    return float(epoch_update)
# - Cache - #

## Objects ##

def is_obj_tracked(obj_type, subtype, obj_id):
    return r_tracker.exists(f'obj:trackers:{obj_type}:{subtype}:{obj_id}')

def get_obj_trackers(obj_type, subtype, obj_id):
    return r_tracker.smembers(f'obj:trackers:{obj_type}:{subtype}:{obj_id}')

def delete_obj_trackers(obj_type, subtype, obj_id):
    for tracker_uuid in get_obj_trackers(obj_type, subtype, obj_id):
        tracker = Tracker(tracker_uuid)
        tracker.remove(obj_type, subtype, obj_id)

######################
#### TRACKERS ACL ####

## LEVEL ##
def is_tracker_global_level(tracker_uuid):
    return int(r_tracker.hget(f'tracker:{tracker_uuid}', 'level')) == 1

def is_tracked_in_global_level(tracked, tracker_type):
    for tracker_uuid in get_trackers_by_tracked(tracker_type, tracked):
        tracker = Tracker(tracker_uuid)
        if tracker.is_level_global():
            return True
    return False

def is_tracked_in_user_level(tracked, tracker_type, user_id):
    trackers_uuid = get_user_trackers_by_tracked(tracker_type, tracked, user_id)
    if trackers_uuid:
        return True
    else:
        return False

## API ##
def api_check_tracker_uuid(tracker_uuid):
    if not is_valid_uuid_v4(tracker_uuid):
        return {"status": "error", "reason": "Invalid uuid"}, 400
    if not r_tracker.exists(f'tracker:{tracker_uuid}'):
        return {"status": "error", "reason": "Unknown uuid"}, 404
    return None

def api_check_tracker_acl(tracker_uuid, user_org, user_id, user_role, action):
    res = api_check_tracker_uuid(tracker_uuid)
    if res:
        return res
    tracker = Tracker(tracker_uuid)
    if not ail_orgs.check_obj_access_acl(tracker, user_org, user_id, user_role, action):
        return {"status": "error", "reason": "Access Denied"}, 403

def api_is_allowed_to_edit_tracker_level(tracker_uuid, user_org, user_id, user_role, new_level):
    tracker = Tracker(tracker_uuid)
    if not ail_orgs.check_acl_edit_level(tracker, user_org, user_id, user_role, new_level):
        return {"status": "error", "reason": "Access Denied - Tracker level"}, 403

## --ACL-- ##

#### FIX DB #### TODO ###################################################################
def fix_tracker_stats_per_day(tracker_uuid):
    tracker = Tracker(tracker_uuid)
    date_from = tracker.get_date()
    date_to = Date.get_today_date_str()
    # delete stats
    r_tracker.delete(f'tracker:stat:{tracker_uuid}')
    r_tracker.hdel(f'tracker:{tracker_uuid}', 'first_seen')
    r_tracker.hdel(f'tracker:{tracker_uuid}', 'last_seen')
    # create new stats
    for date_day in Date.substract_date(date_from, date_to):
        date_day = int(date_day)

        nb_items = r_tracker.scard(f'tracker:item:{tracker_uuid}:{date_day}')
        if nb_items:
            r_tracker.zincrby(f'tracker:stat:{tracker_uuid}', nb_items, int(date_day))

            # update first_seen/last_seen
            tracker.update_daterange(date_day)

def fix_tracker_item_link(tracker_uuid):
    tracker = Tracker(tracker_uuid)
    date_from = tracker.get_first_seen()
    date_to = tracker.get_last_seen()

    if date_from and date_to:
        for date_day in Date.substract_date(date_from, date_to):
            l_items = r_tracker.smembers(f'tracker:item:{tracker_uuid}:{date_day}')
            for item_id in l_items:
                r_tracker.sadd(f'obj:trackers:item:{item_id}', tracker_uuid)

def fix_all_tracker_uuid_list():
    r_tracker.delete(f'trackers:all')
    for tracker_type in get_trackers_types():
        r_tracker.delete(f'trackers:all:{tracker_type}')
        for tracked in get_trackers_tracked_by_type(tracker_type):
            l_tracker_uuid = get_trackers_by_tracked(tracker_type, tracked)
            for tracker_uuid in l_tracker_uuid:
                r_tracker.sadd(f'trackers:all', tracker_uuid)
                r_tracker.sadd(f'trackers:all:{tracker_type}', tracker_uuid)

## --FIX DB-- ##

#### CREATE TRACKER ####
def api_validate_tracker_to_add(to_track, tracker_type, nb_words=1):
    if tracker_type == 'regex':
        if not is_valid_regex(to_track):
            return {"status": "error", "reason": "Invalid regex"}, 400
    elif tracker_type == 'word' or tracker_type == 'set':
        # force lowercase
        to_track = to_track.lower()
        word_set = set(to_track)
        set_inter = word_set.intersection(get_special_characters())
        if set_inter:
            return {"status": "error",
                    "reason": f'special character(s) not allowed: {set_inter}',
                    "message": "Please use a python regex or remove all special characters"}, 400
        words = to_track.split()
        # not a word
        if tracker_type == 'word' and len(words) > 1:
            tracker_type = 'set'

        # output format: tracker1,tracker2,tracker3;2
        if tracker_type == 'set':
            try:
                nb_words = int(nb_words)
            except TypeError:
                nb_words = 1
            if nb_words == 0:
                nb_words = 1

            words_set = set(words)
            words_set = sorted(words_set)
            if nb_words > len(words_set):
                nb_words = len(words_set)

            to_track = ",".join(words_set)
            to_track = f"{to_track};{nb_words}"
    elif tracker_type == 'typosquatting':
        to_track = to_track.lower()
        # Take only the first term
        domain = to_track.split(" ")
        if len(domain) > 1:
            return {"status": "error", "reason": "Only one domain is accepted at a time"}, 400
        if "." not in to_track:
            return {"status": "error", "reason": "Invalid domain name"}, 400

    elif tracker_type == 'yara_custom':
        if not is_valid_yara_rule(to_track):
            return {"status": "error", "reason": "Invalid custom Yara Rule"}, 400
    elif tracker_type == 'yara_default':
        if not is_valid_default_yara_rule(to_track):
            return {"status": "error", "reason": "The Yara Rule doesn't exist"}, 400
    else:
        return {"status": "error", "reason": "Incorrect type"}, 400
    return {"status": "success", "tracked": to_track, "type": tracker_type}, 200

def api_add_tracker(dict_input, org, user_id):
    to_track = dict_input.get('tracked', None)
    if not to_track:
        return {"status": "error", "reason": "Tracker not provided"}, 400
    tracker_type = dict_input.get('type', None)
    if not tracker_type:
        return {"status": "error", "reason": "Tracker type not provided"}, 400
    nb_words = dict_input.get('nb_words', 1)
    description = dict_input.get('description', '')
    description = escape(description)
    webhook = dict_input.get('webhook', '')
    webhook = escape(webhook)
    res = api_validate_tracker_to_add(to_track, tracker_type, nb_words=nb_words)
    if res[1] != 200:
        return res
    to_track = res[0]['tracked']
    tracker_type = res[0]['type']

    tags = dict_input.get('tags', [])
    mails = dict_input.get('mails', [])
    res = verify_mail_list(mails)
    if res:
        return res

    # Filters # TODO MOVE ME
    filters = dict_input.get('filters', {})
    if filters:
        if filters.keys() == set(get_objects_tracked()) and set(filters['pgp'].get('subtypes', [])) == {'mail', 'name'}:
            filters = {}
        for obj_type in filters:
            if obj_type not in get_objects_tracked():
                return {"status": "error", "reason": "Invalid Tracker Object type"}, 400

            if obj_type == 'pgp':
                if set(filters['pgp'].get('subtypes', [])) == {'mail', 'name'}:
                    filters['pgp'].pop('subtypes')

            for filter_name in filters[obj_type]:
                if filter_name not in {'mimetypes', 'sources', 'subtypes'}:
                    return {"status": "error", "reason": "Invalid Filter"}, 400
                elif filter_name == 'mimetypes': # TODO
                    pass
                elif filter_name == 'sources':
                    if obj_type == 'item':
                        res = item_basic.verify_sources_list(filters['item']['sources'])
                        if res:
                            return res
                    elif obj_type == 'message':
                        pass
                        # TODO Check IF not at the same time in sources + excludes
                    else:
                        return {"status": "error", "reason": "Invalid Filter sources"}, 400
                elif filter_name == 'subtypes':
                    obj_subtypes = set(get_object_all_subtypes(obj_type))
                    for subtype in filters[obj_type]['subtypes']:
                        if subtype not in obj_subtypes:
                            return {"status": "error", "reason": "Invalid Tracker Object subtype"}, 400

    level = dict_input.get('level', 1)
    try:
        level = int(level)
    except TypeError:
        level = 1
    if level not in range(0, 3):
        level = 1

    tracker_uuid = create_tracker(tracker_type, to_track, org, user_id, level, description=description, filters=filters,
                                  tags=tags, mails=mails, webhook=webhook)

    return {'tracked': to_track, 'type': tracker_type, 'uuid': tracker_uuid}, 200

def api_edit_tracker(dict_input, user_org, user_id, user_role):
    tracker_uuid = dict_input.get('uuid')
    res = api_check_tracker_acl(tracker_uuid, user_org, user_id, user_role, 'edit')
    if res:
        return res

    tracker = Tracker(tracker_uuid)

    to_track = dict_input.get('tracked', None)
    if not to_track:
        return {"status": "error", "reason": "Tracker not provided"}, 400
    tracker_type = dict_input.get('type', None)
    if not tracker_type:
        return {"status": "error", "reason": "Tracker type not provided"}, 400

    level = dict_input.get('level', 1)
    try:
        level = int(level)
    except TypeError:
        level = 1
    if level not in range(0, 3):
        level = 1
    res = api_is_allowed_to_edit_tracker_level(tracker_uuid, user_org, user_id, user_role, level)
    if res:
        return res

    nb_words = dict_input.get('nb_words', 1)
    description = dict_input.get('description', '')
    description = escape(description)
    webhook = dict_input.get('webhook', '')
    webhook = escape(webhook)
    res = api_validate_tracker_to_add(to_track, tracker_type, nb_words=nb_words)
    if res[1] != 200:
        return res
    to_track = res[0]['tracked']
    tracker_type = res[0]['type']

    tags = dict_input.get('tags', [])
    mails = dict_input.get('mails', [])
    res = verify_mail_list(mails)
    if res:
        return res

    # Filters # TODO MOVE ME
    filters = dict_input.get('filters', {})
    if filters:
        if filters.keys() == set(get_objects_tracked()) and set(filters['pgp'].get('subtypes', [])) == {'mail', 'name'}:
            if not filters['decoded'] and not filters['item']:
                filters = {}
        for obj_type in filters:
            if obj_type not in get_objects_tracked():
                return {"status": "error", "reason": "Invalid Tracker Object type"}, 400

            if obj_type == 'pgp':
                if set(filters['pgp'].get('subtypes', [])) == {'mail', 'name'}:
                    filters['pgp'].pop('subtypes')

            for filter_name in filters[obj_type]:
                if filter_name not in {'mimetypes', 'sources', 'subtypes'}:
                    return {"status": "error", "reason": "Invalid Filter"}, 400
                elif filter_name == 'mimetypes':  # TODO
                    pass
                elif filter_name == 'sources':
                    if obj_type == 'item':
                        res = item_basic.verify_sources_list(filters['item']['sources'])
                        if res:
                            return res
                    else:
                        return {"status": "error", "reason": "Invalid Filter sources"}, 400
                elif filter_name == 'subtypes':
                    obj_subtypes = set(get_object_all_subtypes(obj_type))
                    for subtype in filters[obj_type]['subtypes']:
                        if subtype not in obj_subtypes:
                            return {"status": "error", "reason": "Invalid Tracker Object subtype"}, 400

    tracker.edit(tracker_type, to_track, level, user_org, description=description, filters=filters,
                 tags=tags, mails=mails, webhook=webhook)
    return {'tracked': to_track, 'type': tracker_type, 'uuid': tracker_uuid}, 200


def api_delete_tracker(data, user_org, user_id, user_role):
    tracker_uuid = data.get('uuid')
    res = api_check_tracker_acl(tracker_uuid, user_org, user_id, user_role, 'delete')
    if res:
        return res

    tracker = Tracker(tracker_uuid)
    return tracker.delete(), 200

def api_tracker_add_object(data, user_org, user_id, user_role):
    tracker_uuid = data.get('uuid')
    res = api_check_tracker_acl(tracker_uuid, user_org, user_id, user_role, 'edit')
    if res:
        return res
    tracker = Tracker(tracker_uuid)
    object_gid = data.get('gid')
    date = data.get('date')
    if date:
        if not Date.validate_str_date(date):
            date = None
    try:
        obj_type, subtype, obj_id = object_gid.split(':', 2)
    except (AttributeError, IndexError):
        return {"status": "error", "reason": "Invalid Object"}, 400
    return tracker.add(obj_type, subtype, obj_id, date=date), 200

def api_tracker_remove_object(data, user_org, user_id, user_role):
    tracker_uuid = data.get('uuid')
    res = api_check_tracker_acl(tracker_uuid, user_org, user_id, user_role, 'edit')
    if res:
        return res

    tracker = Tracker(tracker_uuid)
    object_gid = data.get('gid')
    try:
        obj_type, subtype, obj_id = object_gid.split(':', 2)
    except (AttributeError, IndexError):
        return {"status": "error", "reason": "Invalid Object"}, 400
    return tracker.remove(obj_type, subtype, obj_id), 200

## -- CREATE TRACKER -- ##

####################
#### WORD - SET ####

def get_tracked_words():
    to_track = {}
    for obj_type in get_objects_tracked():
        to_track[obj_type] = _get_tracked_by_obj_type('word', obj_type)
    return to_track

def get_tracked_sets():
    to_track = {}
    for obj_type in get_objects_tracked():
        to_track[obj_type] = []
        for tracked in _get_tracked_by_obj_type('set', obj_type):
            res = tracked.split(';')
            nb_words = int(res[1])
            words_set = res[0].split(',')
            to_track[obj_type].append({'words': words_set, 'nb': nb_words, 'tracked': tracked})
    return to_track

def get_text_word_frequency(content, filtering=True):
    content = content.lower()
    words_dict = defaultdict(int)

    if filtering:
        if TOKENIZER is None:
            init_tokenizer()
        blob = TextBlob(content, tokenizer=TOKENIZER)
    else:
        blob = TextBlob(content)
    for word in blob.tokens:
        words_dict[word] += 1
    return words_dict

###############
#### REGEX ####

def get_tracked_regexs():
    to_track = {}
    for obj_type in get_objects_tracked():
        to_track[obj_type] = []
        for tracked in _get_tracked_by_obj_type('regex', obj_type):
            to_track[obj_type].append({'regex': re.compile(tracked), 'tracked': tracked})
    return to_track

########################
#### TYPO SQUATTING ####

def get_tracked_typosquatting_domains(tracked):
    return r_tracker.smembers(f'tracker:typosquatting:{tracked}')

def get_tracked_typosquatting():
    to_track = {}
    for obj_type in get_objects_tracked():
        to_track[obj_type] = []
        for tracked in _get_tracked_by_obj_type('typosquatting', obj_type):
            to_track[obj_type].append({'domains': get_tracked_typosquatting_domains(tracked), 'tracked': tracked})
    return to_track

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
    yara_files = r_tracker.smembers('all:tracker:yara')
    if not yara_files:
        yara_files = []
    if filter_disabled:
        pass
    return yara_files

def get_tracked_yara_rules():
    to_track = {}
    for obj_type in get_objects_tracked():
        rules = {}
        for tracked in _get_tracked_by_obj_type('yara', obj_type):
            rule = os.path.join(get_yara_rules_dir(), tracked)
            if not os.path.exists(rule):
                logger.critical(f"Yara rule don't exists {tracked} : {obj_type}")
            else:
                rules[tracked] = rule
        to_track[obj_type] = yara.compile(filepaths=rules)
    return to_track

def reload_yara_rules():
    yara_files = get_all_tracked_yara_files()
    # {uuid: filename}
    rule_dict = {}
    for yar_path in yara_files:
        for tracker_uuid in get_trackers_by_tracked('yara', yar_path):
            rule_dict[tracker_uuid] = os.path.join(get_yara_rules_dir(), yar_path)
    for tracker_uuid in rule_dict:
        if not os.path.isfile(rule_dict[tracker_uuid]):
            # TODO IGNORE + LOGS
            raise Exception(f"Error: {rule_dict[tracker_uuid]} doesn't exists")
    rules = yara.compile(filepaths=rule_dict)
    return rules

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
        if not tracker_uuid:
            tracker_uuid = str(uuid.uuid4())
        filename = os.path.join('custom-rules', tracker_uuid + '.yar')
        with open(os.path.join(get_yara_rules_dir(), filename), 'w') as f:
            f.write(str(yara_rule))
    elif yara_rule_type == 'yara_default':
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
        return ''  # # TODO: throw exception

    with open(filename, 'r') as f:
        rule_content = f.read()
    return rule_content

def api_get_default_rule_content(default_yara_rule):
    yara_dir = get_yara_rules_default_dir()
    filename = os.path.join(yara_dir, default_yara_rule)
    filename = os.path.realpath(filename)
    if not os.path.commonprefix([filename, yara_dir]) == yara_dir:
        return {'status': 'error', 'reason': 'file traversal detected'}, 400

    if not os.path.isfile(filename):
        return {'status': 'error', 'reason': 'yara rule not found'}, 400

    with open(filename, 'r') as f:
        rule_content = f.read()
    return {'rule_name': default_yara_rule, 'content': rule_content}, 200


def get_yara_rule_content_restapi(request_dict):
    rule_name = request_dict.get('rule_name', None)
    if not request_dict:
        return {'status': 'error', 'reason': 'Malformed JSON'}, 400
    if not rule_name:
        return {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400
    yara_dir = get_yara_rules_dir()
    filename = os.path.join(yara_dir, rule_name)
    filename = os.path.realpath(filename)
    if not os.path.commonprefix([filename, yara_dir]) == yara_dir:
        return {'status': 'error', 'reason': 'File Path Traversal'}, 400
    if not os.path.isfile(filename):
        return {'status': 'error', 'reason': 'yara rule not found'}, 400
    with open(filename, 'r') as f:
        rule_content = f.read()
    rule_content = base64.b64encode((rule_content.encode('utf-8'))).decode('UTF-8')
    return {'status': 'success', 'content': rule_content}, 200

## -- YARA -- ##

######################
#### RETRO - HUNT ####

# state: pending/running/completed/paused

class RetroHunt:

    def __init__(self, task_uuid):
        self.uuid = task_uuid

    def exists(self):
        return r_tracker.exists(f'retro_hunt:{self.uuid}')

    def _get_field(self, field):
        return r_tracker.hget(f'retro_hunt:{self.uuid}', field)

    def _set_field(self, field, value):
        return r_tracker.hset(f'retro_hunt:{self.uuid}', field, value)

    ## LEVEL ##

    def get_level(self):
        level = int(self._get_field('level'))
        if not level:
            level = 1
        return int(level)

    def set_level(self, level, org_uuid):
        if level == 1:  # global
            r_tracker.sadd('retro_hunts', self.uuid)
        elif level == 2:  # org only
            self.add_to_org(org_uuid)
        self._set_field('level', level)

    def delete_level(self, level=None):
        if not level:
            level = self.get_level()
        if level == 1:
            r_tracker.srem('retro_hunts', self.uuid)
        # Org
        elif level == 2:
            ail_orgs.remove_obj_to_org(self.get_org(), 'retro_hunt', self.uuid)

    def reset_level(self, old_level, new_level, new_org_uuid):
        self.delete_level(old_level)
        self.set_level(new_level, new_org_uuid)

    def check_level(self, user_org):
        level = self.get_level()
        if level == 1:
            return True
        elif level == 2:
            return self.get_org() == user_org

    ## ORG ##

    def get_creator_org(self):
        return self._get_field('creator_org')

    def get_org(self):
        return self._get_field('org')

    def add_to_org(self, org_uuid):
        self._set_field('org', org_uuid)
        ail_orgs.add_obj_to_org(org_uuid, 'retro_hunt', self.uuid)

    ## -ORG- ##

    def get_creator(self):
        return self._get_field('creator')

    def get_date(self):
        return self._get_field('date')

    def get_last_analyzed(self):
        return self._get_field('last')

    def set_last_analyzed(self, obj_type, subtype, obj_id):
        return self._set_field('last', f'{obj_type}:{subtype}:{obj_id}')

    def get_last_analyzed_cache(self):
        r_cache.hget(f'retro_hunt:task:{self.uuid}', 'obj')

    def set_last_analyzed_cache(self, obj_type, subtype, obj_id):
        r_cache.hset(f'retro_hunt:task:{self.uuid}', 'obj', f'{obj_type}:{subtype}:{obj_id}')

    def get_name(self):
        return self._get_field('name')

    def get_description(self):
        return self._get_field('description')

    def get_timeout(self):
        res = self._get_field('timeout')
        if res:
            return int(res)
        else:
            return 30  # # TODO: FIXME use instance limit

    def get_filters(self):
        filters = self._get_field('filters')
        if not filters:
            return {}
        else:
            return json.loads(filters)

    def set_filters(self, filters):
        if filters:
            self._set_field('filters', json.dumps(filters))

    def get_tags(self):
        return r_tracker.smembers(f'retro_hunt:tags:{self.uuid}')

    def get_mails(self):
        return r_tracker.smembers(f'retro_hunt:mails:{self.uuid}')

    def get_state(self):
        return self._get_field('state')

    def _set_state(self, new_state):
        curr_state = self.get_state()
        if curr_state:
            r_tracker.srem(f'retro_hunt:task:{curr_state}', self.uuid)
        r_tracker.sadd(f'retro_hunts:{new_state}', self.uuid)
        self._set_field('state', new_state)

    def get_rule(self, r_compile=False):
        rule = self._get_field('rule')
        if r_compile:
            rule = os.path.join(get_yara_rules_dir(), rule)
            rule_dict = {self.uuid: os.path.join(get_yara_rules_dir(), rule)}
            rule = yara.compile(filepaths=rule_dict)
        return rule

    # add timeout ?
    def get_meta(self, options=set()):
        meta = {'uuid': self.uuid,
                'name': self.get_name(),
                'state': self.get_state(),
                'rule': self.get_rule(),
                }
        if 'creator' in options:
            meta['creator'] = self.get_creator()
        if 'date' in options:
            meta['date'] = self.get_date()
        if 'description' in options:
            meta['description'] = self.get_description()
        if 'level' in options:
            meta['level'] = self.get_level()
        if 'mails' in options:
            meta['mails'] = self.get_mails()
        if 'nb_match' in options:
            meta['nb_match'] = self.get_nb_match()
        if 'nb_objs' in options:
            meta['nb_objs'] = self.get_nb_objs()
        if 'org' in options:
            meta['org'] = self.get_org()
            if 'org_name' in options:
                meta['org_name'] = ail_orgs.Organisation(self.get_org()).get_name()
        if 'progress' in options:
            meta['progress'] = self.get_progress()
        if 'filters' in options:
            meta['filters'] = self.get_filters()
        if 'tags' in options:
            meta['tags'] = self.get_tags()
        return meta

    def is_paused(self):
        return r_tracker.sismember('retro_hunts:paused', self.uuid)

    def to_pause(self):
        to_pause = r_cache.hget(f'retro_hunt:{self.uuid}', 'pause')
        if to_pause:
            return True
        else:
            return False

    def pause(self):
        self._set_state('paused')
        r_cache.hset(f'retro_hunt:{self.uuid}', 'pause', time.time())
        self.clear_cache()

    def resume(self):
        r_cache.hdel(f'retro_hunt:{self.uuid}', 'pause')
        self._set_state('pending')

    def is_running(self):
        return r_tracker.sismember('retro_hunts:running', self.uuid)

    def run(self): # TODO ADD MORE CHECK
        self._set_state('running')

    def complete(self):
        self._set_state('completed')
        self.clear_cache()
        r_tracker.hdel(f'retro_hunt:{self.uuid}', 'last')

    def get_progress(self):
        if self.get_state() == 'completed':
            progress = 100
        else:
            progress = r_cache.hget(f'retro_hunt:{self.uuid}', 'progress')
            if not progress:
                progress = self._get_field('progress')
        return progress

    def set_progress(self, progress):
        res = r_cache.hset(f'retro_hunt:{self.uuid}', 'progress', progress)
        if res:
            self._set_field('progress', progress)

    def get_nb_match(self):
        return self._get_field('nb_match')

    def _incr_nb_match(self):
        r_tracker.hincrby(f'retro_hunt:{self.uuid}', 'nb_match', 1)

    def _decr_nb_match(self):
        r_tracker.hincrby(f'retro_hunt:{self.uuid}', 'nb_match', -1)

    def _set_nb_match(self, nb_match):
        self._set_field('nb_match', nb_match)

    def clear_cache(self):
        r_cache.delete(f'retro_hunt:{self.uuid}')

    def get_nb_objs_by_type(self, obj_type):
        return r_tracker.scard(f'retro_hunt:objs:{self.uuid}:{obj_type}')

    def get_objs_by_type(self, obj_type):
        return r_tracker.smembers(f'retro_hunt:objs:{self.uuid}:{obj_type}')

    def get_nb_objs(self):
        objs = {}
        for obj_type in get_objects_retro_hunted():
            nb = self.get_nb_objs_by_type(obj_type)
            if nb:
                objs[obj_type] = nb
        return objs

    def get_objs(self):
        objs = []
        for obj_type in get_objects_retro_hunted():
            for obj in self.get_objs_by_type(obj_type):
                subtype, obj_id = obj.split(':', 1)
                objs.append((obj_type, subtype, obj_id))
        return objs

    def add(self, obj_type, subtype, obj_id):
        # match by object type:
        r_tracker.sadd(f'retro_hunt:objs:{self.uuid}:{obj_type}', f'{subtype}:{obj_id}')
        # MAP object -> retro hunt
        r_tracker.sadd(f'obj:retro_hunts:{obj_type}:{subtype}:{obj_id}', self.uuid)
        self._incr_nb_match()

    def remove(self, obj_type, subtype, obj_id):
        # match by object type:
        r_tracker.srem(f'retro_hunt:objs:{self.uuid}:{obj_type}', f'{subtype}:{obj_id}')
        # MAP object -> retro hunt
        r_tracker.srem(f'obj:retro_hunts:{obj_type}:{subtype}:{obj_id}', self.uuid)
        self._decr_nb_match()

    def create(self, org_uuid, user_id, level, name, rule, description=None, filters=[], mails=[], tags=[], timeout=30, state='pending'):
        if self.exists():
            raise Exception('Error: Retro Hunt Task already exists')

        self._set_field('name', escape(name))

        self._set_field('rule', rule)

        self._set_field('date', datetime.date.today().strftime("%Y%m%d"))
        self._set_field('name', escape(name))
        self._set_field('creator_org', org_uuid)
        self._set_field('creator', user_id)
        if description:
            self._set_field('description', description)
        if timeout:
            self._set_field('timeout', int(timeout))
        for tag in tags:
            # tag = escape(tag)
            r_tracker.sadd(f'retro_hunt:tags:{self.uuid}', tag)
            Tag.create_custom_tag(tag)
        for mail in mails:
            r_tracker.sadd(f'retro_hunt:mails:{self.uuid}', escape(mail))

        if filters:
            self.set_filters(filters)

        self.set_level(level, org_uuid)
        r_tracker.sadd('retro_hunts:all', self.uuid)

        # add to pending tasks
        if state not in ('pending', 'completed', 'paused'):
            state = 'pending'
        self._set_state(state)

    def delete_objs(self):
        for obj_type in get_objects_retro_hunted():
            for obj in self.get_objs_by_type(obj_type):
                subtype, obj_id = obj.split(':', 1)
                # match by object type:
                r_tracker.srem(f'retro_hunt:objs:{self.uuid}:{obj_type}', f'{subtype}:{obj_id}')
                # MAP object -> retro hunt
                r_tracker.srem(f'obj:retro_hunts:{obj_type}:{subtype}:{obj_id}', self.uuid)

    def delete(self):
        if self.is_running() and self.get_state() not in ['completed', 'paused']:
            self.pause()
            return None

        self.delete_objs()

        # Delete custom rule
        rule = self.get_rule()
        if not is_default_yara_rule(rule):
            filepath = get_yara_rule_file_by_tracker_name(rule)
            if filepath:
                os.remove(filepath)

        self.delete_level()

        r_tracker.srem('retro_hunts:pending', self.uuid)
        r_tracker.delete(f'retro_hunts:{self.uuid}')
        r_tracker.delete(f'retro_hunt:tags:{self.uuid}')
        r_tracker.delete(f'retro_hunt:mails:{self.uuid}')

        for obj in self.get_objs():
            self.remove(obj[0], obj[1], obj[2])

        r_tracker.srem('retro_hunts:all', self.uuid)
        r_tracker.srem('retro_hunts:pending', self.uuid)
        r_tracker.srem('retro_hunts:paused', self.uuid)
        r_tracker.srem('retro_hunts:completed', self.uuid)

        self.clear_cache()
        return self.uuid

def create_retro_hunt(user_org, user_id, level, name, rule_type, rule, description=None, filters=[], mails=[], tags=[], timeout=30, state='pending', task_uuid=None):
    if not task_uuid:
        task_uuid = str(uuid.uuid4())
    retro_hunt = RetroHunt(task_uuid)
    # rule_type: yara_default - yara custom
    rule = save_yara_rule(rule_type, rule, tracker_uuid=retro_hunt.uuid)
    retro_hunt.create(user_org, user_id, level, name, rule, description=description, mails=mails, tags=tags,
                      timeout=timeout, filters=filters, state=state)
    return retro_hunt.uuid

# TODO
# def _re_create_retro_hunt_task(name, rule, date, date_from, date_to, creator, sources, tags, mails, timeout, description, task_uuid, state='pending', nb_match=0, last_id=None):
#     retro_hunt = RetroHunt(task_uuid)
#     retro_hunt.create(name, rule, date_from, date_to, creator, description=description, mails=mails, tags=tags,
#                       timeout=timeout, sources=sources, state=state)
#     if last_id:
#         set_retro_hunt_last_analyzed(task_uuid, last_id)
#     retro_hunt._set_nb_match(nb_match)
#     retro_hunt._set_field('date', date)

## ? ? ?
# set tags
# set mails
# limit mail

# SET Retro Hunts

def get_all_retro_hunt_tasks():
    return r_tracker.smembers('retro_hunts:all')

def get_retro_hunts_global():
    return r_tracker.smembers('retro_hunts')

def get_retro_hunts_org(org_uuid):
    return ail_orgs.get_org_objs_by_type(org_uuid, 'retro_hunt')

def get_retro_hunts_orgs():
    retros = []
    for retro_uuid in get_all_retro_hunt_tasks():
        retro = RetroHunt(retro_uuid)
        if retro.get_level() == 2:
            retros.append(retro_uuid)
    return retros

def get_retro_hunt_pending_tasks():
    return r_tracker.smembers('retro_hunts:pending')

def get_retro_hunt_running_tasks():
    return r_tracker.smembers('retro_hunts:running')

def get_retro_hunt_paused_tasks():
    return r_tracker.smembers('retro_hunts:paused')

def get_retro_hunt_completed_tasks():
    return r_tracker.smembers('retro_hunts:completed')

## Change STATES ##

def get_retro_hunt_task_to_start():
    task_uuid = r_tracker.spop('retro_hunts:pending')
    if task_uuid:
        retro_hunt = RetroHunt(task_uuid)
        retro_hunt.run()
    return task_uuid

## Metadata ##

def get_retro_hunt_metas(trackers_uuid):
    tasks = []
    for task_uuid in trackers_uuid:
        retro_hunt = RetroHunt(task_uuid)
        tasks.append(retro_hunt.get_meta(options={'date', 'progress', 'org', 'org_name', 'nb_match', 'tags'}))
    return tasks

## Objects ##

def is_obj_retro_hunted(obj_type, subtype, obj_id):
    return r_tracker.exists(f'obj:retro_hunts:{obj_type}:{subtype}:{obj_id}')

def get_obj_retro_hunts(obj_type, subtype, obj_id):
    return r_tracker.smembers(f'obj:retro_hunts:{obj_type}:{subtype}:{obj_id}')

def delete_obj_retro_hunts(obj_type, subtype, obj_id):
    for retro_uuid in get_obj_retro_hunts(obj_type, subtype, obj_id):
        retro_hunt = RetroHunt(retro_uuid)
        retro_hunt.remove(obj_type, subtype, obj_id)

####  ACL  ####

def api_check_retro_hunt_acl(retro_hunt, user_org, user_id, user_role, action):
    if not ail_orgs.check_obj_access_acl(retro_hunt, user_org, user_id, user_role, action):
        return {"status": "error", "reason": "Access Denied"}, 403

# TODO
def api_is_allowed_to_edit_retro_hunt_level(retro_hunt, user_org, user_id, user_role, new_level):
    if not ail_orgs.check_acl_edit_level(retro_hunt, user_org, user_id, user_role, new_level):
        return {"status": "error", "reason": "Access Denied - Tracker level"}, 403

####  API  ####

def api_check_retro_hunt_task_uuid(task_uuid):
    if not is_valid_uuid_v4(task_uuid):
        return {"status": "error", "reason": "Invalid uuid"}, 400
    retro_hunt = RetroHunt(task_uuid)
    if not retro_hunt.exists():
        return {"status": "error", "reason": "Unknown uuid"}, 404
    return None

def api_pause_retro_hunt_task(user_org, user_id, user_role, task_uuid):
    res = api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return res
    retro_hunt = RetroHunt(task_uuid)
    res = api_check_retro_hunt_acl(retro_hunt, user_org, user_id, user_role, 'edit')
    if res:
        return res
    task_state = retro_hunt.get_state()
    if task_state not in ['pending', 'running']:
        return {"status": "error", "reason": f"Task {task_uuid} not paused, current state: {task_state}"}, 400
    retro_hunt.pause()
    return task_uuid, 200

def api_resume_retro_hunt_task(user_org, user_id, user_role, task_uuid):
    res = api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return res
    retro_hunt = RetroHunt(task_uuid)
    res = api_check_retro_hunt_acl(retro_hunt, user_org, user_id, user_role, 'edit')
    if res:
        return res
    if not retro_hunt.is_paused():
        return {"status": "error",
                "reason": f"Task {task_uuid} not paused, current state: {retro_hunt.get_state()}"}, 400
    retro_hunt.resume()
    return task_uuid, 200

def api_validate_rule_to_add(rule, rule_type):
    if rule_type == 'yara_custom':
        if not is_valid_yara_rule(rule):
            return {"status": "error", "reason": "Invalid custom Yara Rule"}, 400
    elif rule_type == 'yara_default':
        if not is_valid_default_yara_rule(rule):
            return {"status": "error", "reason": "The Yara Rule doesn't exist"}, 400
    else:
        return {"status": "error", "reason": "Incorrect type"}, 400
    return {"status": "success", "rule": rule, "type": rule_type}, 200

def api_create_retro_hunt_task(dict_input, user_org, user_id):
    # # TODO: API: check mandatory arg
    # # TODO: TIMEOUT

    # timeout=30
    rule = dict_input.get('rule', None)
    if not rule:
        return {"status": "error", "reason": "Retro Hunt Rule not provided"}, 400
    task_type = dict_input.get('type', None)
    if not task_type:
        return {"status": "error", "reason": "type not provided"}, 400

    # Level
    level = dict_input.get('level', 1)
    try:
        level = int(level)
    except TypeError:
        level = 1
    if level not in range(1, 3):
        level = 1

    # # TODO: limit
    name = dict_input.get('name', '')
    name = escape(name)
    name = name[:60]
    # # TODO: limit
    description = dict_input.get('description', '')
    description = escape(description)
    description = description[:1000]

    res = api_validate_rule_to_add(rule, task_type)
    if res[1] != 200:
        return res

    tags = dict_input.get('tags', [])    # TODO escape custom tags
    mails = dict_input.get('mails', [])  # TODO escape mails
    res = verify_mail_list(mails)
    if res:
        return res

    # Filters # TODO MOVE ME
    filters = dict_input.get('filters', {})
    if filters:
        if filters.keys() == get_objects_retro_hunted():
            filters = {}
        for obj_type in filters:
            if obj_type not in get_objects_retro_hunted():
                return {"status": "error", "reason": "Invalid Tracker Object type"}, 400

            for filter_name in filters[obj_type]:
                if filter_name not in {'date_from', 'date_to', 'mimetypes', 'sources', 'subtypes'}:
                    return {"status": "error", "reason": "Invalid Filter"}, 400
                elif filter_name == 'date_from':
                    if not Date.validate_str_date(filters[obj_type]['date_from']):
                        return {"status": "error", "reason": "Invalid date_from"}, 400
                elif filter_name == 'date_to':
                    if not Date.validate_str_date(filters[obj_type]['date_from']):
                        return {"status": "error", "reason": "Invalid date_to"}, 400
                elif filter_name == 'mimetypes':  # TODO sanityze mimetypes
                    pass
                elif filter_name == 'sources':
                    if obj_type == 'item':
                        res = item_basic.verify_sources_list(filters['item']['sources'])
                        if res:
                            return res
                    else:
                        return {"status": "error", "reason": "Invalid Filter sources"}, 400
                elif filter_name == 'subtypes':
                    obj_subtypes = set(get_object_all_subtypes(obj_type))
                    for subtype in filters[obj_type]['subtypes']:
                        if subtype not in obj_subtypes:
                            return {"status": "error", "reason": "Invalid Tracker Object subtype"}, 400

            if 'date_from' and 'date_to' in filters:
                res = Date.api_validate_str_date_range(filters[obj_type]['date_from'], filters[obj_type]['date_to'])
                if res:
                    return res

    task_uuid = create_retro_hunt(user_org, user_id, level, name, task_type, rule, description=description,
                                  mails=mails, tags=tags, timeout=30, filters=filters)
    return {'name': name, 'rule': rule, 'type': task_type, 'uuid': task_uuid}, 200

def api_delete_retro_hunt_task(user_org, user_id, user_role, task_uuid):
    res = api_check_retro_hunt_task_uuid(task_uuid)
    if res:
        return res
    retro_hunt = RetroHunt(task_uuid)
    res = api_check_retro_hunt_acl(retro_hunt, user_org, user_id, user_role, 'delete')
    if res:
        return res
    if retro_hunt.is_running() and retro_hunt.get_state() not in ['completed', 'paused']:
        return {"status": "error", "reason": "You can't delete a running task"}, 400
    else:
        return retro_hunt.delete(), 200

################################################################################
################################################################################
################################################################################
################################################################################

#### DB FIX ####

# def _fix_db_custom_tags():
#     for tag in get_trackers_tags():
#         if not Tag.is_taxonomie_tag(tag) and not Tag.is_galaxy_tag(tag):
#             Tag.create_custom_tag(tag)

#### -- ####


# if __name__ == '__main__':

    # _fix_db_custom_tags()
    # fix_all_tracker_uuid_list()
    # res = get_all_tracker_uuid()
    # print(len(res))

    # import Term
    # Term.delete_term('5262ab6c-8784-4a55-b0ff-a471018414b4')

    # fix_tracker_stats_per_day('5262ab6c-8784-4a55-b0ff-a471018414b4')

    # tracker_uuid = '5262ab6c-8784-4a55-b0ff-a471018414b4'
    # fix_tracker_item_link(tracker_uuid)
    # res = get_item_all_trackers_uuid('archive/')
    # print(res)

    # res = is_valid_yara_rule('rule dummy {  }')

    # res = create_tracker('test', 'word', 'admin@admin.test', 1, [], [], None, sources=['crawled', 'pastebin.com', 'rt/pastebin.com'])
    # res = create_tracker('circl\.lu', 'regex', 'admin@admin.test', 1, [], [], None, sources=['crawled','pastebin.com'])
    # print(res)

    # t_uuid = '1c2d35b0-9330-4feb-b454-da13007aa9f7'
    # res = get_tracker_sources('ail-yara-rules/rules/crypto/certificate.yar', 'yara')

    # sys.path.append(os.environ['AIL_BIN'])
    # from packages import Term
    # Term.delete_term('074ab4be-6049-45b5-a20e-8125a4e4f500')

    # res = get_items_to_analyze('archive/pastebin.com_pro/2020/05/15', last='archive/pastebin.com_pro/2020/05/15/zkHEgqjQ.gz')
    # get_retro_hunt_task_progress('0', nb_src_done=2)

    # res = set_cache_retro_hunt_task_progress('0', 100)
    # res = get_retro_hunt_task_nb_src_done('0', sources=['pastebin.com_pro', 'alerts/pastebin.com_pro', 'crawled'])
    # print(res)

    # sources = ['pastebin.com_pro', 'alerts/pastebin.com_pro', 'crawled']
    # rule = 'custom-rules/4a8a3d04-f0b6-43ce-8e00-bdf47a8df241.yar'
    # name = 'retro_hunt_test_1'
    # description = 'circl retro hunt first test'
    # tags =  ['retro_circl', 'circl']
    # creator = 'admin@admin.test'
    # date_from = '20200610'
    # date_to = '20210630'

    # res = create_retro_hunt_task(name, rule, date_from, date_to, creator, sources=sources, tags=tags, description=description)

    # get_retro_hunt_nb_item_by_day(['80b402ef-a8a9-4e97-adb6-e090edcfd571'], date_from=None, date_to=None, num_day=31)

    # res = get_retro_hunt_nb_item_by_day(['c625f971-16e6-4331-82a7-b1e1b9efdec1'], date_from='20200610', date_to='20210630')

    # res = delete_retro_hunt_task('598687b6-f765-4f8b-861a-09ad76d0ab34')

    # print(res)
