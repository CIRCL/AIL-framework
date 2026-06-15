#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta

from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects, r_object
from lib.objects.Subforums import Subforum

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


FORUM_CRAWL_ACCOUNT_STATUSES = {'waiting', 'crawling', 'error', 'need_manual_login', 'banned', 'disabled'}
FORUM_CRAWL_WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

def _str_to_bool(value):
    return value == 'True'


def _active_time_ranges_to_str(ranges):
    return ','.join([f'{start}-{end}' for start, end in ranges])


def _str_to_active_time_ranges(value):
    ranges = []
    if value:
        for date_range in value.split(','):
            start, end = date_range.split('-', 1)
            ranges.append([int(start), int(end)])
    return ranges


class ForumAccount:
    def __init__(self, forum_id, account_id):
        self.forum_id = forum_id
        self.id = account_id

    def _get_field(self, field):
        return r_object.hget(f'forum:crawl:account:{self.forum_id}:{self.id}', field)

    def _set_field(self, field, value):
        return r_object.hset(f'forum:crawl:account:{self.forum_id}:{self.id}', field, value)

    def _del_field(self, field):
        return r_object.hdel(f'forum:crawl:account:{self.forum_id}:{self.id}', field)

    def get_meta(self, options={}):  # TODO only load needed meta
        account = {'id': self.id}
        account['enabled'] = self.is_enabled()
        account['status'] = self._get_field('status')
        account['error'] = self._get_field('error')
        account['cookiejar_uuid'] = self._get_field('cookiejar_uuid')
        account['last_login'] = self._get_field('last_login')
        account['active_time'] = self.get_active_time()
        account['random_time_between_page'] = self._get_field('random_time_between_page')
        account['subforums_to_crawl'] = self.get_subforums_to_crawl()
        account['current_task_uuid'] = self._get_field('current_task_uuid')
        account['current_crawl_key'] = self._get_field('current_crawl_key')
        account['current_url'] = self._get_field('current_url')
        account['current_referer'] = self._get_field('current_referer')
        account['last_used_at'] = self._get_field('last_used_at')
        account['last_crawled_at'] = self._get_field('last_crawled_at')
        account['last_extracted'] = self._get_field('last_extracted')
        account['available'] = self.is_available()
        account['availability_reason'] = self._get_field('availability_reason')
        return account

    def set_meta(self, meta):
        if 'status' not in meta:
            meta['status'] = 'need_manual_login'
        if meta.get('active_time'):
            meta['active_time'] = self.normalize_active_time(meta.get('active_time'))
        fields = ['status', 'error', 'cookiejar_uuid', 'last_login', 'current_task_uuid', 'current_crawl_key', 'current_url', 'current_referer', 'last_used_at', 'last_crawled_at', 'next_available_at', 'availability_reason', 'random_time_between_page']
        for field in fields:  # edit
            if meta.get(field) is None:
                self._del_field(field)
            else:
                self._set_field(field, meta.get(field))
        self._set_field('enabled', meta.get('enabled'))
        self._set_field('available', meta.get('available'))
        self.set_active_time(meta.get('active_time'))
        self.set_subforums_to_crawl(meta.get('subforums_to_crawl', []))

    def get_status(self):
        status = self._get_field('status')
        return status

    def set_status(self, status):
        self._set_field('status', status)

    def is_available(self):
        return _str_to_bool(self._get_field('available'))

    def is_enabled(self):
        return _str_to_bool(self._get_field('enabled'))

    def set_enabled(self, enabled):
        self._set_field('enabled', enabled)

    def get_cookiejar_uuid(self):
        return self._get_field('cookiejar_uuid')

    def set_cookiejar_uuid(self, cookiejar_uuid):
        self._set_field('cookiejar_uuid', cookiejar_uuid)

    def get_active_time(self):
        active_time = {}
        for weekday in FORUM_CRAWL_WEEKDAYS:
            active_time[weekday] = _str_to_active_time_ranges(self._get_field(f'active_time:{weekday}'))
        if active_time == {weekday: [] for weekday in FORUM_CRAWL_WEEKDAYS}:
            return None
        return active_time

    def set_active_time(self, active_time):
        if active_time:
            active_time = self.normalize_active_time(active_time)
            for weekday in FORUM_CRAWL_WEEKDAYS:
                self._set_field(f'active_time:{weekday}', _active_time_ranges_to_str(active_time.get(weekday, [])))
        else:
            for weekday in FORUM_CRAWL_WEEKDAYS:
                r_object.hdel(f'forum:crawl:account:{self.forum_id}:{self.id}', f'active_time:{weekday}')

    def _active_time_to_minute(self, value):
        if isinstance(value, str):
            hour, minute = value.split(':', 1)
            return int(hour) * 60 + int(minute)
        return int(value)

    def normalize_active_time(self, active_time):
        if not active_time:
            return None
        normalized = {weekday: [] for weekday in FORUM_CRAWL_WEEKDAYS}
        for weekday in FORUM_CRAWL_WEEKDAYS:
            for start, end in active_time.get(weekday, []):
                start = self._active_time_to_minute(start)
                end = self._active_time_to_minute(end)
                if start < 0 or start > 1440 or end < 0 or end > 1440 or start == end:
                    continue
                if start < end:
                    normalized[weekday].append([start, end])
                else:
                    normalized[weekday].append([start, 1440])
                    next_weekday = FORUM_CRAWL_WEEKDAYS[(FORUM_CRAWL_WEEKDAYS.index(weekday) + 1) % 7]
                    normalized[next_weekday].append([0, end])
        for weekday in FORUM_CRAWL_WEEKDAYS:
            ranges = sorted(normalized[weekday])
            merged = []
            for start, end in ranges:
                if not merged or start > merged[-1][1]:
                    merged.append([start, end])
                elif end > merged[-1][1]:
                    merged[-1][1] = end
            normalized[weekday] = merged
        return normalized

    def is_in_active_time(self, now=None):
        active_time = self.get_active_time()
        if not active_time:
            return True
        if now is None:
            now = datetime.now(timezone.utc)
        weekday = FORUM_CRAWL_WEEKDAYS[now.weekday()]
        minute = now.hour * 60 + now.minute
        for start, end in active_time.get(weekday, []):
            if start <= minute < end:
                return True
        return False

    def get_next_active_time(self, now=None):
        active_time = self.get_active_time()
        if not active_time:
            return None
        if now is None:
            now = datetime.now(timezone.utc)
        now = now.astimezone(timezone.utc)
        minute = now.hour * 60 + now.minute
        for delta in range(0, 7):
            day = now + timedelta(days=delta)
            weekday = FORUM_CRAWL_WEEKDAYS[day.weekday()]
            start_min = minute + 1 if delta == 0 else 0
            for start, end in active_time.get(weekday, []):
                if end <= start_min:
                    continue
                next_minute = max(start, start_min)
                next_dt = day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=next_minute)
                return int(next_dt.timestamp())

    def get_subforums_to_crawl(self):
        return r_object.smembers(f'forum:crawl:account:subforums:{self.forum_id}:{self.id}')

    def set_subforums_to_crawl(self, subforum_ids):
        r_object.delete(f'forum:crawl:account:subforums:{self.forum_id}:{self.id}')
        for subforum_id in subforum_ids or []:
            r_object.sadd(f'forum:crawl:account:subforums:{self.forum_id}:{self.id}', subforum_id)

    def refresh_availability(self, forum_enabled=True, now=None):
        if now is None:
            now = datetime.now(timezone.utc)
        reason = 'available'
        next_available_at = 0
        status = self.get_status()
        if not forum_enabled:
            reason = 'forum_disabled'
        elif not self.is_enabled():
            reason = 'disabled'
        elif status in ['error', 'need_manual_login', 'banned', 'disabled']:
            reason = status
        elif status != 'waiting':
            reason = 'not_waiting'
        elif not self.get_cookiejar_uuid():
            reason = 'missing_cookiejar'
        elif self._get_field('current_crawl_key'):
            reason = 'already_crawling'
        elif not self.is_in_active_time(now=now):
            reason = 'outside_active_time'
            next_available_at = self.get_next_active_time(now=now)
        self._set_field('available', reason == 'available')
        self._set_field('availability_reason', reason)
        if reason == 'available':
            r_object.zadd(f'forum:accounts:available:{self.forum_id}', {self.id: next_available_at})
        else:
            r_object.zrem(f'forum:accounts:available:{self.forum_id}', self.id)

    def set_current_crawl(self, crawl_key, url, referer, task_uuid):
        self._set_field('current_crawl_key', crawl_key)
        self._set_field('current_url', url)
        self._set_field('current_referer', referer)
        self._set_field('current_task_uuid', task_uuid)

    def clear_current_crawl(self):
        self._del_field('current_crawl_key')
        self._del_field('current_url')
        self._del_field('current_referer')
        self._del_field('current_task_uuid')

    def set_error(self, error):
        self.set_status('error')
        self._set_field('error', error)

    def clear_error(self):
        self._del_field('error')
        self.set_status('waiting')

class Forum(AbstractDaterangeObject):
    def __init__(self, id):
        super().__init__('forum', id)

    def get_forum_type(self):
        return self._get_field('forum_type')

    def get_name(self):
        return self._get_field('name')

    def set_name(self, name):
        self._set_field('name', name)

    def get_info(self):
        return self._get_field('info')

    def set_info(self, info):
        self._set_field('info', info)

    def get_url(self):
        return self._get_field('url')

    def set_url(self, url):
        self._set_field('url', url)

    def get_subforums(self):
        subforums = []
        for child in self.get_childrens():
            obj_type, _, obj_id = child.split(':', 2)
            if obj_type == 'subforum':
                subforums.append(obj_id)
        return subforums

    def get_nb_subforums(self):
        return len(self.get_subforums())

    def get_orphan_subforums(self):
        return r_object.smembers(f'subforums:orphans:{self.id}')

    def get_nb_orphan_subforums(self):
        return len(self.get_orphan_subforums())

    def add_orphan_subforum(self, subforum_global_id):
        r_object.sadd(f'subforums:orphans:{self.id}', subforum_global_id)

    def remove_orphan_subforum(self, subforum_global_id):
        r_object.srem(f'subforums:orphans:{self.id}', subforum_global_id)

    def is_orphan_subforum(self, subforum_global_id):
        return r_object.sismember(f'subforums:orphans:{self.id}', subforum_global_id)

    def add_post_global_id(self, post_id, post_global_id):
        r_object.hset(f'posts:{self.subtype}:{self.id}', post_id, post_global_id)

    def get_post_global_id(self, post_id):
        return r_object.hget(f'posts:{self.subtype}:{self.id}', post_id)

    def get_crawl_config(self):
        config = {'id': self.id}
        config['enabled'] = _str_to_bool(self._get_field('enabled'))
        config['javascript'] = _str_to_bool(self._get_field('javascript'))
        config['delta_subforum_refresh'] = self._get_field('delta_subforum_refresh')
        config['delta_thread_refresh'] = self._get_field('delta_thread_refresh')
        config['default_referer'] = self._get_field('default_referer')
        config['timeout'] = self._get_field('timeout')
        config['proxy'] = self._get_field('proxy')
        config['accounts'] = self.get_crawl_accounts()
        config['subforums_excluded'] = r_object.smembers(f'forum:crawl:config:subforums:excluded:{self.id}')
        config['subforums_to_crawl'] = r_object.smembers(f'forum:crawl:config:subforums:to_crawl:{self.id}')
        return config

    def set_crawl_config(self, config):
        self._set_field('enabled', config.get('enabled'))
        self._set_field('javascript', config.get('javascript'))
        self._set_field('delta_subforum_refresh', int(config.get('delta_subforum_refresh') or 0))
        self._set_field('delta_thread_refresh', int(config.get('delta_thread_refresh') or 0))
        self._set_field('timeout', int(config.get('timeout') or 60))
        if config.get('default_referer'):
            self._set_field('default_referer', config.get('default_referer'))
        if config.get('proxy'):
            self._set_field('proxy', config.get('proxy'))
        else:
            r_object.hdel(f'meta:{self.type}:{self.id}', 'proxy')
        if 'subforums_excluded' in config:
            r_object.delete(f'forum:crawl:config:subforums:excluded:{self.id}')
            for subforum_id in config.get('subforums_excluded', []):
                r_object.sadd(f'forum:crawl:config:subforums:excluded:{self.id}', subforum_id)
        if 'subforums_to_crawl' in config:
            r_object.delete(f'forum:crawl:config:subforums:to_crawl:{self.id}')
            for subforum_id in config.get('subforums_to_crawl', []):
                r_object.sadd(f'forum:crawl:config:subforums:to_crawl:{self.id}', subforum_id)
        return self.get_crawl_config()

    def get_crawl_accounts(self):
        return r_object.smembers(f'forum:crawl:accounts:{self.id}')

    def get_crawl_account(self, account_id):
        return ForumAccount(self.id, account_id)

    def set_crawl_account(self, account_id, account):
        self.get_crawl_account(account_id).set_meta(account)

    def add_crawl_account(self, account_id, meta=None):
        account = ForumAccount(self.id, account_id)
        account.set_meta(meta)
        r_object.sadd(f'forum:crawl:accounts:{self.id}', account_id)
        return account

    def remove_crawl_account(self, account_id):
        r_object.srem(f'forum:crawl:accounts:{self.id}', account_id)
        r_object.zrem(f'forum:accounts:available:{self.id}', account_id)

    def refresh_account_availability(self, account_id):
        ForumAccount(self.id, account_id).refresh_availability(forum_enabled=self.get_crawl_config().get('enabled'))

    def refresh_accounts_availability(self):
        for account_id in self.get_crawl_accounts():
            self.refresh_account_availability(account_id)

    def get_available_accounts(self):
        return r_object.zrange(f'forum:accounts:available:{self.id}', 0, -1)

    # TODO
    def get_next_available_account_round_robin(self):
        accounts = self.get_available_accounts()
        if not accounts:
            r_object.delete(f'forum:crawl:rr:{self.id}')
            return None
        index = r_object.incr(f'forum:crawl:rr:{self.id}') - 1
        return accounts[index % len(accounts)]

    def _get_crawl_item_subforum_id(self, item):
        if item.get('type') == 'subforum':
            return item.get('id')
        if item.get('type') == 'forum-thread':
            parent = item.get('parent') or {}
            if parent.get('type') == 'subforum':
                return parent.get('id')
        return None

    def is_subforum_in_scope(self, subforum_id, allowed_roots):
        if not allowed_roots:
            return True
        if subforum_id in allowed_roots:
            return True
        # CHECK Child
        # subforums = list(allowed_roots)
        # seen = set()
        # while subforums:
        #     current_id = subforums.pop(0)
        #     if current_id in seen:
        #         continue
        #     seen.add(current_id)
        #     # CHECK children
        #     for child_id in Subforum(current_id, self.id).get_subforums():
        #         if child_id == subforum_id:
        #             return True
        #         if child_id not in seen:
        #             subforums.append(child_id)
        return False

    def forum_allows_crawl_item(self, item):
        config = self.get_crawl_config()
        if not config.get('enabled'):
            return False, 'forum_disabled'
        if item.get('type') == 'forum':
            return True, 'allowed'
        subforum_id = self._get_crawl_item_subforum_id(item)
        if not subforum_id:
            return False, 'missing_subforum_id'
        if subforum_id in config.get('subforums_excluded', set()):
            return False, 'excluded_subforum'
        subforums_to_crawl = config.get('subforums_to_crawl', set())
        if self.is_subforum_in_scope(subforum_id, subforums_to_crawl):
            return True, 'allowed'
        return False, 'outside_forum_scope'

    def account_allows_crawl_item(self, account_id, item):
        if item.get('type') == 'forum':
            return True, 'allowed'
        subforum_id = self._get_crawl_item_subforum_id(item)
        if not subforum_id:
            return False, 'missing_subforum_id'
        subforums_to_crawl = ForumAccount(self.id, account_id).get_subforums_to_crawl()
        if self.is_subforum_in_scope(subforum_id, subforums_to_crawl):
            return True, 'allowed'
        return False, 'outside_account_scope'

    def preferred_account_allows_item(self, account_id, item):
        preferred_account_ids = item.get('preferred_account_ids', [])
        if not preferred_account_ids:
            return True, 'allowed'
        if account_id in preferred_account_ids:
            return True, 'allowed'
        if item.get('preferred_account_fallback'):
            return True, 'allowed_fallback'
        return False, 'not_preferred_account'

    def get_thread_crawl_account(self, thread_id):
        return r_object.hget(f'forum:crawl:thread:account:{self.id}', thread_id)

    def set_thread_crawl_account(self, thread_id, account_id):
        return r_object.hset(f'forum:crawl:thread:account:{self.id}', thread_id, account_id)

    def release_thread_crawl_account(self, thread_id):
        return r_object.hdel(f'forum:crawl:thread:account:{self.id}', thread_id)

    def thread_affinity_allows_account(self, thread_id, account_id):
        assigned_account = self.get_thread_crawl_account(thread_id)
        if not assigned_account or assigned_account == account_id:
            return True, 'allowed'
        return False, 'thread_assigned_to_other_account'

    def account_can_reserve_crawl_item(self, account_id, item):
        allowed, reason = self.forum_allows_crawl_item(item)
        if not allowed:
            return allowed, reason
        allowed, reason = self.account_allows_crawl_item(account_id, item)
        if not allowed:
            return allowed, reason
        allowed, reason = self.preferred_account_allows_item(account_id, item)
        if not allowed:
            return allowed, reason
        if item.get('type') == 'forum-thread':
            affinity_allowed, affinity_reason = self.thread_affinity_allows_account(item.get('id'), account_id)
            if not affinity_allowed:
                return affinity_allowed, affinity_reason
        return allowed, reason

    def reserve_crawl_item_for_account(self, crawl_key, account_id, task_uuid=None):
        item = self.get_crawl_item(crawl_key)
        if not item:
            return False, 'missing_item'
        allowed, reason = self.account_can_reserve_crawl_item(account_id, item)
        if not allowed:
            return allowed, reason
        thread_affinity_set = False
        if item.get('type') == 'forum-thread' and not self.get_thread_crawl_account(item.get('id')):
            self.set_thread_crawl_account(item.get('id'), account_id)
            thread_affinity_set = True
        reserved, payload = self.reserve_crawl_item(crawl_key, account_id, task_uuid=task_uuid)
        if not reserved and thread_affinity_set:
            self.release_thread_crawl_account(item.get('id'))
        return reserved, payload

    def validate_crawl_item(self, item):
        if not isinstance(item, dict):
            return False, 'invalid_item'
        if not item.get('crawl_key'):
            return False, 'missing_crawl_key'
        if item.get('type') not in {'forum', 'subforum', 'forum-thread'}:
            return False, 'invalid_type'
        if not item.get('id'):
            return False, 'missing_id'
        if not isinstance(item.get('page'), int) or item.get('page') < 1:
            return False, 'invalid_page'
        if not item.get('url'):
            return False, 'missing_url'
        parent = item.get('parent')
        if parent is not None:
            if not isinstance(parent, dict):
                return False, 'invalid_parent'
            if parent.get('type') not in {'forum', 'subforum'}:
                return False, 'invalid_parent_type'
            if not parent.get('id'):
                return False, 'missing_parent_id'
        return True, None

    def enqueue_crawl_item(self, item, score=None):
        valid, reason = self.validate_crawl_item(item)
        if not valid:
            return False, reason
        crawl_key = item['crawl_key']
        if self.is_crawl_item_queued(crawl_key):
            return False, 'already_queued'
        if score is None:
            score = int(time.time())
        r_object.hset(f'forum:crawl:items:{self.id}', crawl_key, json.dumps(item))
        r_object.zadd(f'forum:crawl:queue:{self.id}', {crawl_key: score})
        r_object.sadd(f'forum:crawl:queued:{self.id}', crawl_key)
        return True, None

    def get_crawl_item(self, crawl_key):
        item = r_object.hget(f'forum:crawl:items:{self.id}', crawl_key)
        if item:
            return json.loads(item)
        return None

    def get_pending_crawl_keys(self, start=0, stop=100):
        return r_object.zrange(f'forum:crawl:queue:{self.id}', start, stop)

    def reserve_crawl_item(self, crawl_key, account_id, task_uuid=None):
        if not r_object.zrem(f'forum:crawl:queue:{self.id}', crawl_key):
            return False, 'not_pending'
        item = self.get_crawl_item(crawl_key)
        if not item:
            self.complete_crawl_item(crawl_key)
            return False, 'missing_item'
        inflight = {
            'account_id': account_id,
            'task_uuid': task_uuid,
            'started_at': int(time.time()),
        }
        r_object.hset(f'forum:crawl:inflight:{self.id}', crawl_key, json.dumps(inflight))
        return True, item

    def _cleanup_crawl_item(self, crawl_key):
        r_object.zrem(f'forum:crawl:queue:{self.id}', crawl_key)
        r_object.srem(f'forum:crawl:queued:{self.id}', crawl_key)
        r_object.hdel(f'forum:crawl:items:{self.id}', crawl_key)
        r_object.hdel(f'forum:crawl:inflight:{self.id}', crawl_key)
        return True, None

    def complete_crawl_item(self, crawl_key):
        return self._cleanup_crawl_item(crawl_key)

    def fail_crawl_item(self, crawl_key, error=None):
        item = self.get_crawl_item(crawl_key)
        if item and item.get('type') == 'forum-thread':
            self.release_thread_crawl_account(item.get('id'))
        return self._cleanup_crawl_item(crawl_key)

    def get_inflight_crawl_items(self):
        inflight = {}
        for crawl_key, meta in r_object.hgetall(f'forum:crawl:inflight:{self.id}').items():
            inflight[crawl_key] = json.loads(meta)
        return inflight

    def get_inflight_crawl_item(self, crawl_key):
        meta = r_object.hget(f'forum:crawl:inflight:{self.id}', crawl_key)
        if meta:
            return json.loads(meta)
        return None

    def get_nb_pending_crawl_items(self):
        return r_object.zcard(f'forum:crawl:queue:{self.id}')

    def get_nb_inflight_crawl_items(self):
        return r_object.hlen(f'forum:crawl:inflight:{self.id}')

    def is_crawl_item_queued(self, crawl_key):
        return r_object.sismember(f'forum:crawl:queued:{self.id}', crawl_key)

    def get_link(self, flask_context=False):
        if flask_context:
            return url_for('correlation.show_correlation', type=self.type, subtype=self.subtype, id=self.id)
        return f'{baseurl}/correlation/show?type={self.type}&subtype={self.subtype}&id={self.id}'

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf086', 'color': '#4dffff', 'radius': 5}

    def get_misp_object(self):
        pass

    def get_meta(self, options=set(), flask_context=False):
        meta = self._get_meta(options=options, flask_context=flask_context)
        meta['tags'] = self.get_tags(r_list=True)
        if 'forum_type' in options:
            meta['forum_type'] = self.get_forum_type()
        if 'name' in options:
            meta['name'] = self._get_field('name')
        if 'info' in options:
            meta['info'] = self._get_field('info')
        if 'url' in options:
            meta['url'] = self._get_field('url')
        if 'subforums' in options:
            meta['subforums'] = self.get_subforums()
        if 'nb_subforums' in options:
            meta['nb_subforums'] = self.get_nb_subforums()
        if 'orphan_subforums' in options:
            meta['orphan_subforums'] = self.get_orphan_subforums()
        if 'nb_orphan_subforums' in options:
            meta['nb_orphan_subforums'] = self.get_nb_orphan_subforums()
        return meta

    def create(self, forum_type, name=None, url=None, info=None):
        if not self.exists():
            self._set_field('forum_type', forum_type)
            self._add_create()
        if name:
            self.set_name(name)
        if url:
            self.set_url(url)
        if info:
            self.set_info(info)
        return self

    def delete(self):
        self._delete()

def get_forums():
    return Forums().get_ids()

class Forums(AbstractDaterangeObjects):
    def __init__(self):
        super().__init__('forum', Forum)

    def get_name(self):
        return 'Forums'

    def get_icon(self):
        return {'fa': 'fas', 'icon': 'comments'}

    def get_link(self, flask_context=False):
        if flask_context:
            return url_for('objects_subtypes.objects_dashboard_username')
        return f'{baseurl}/objects/forums'

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search
