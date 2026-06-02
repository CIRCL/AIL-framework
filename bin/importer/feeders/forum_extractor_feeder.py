#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Forum Extractor Feeder Importer Module
======================================

Ingest normalized forum-extractor dictionaries and upsert forum/subforum/thread/post objects.
"""

import datetime
# import json
import logging  # TODO USE AIL LOGGER
import os
import sys

sys.path.append(os.environ['AIL_BIN'])

from importer.feeders.Default import DefaultFeeder
from lib.objects.Forums import Forum
from lib.objects.Subforums import Subforum
from lib.objects.ForumThreads import ForumThread
from lib.objects.Posts import Post

# TODO IMAGES + USER ACCOUNTS + FILENAMES
class ForumExtractorFeeder(DefaultFeeder):
    """Ingest forum-extractor output into AIL forum objects."""

    def __init__(self, json_data):
        super().__init__(json_data)
        self.name = 'forum-extractor'
        self.logger = logging.getLogger(self.__class__.__name__)

    def import_result(self):
        """Import one forum-extractor result dictionary from self.json_data."""
        status = self.json_data.get('status')

        if status == 'success':
            return self._import_success(self.json_data)
        if status == 'unsupported_page_type':
            self.logger.info('Forum extractor unsupported page type: %s', self.json_data.get('page_type'))
            return {'status': 'unsupported_page_type', 'imported': 0, 'warnings': ['unsupported_page_type']}
        if status == 'error':
            self.logger.error('Forum extractor parser error: %s', self.json_data.get('error'))
            return {'status': 'error', 'imported': 0, 'error': self.json_data.get('error')}

        self.logger.error('Forum extractor unknown status: %s', status)
        return {'status': 'error', 'imported': 0, 'error': f'unknown_status:{status}'}

    def _import_success(self, result):
        """Import a successful parser result payload."""
        forum_type = result.get('forum_type')
        forum_id = result.get('forum_id')
        extracted = result.get('extracted') or {}

        if not forum_type or not forum_id:
            return {'status': 'error', 'imported': 0, 'error': 'missing_forum_type_or_forum_id'}

        forum = self._upsert_forum(result, extracted, forum_type, forum_id)
        if not forum:
            return {'status': 'error', 'imported': 0, 'error': 'forum_upsert_failed'}

        parent_subforum = self._upsert_subforum(extracted.get('parent_subforum'), forum_type, forum_id, forum)
        current_subforum = self._upsert_subforum(extracted.get('current_subforum'), forum_type, forum_id, forum, parent_subforum)

        for sub in extracted.get('subforums') or []:
            self._upsert_subforum_recursive(sub, forum_type, forum_id, forum, current_subforum or parent_subforum)

        if not current_subforum and result.get('page_type') in {'thread_page', 'forum_thread_list'}:
            if extracted.get('thread') or extracted.get('threads'):
                return {'status': 'error', 'imported': 0, 'error': 'missing_current_subforum'}

        imported = {'forum': 1, 'subforum': 0, 'forum-thread': 0, 'post': 0}
        warnings = []

        thread_objs = []
        if extracted.get('thread'):
            thread_objs.append(extracted['thread'])
        thread_objs.extend(extracted.get('threads') or [])

        for thread_data in thread_objs:
            thread = self._upsert_thread(thread_data, forum_type, forum_id, current_subforum)
            if not thread:
                return {'status': 'error', 'imported': sum(imported.values()), 'error': 'thread_parent_missing'}
            imported['forum-thread'] += 1

        posts = extracted.get('posts') or []
        imported_posts = []
        parent_thread = self._resolve_parent_thread(extracted, forum_type, forum_id) # TODO warning not created
        for post_data in posts:
            post = self._upsert_post(post_data, forum_type, forum_id, parent_thread, forum)
            if post:
                imported_posts.append((post, post_data))
                imported['post'] += 1

        seen_timestamps = [self._safe_timestamp(p[1].get('post_timestamp')) for p in imported_posts if self._safe_timestamp(p[1].get('post_timestamp'))]
        if seen_timestamps:
            date_values = {
                self._to_date_int(min(seen_timestamps)),
                self._to_date_int(max(seen_timestamps)),
            }
            for date_value in date_values:
                forum.update_daterange(date_value)
                if current_subforum:
                    current_subforum.update_daterange(date_value)
                if parent_thread:
                    parent_thread.update_daterange(date_value)
        # elif page_timestamp:  # TODO ONLY USE POST TIMESTAMP
        #     date = self._to_date_int(page_timestamp)
        #     forum.update_daterange(date)
        #     if current_subforum:
        #         current_subforum.update_daterange(date)
        #     for thread_data in thread_objs:
        #         thread = self._upsert_thread(thread_data, forum_type, forum_id, current_subforum)
        #         if thread:
        #             thread.update_daterange(date)

        return {'status': 'success', 'imported': imported, 'warnings': warnings}

    def _upsert_forum(self, result, extracted, forum_type, forum_id):
        """Create/update a Forum object from extracted data."""
        fdata = extracted.get('forum') or {}
        forum = Forum(forum_id, forum_type)
        if fdata.get('forum_name'):
            forum._set_field('title', fdata.get('forum_name'))
        forum_url = fdata.get('forum_url') or result.get('url')
        if forum_url:
            forum._set_field('url', forum_url)
        if fdata.get('info'):
            forum._set_field('info', fdata.get('info'))
        return forum

    def _upsert_subforum_recursive(self, sub_data, forum_type, forum_id, forum, parent_subforum=None):
        """Recursively create/update subforums and parent links."""
        subforum = self._upsert_subforum(sub_data, forum_type, forum_id, forum, parent_subforum)
        if not subforum:
            return
        for child in sub_data.get('subforums') or []:
            self._upsert_subforum_recursive(child, forum_type, forum_id, forum, subforum)

    def _upsert_subforum(self, sub_data, forum_type, forum_id, forum, parent_subforum=None):
        """Create/update one Subforum object and set parent."""
        if not sub_data or not sub_data.get('subforum_id'):
            return None
        subforum = Subforum(f'{forum_id}/{sub_data.get("subforum_id")}', forum_type)
        if sub_data.get('subforum_name'):
            subforum._set_field('title', sub_data.get('subforum_name'))
        if sub_data.get('subforum_url'):
            subforum._set_field('url', sub_data.get('subforum_url'))
        if sub_data.get('description'):
            subforum._set_field('info', sub_data.get('description'))
        elif sub_data.get('info'):
            subforum._set_field('info', sub_data.get('info'))
        # if sub_data.get('flags') is not None:
        #     subforum._set_field('flags', json.dumps(sub_data.get('flags')))
        subforum.set_parent(obj_global_id=(parent_subforum or forum).get_global_id())
        return subforum

    def _upsert_thread(self, thread_data, forum_type, forum_id, subforum):
        """Create/update one ForumThread object and set parent subforum."""
        if not thread_data or not thread_data.get('thread_id'):
            return None
        if not subforum:
            return None
        thread = ForumThread(f'{forum_id}/{thread_data.get("thread_id")}', forum_type)
        if thread_data.get('thread_title'):
            thread._set_field('title', thread_data.get('thread_title'))
        if thread_data.get('thread_url'):
            thread._set_field('url', thread_data.get('thread_url'))
        # if thread_data.get('thread_flags') is not None:
        #     thread._set_field('flags', json.dumps(thread_data.get('thread_flags')))
        # TODO USER ACCOUNT
        # TODO META
        # thread._set_field('info', json.dumps({
        #     'author_id': thread_data.get('thread_author_id'),
        #     'author_username': thread_data.get('thread_author_username'),
        #     'reply_count': thread_data.get('thread_reply_count'),
        #     'view_count': thread_data.get('thread_view_count'),
        #     'page_count': thread_data.get('thread_page_count'),
        #     'current_page': thread_data.get('thread_current_page'),
        # }))
        thread.set_parent(obj_global_id=subforum.get_global_id())
        return thread

    def _resolve_parent_thread(self, extracted, forum_type, forum_id):
        """Resolve thread parent object from extracted.thread."""
        thread_data = extracted.get('thread')
        if not thread_data or not thread_data.get('thread_id'):
            return None
        return ForumThread(f'{forum_id}/{thread_data.get("thread_id")}', forum_type)

    def _upsert_post(self, post_data, forum_type, forum_id, parent_thread, forum):
        """Create/update one Post object and add it to its thread timeline."""
        post_id = post_data.get('post_id')
        post_timestamp = self._safe_timestamp(post_data.get('post_timestamp'))
        if not post_id or post_timestamp is None or not parent_thread:
            return None, []
        ts_int = int(post_timestamp)
        obj_id = f'{forum_type}/{forum_id}/{ts_int}/{post_id}'
        post = Post(obj_id)
        post.set_content((post_data.get('content') or {}).get('text') or '')
        post._set_field('timestamp', str(post_timestamp))
        if post_data.get('post_state'):
            post.set_state(post_data.get('post_state'))
        # TODO CREATE MISSING FIELDS
        # post._set_field('custom', json.dumps({
        #     'url': post_data.get('post_url'),
        #     'html': (post_data.get('content') or {}).get('html'),
        #     'author_id': (post_data.get('author') or {}).get('author_id'),
        #     'author_username': (post_data.get('author') or {}).get('author_username'),
        #     'urls': (post_data.get('content') or {}).get('urls') or [],
        #     'images': (post_data.get('content') or {}).get('images') or [],
        #     'files': (post_data.get('content') or {}).get('files') or [],
        #     'reactions': post_data.get('reactions') or [],
        #     'post_timestamp_raw': post_data.get('post_timestamp_raw'),
        # }))
        # TODO REPLACE by functions
        quote_ids = (post_data.get('content') or {}).get('quoted_posts') or [] # TODO INVALID KEY
        # TODO USE SELF.Forum for the object
        parent_thread.add_post(post, post_id, post_timestamp, forum_obj, quote_ids=quote_ids)
        return post

    @staticmethod
    def _safe_timestamp(value):
        try:
            if value is None:
                return None
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _to_date_int(timestamp):
        return int(datetime.datetime.utcfromtimestamp(float(timestamp)).strftime('%Y%m%d'))

def ingest_forum_extractor_result(result):
    """Convenience entrypoint to ingest a forum-extractor result dict."""
    return ForumExtractorFeeder(result).import_result()
