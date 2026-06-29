#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

from datetime import datetime, timezone
from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, AbstractSubtypeObjects, r_object
from lib.objects import Posts
from packages import Date

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None

# TODO GET FORUM
class ForumThread(AbstractSubtypeObject):
    def __init__(self, id, subtype):
        super().__init__('forum-thread', id, subtype)

    def get_forum_type(self):
        return self.subtype

    def get_forum_id(self): # TODO
        pass

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

    def contain_posts(self):
        return r_object.exists(f'posts:forum-thread:{self.subtype}:{self.id}')

    def get_nb_posts(self):
        return r_object.zcard(f'posts:forum-thread:{self.subtype}:{self.id}')

    def get_post_page(self, post_gid, nb):
        if not post_gid:
            return -1
        rank = r_object.zrank(f'posts:forum-thread:{self.subtype}:{self.id}', post_gid)
        if rank is None:
            return -1
        return int(rank / nb) + 1

    def _get_posts(self, nb=-1, page=-1):
        if nb < 1:
            posts = r_object.zrange(f'posts:forum-thread:{self.subtype}:{self.id}', 0, -1, withscores=True)
            nb_pages = 0
            page = 1
            total = len(posts)
            nb_first = 1
            nb_last = total
        else:
            total = r_object.zcard(f'posts:forum-thread:{self.subtype}:{self.id}')
            nb_pages = total / nb
            if not nb_pages.is_integer():
                nb_pages = int(nb_pages) + 1
            else:
                nb_pages = int(nb_pages)
            if page > nb_pages or page < 1:
                page = nb_pages

            if page > 1:
                start = (page - 1) * nb
            else:
                start = 0
            posts = r_object.zrange(f'posts:forum-thread:{self.subtype}:{self.id}', start, start + nb - 1, withscores=True)
            nb_first = start + 1
            nb_last = start + nb
        if nb_last > total:
            nb_last = total
        return posts, {'nb': nb, 'page': page, 'nb_pages': nb_pages, 'total': total, 'nb_first': nb_first, 'nb_last': nb_last}

    def get_post_meta(self, post_global_id, timestamp=None, options=None, translation_target=None):
        _, _, post_id = post_global_id.split(':', 2)
        post = Posts.Post(post_id)
        if not options:
            options = {'content', 'link', 'state', 'timestamp'}  # TODO GET QUOTES
        meta = post.get_meta(options=options, translation_target=translation_target)
        if timestamp is not None:
            meta['timestamp'] = timestamp
        return meta

    def get_posts(self, page=-1, nb=50, post_gid=None, options=None, translation_target=None):
        tags = {}
        posts = {}
        curr_date = None
        try:
            nb = int(nb)
        except (TypeError, ValueError):
            nb = 50
        if post_gid:
            page = self.get_post_page(post_gid, nb)
        else:
            if not page:
                page = -1
            try:
                page = int(page)
            except TypeError:
                page = 1
        post_items, pagination = self._get_posts(nb=nb, page=page)
        for post_item in post_items:
            timestamp = post_item[1]
            date_day = datetime.utcfromtimestamp(timestamp).strftime('%Y/%m/%d')
            if date_day != curr_date:
                posts[date_day] = []
                curr_date = date_day
            post_dict = self.get_post_meta(post_item[0], timestamp=timestamp, options=options, translation_target=translation_target)
            posts[date_day].append(post_dict)

            if post_dict.get('tags'):
                for tag in post_dict['tags']:
                    if tag not in tags:
                        tags[tag] = 0
                    tags[tag] += 1
        return posts, pagination, tags

    def get_timestamp_first_post(self):
        first = r_object.zrange(f'posts:forum-thread:{self.subtype}:{self.id}', 0, 0, withscores=True)
        if first:
            return int(first[0][1])

    def get_timestamp_last_post(self):
        last = r_object.zrevrange(f'posts:forum-thread:{self.subtype}:{self.id}', 0, 0, withscores=True)
        if last:
            return int(last[0][1])

    def get_first_post(self):
        return r_object.zrange(f'posts:forum-thread:{self.subtype}:{self.id}', 0, 0)

    def get_last_post(self):
        return r_object.zrevrange(f'posts:forum-thread:{self.subtype}:{self.id}', 0, 0)

    def get_nb_post_by_hours(self, date_day, nb_day):
        hours = []
        timestamp = time.mktime(datetime.strptime(date_day, "%Y%m%d").utctimetuple())
        for i in range(24):
            timestamp_end = timestamp + 3600
            nb_posts = r_object.zcount(f'posts:forum-thread:{self.subtype}:{self.id}', timestamp, timestamp_end)
            timestamp = timestamp_end
            hours.append({'date': f'{date_day[0:4]}-{date_day[4:6]}-{date_day[6:8]}', 'day': nb_day, 'hour': i, 'count': nb_posts})
        return hours

    def get_nb_post_by_week(self, date_day):
        date_day = Date.get_date_week_by_date(date_day)
        week_posts = []
        i = 0
        for date in Date.daterange_add_days(date_day, 6):
            week_posts = week_posts + self.get_nb_post_by_hours(date, i)
            i += 1
        return week_posts

    def get_nb_post_this_week(self):
        week_date = Date.get_current_week_day()
        return self.get_nb_post_by_week(week_date)

    def get_nb_week_posts(self):
        week = {}
        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            week[day] = {}
            for i in range(24):
                week[day][i] = 0

        for post_t in r_object.zrange(f'posts:forum-thread:{self.subtype}:{self.id}', 0, -1, withscores=True):
            timestamp = datetime.utcfromtimestamp(float(post_t[1]))
            date_name = timestamp.strftime('%a')
            week[date_name][timestamp.hour] += 1
        stats = []
        nb_day = 0
        for day in week:
            for hour in week[day]:
                stats.append({'date': day, 'day': nb_day, 'hour': hour, 'count': week[day][hour]})
            nb_day += 1
        return stats

    def get_post_years(self):
        timestamp = self.get_timestamp_first_post()
        if not timestamp:
            year_start = int(self.get_first_seen()[0:4])
            year_end = int(self.get_last_seen()[0:4])
            return list(range(year_start, year_end + 1))
        else:
            timestamp = datetime.utcfromtimestamp(float(timestamp))
            year_start = int(timestamp.strftime('%Y'))
            timestamp = datetime.utcfromtimestamp(float(self.get_timestamp_last_post()))
            year_end = int(timestamp.strftime('%Y'))
            return list(range(year_start, year_end + 1))

    def get_nb_year_posts(self, year):
        nb_year = {}
        nb_max = 0
        start = int(datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        end = int(datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp())

        for post_t in r_object.zrangebyscore(f'posts:forum-thread:{self.subtype}:{self.id}', start, end, withscores=True):
            timestamp = datetime.utcfromtimestamp(float(post_t[1]))
            date = timestamp.strftime('%Y-%m-%d')
            if date not in nb_year:
                nb_year[date] = 0
            nb_year[date] += 1
            nb_max = max(nb_max, nb_year[date])
        return nb_max, nb_year

    # post_id: real id of the forum post
    def add_post(self, post, post_id, timestamp, forum_obj, quote_ids=None):
        r_object.zadd(f'posts:forum-thread:{self.subtype}:{self.id}', {post.get_global_id(): float(timestamp)})
        subforum_id = self.get_parent().split(':', 2)[2]
        r_object.zadd(f'last:subforum:{self.subtype}:{subforum_id}', {self.id: float(timestamp)})
        post.set_parent(self.get_global_id())
        forum_obj.add_post_global_id(post_id, post.get_global_id())

        date = post.get_date()

        self.add(date, post)       # ForumThread <-> Post
        forum_obj.add(date, post)  # Forum <-> Post
        # TODO Correlation  Forum <-> ForumThread ???

        # quoted Posts
        unresolved = []
        if quote_ids and forum_obj:
            for quoted_post_id in quote_ids:
                if isinstance(quoted_post_id, dict):
                    quoted_post_id = quoted_post_id.get('post_id')
                if not quoted_post_id:
                    continue
                quoted_post_global_id = forum_obj.get_post_global_id(quoted_post_id)
                if quoted_post_global_id:
                    post.add_relationship(quoted_post_global_id, 'quote')
                else:
                    unresolved.append(str(quoted_post_id))
        return unresolved

    def get_link(self, flask_context=False):
        if flask_context:
            return url_for('correlation.show_correlation', type=self.type, subtype=self.subtype, id=self.id)
        return f'{baseurl}/correlation/show?type={self.type}&subtype={self.subtype}&id={self.id}'

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf0e6', 'color': '#4dffff', 'radius': 5}

    def get_misp_object(self):
        pass

    def get_meta(self, options=set(), flask_context=False):
        meta = self._get_meta(options=options, flask_context=flask_context)
        meta['tags'] = self.get_tags(r_list=True)
        for field in ('name', 'info', 'url', 'flags'):
            if field in options:
                meta[field] = self._get_field(field)
        if 'nb_posts' in options:
            meta['nb_posts'] = self.get_nb_posts()
        return meta

    def create(self, name=None, url=None, info=None, parent_global_id=None):
        if name:
            self._set_field('name', name)
        if url:
            self.set_url(url)
        if info:
            self.set_info(info)
        if parent_global_id:
            self.set_parent(obj_global_id=parent_global_id)
        return self

    def delete(self):
        self._delete()


class ForumThreads(AbstractSubtypeObjects):
    def __init__(self):
        super().__init__('forum-thread', ForumThread)

    def get_name(self):
        return 'Forum-Threads'

    def get_icon(self):
        return {'fa': 'fas', 'icon': 'comments'}

    def get_link(self, flask_context=False):
        if flask_context:
            return url_for('objects_subtypes.objects_dashboard_username')
        return f'{baseurl}/objects/forum-threads'

    def sanitize_id_to_search(self, subtypes, name_to_search):
        return name_to_search
