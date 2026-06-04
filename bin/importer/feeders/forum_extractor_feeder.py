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
from lib.objects.UsersAccount import UserAccount
from lib.objects.Usernames import Username

# TODO IMAGES + USER ACCOUNTS + FILENAMES
class ForumExtractorFeeder(DefaultFeeder):
    """Ingest forum-extractor output into AIL forum objects."""

    def __init__(self, json_data):
        super().__init__(json_data)
        self.name = 'forum-extractor'
        self.logger = logging.getLogger(self.__class__.__name__)
        self.forum = None

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
            # TODO Exception + logs
            return {'status': 'error', 'imported': 0, 'error': 'missing_forum_type_or_forum_id'}

        # Forum
        self.forum = self._upsert_forum(result, extracted, forum_type, forum_id)
        if not self.forum:  # TODO ERROR EXIT + logs
            return {'status': 'error', 'imported': 0, 'error': 'forum_upsert_failed'}

        parent_subforum = self._upsert_subforum(extracted.get('parent_subforum'))
        current_subforum = self._upsert_subforum(extracted.get('current_subforum'), parent_subforum)

        # Import SubForums
        for sub in extracted.get('subforums') or []:
            self._upsert_subforum_recursive(sub, current_subforum or parent_subforum)

        if not current_subforum and result.get('page_type') in {'thread_page', 'forum_thread_list'}:
            if extracted.get('thread') or extracted.get('threads'):
                return {'status': 'error', 'imported': 0, 'error': 'missing_current_subforum'}

        imported = {'forum': 1, 'subforum': 0, 'forum-thread': 0, 'post': 0}
        warnings = []

        # Import Threads
        thread_objs = []
        if extracted.get('thread'):
            thread_objs.append(extracted['thread'])
        thread_objs.extend(extracted.get('threads') or [])

        for thread_data in thread_objs:
            thread = self._upsert_thread(thread_data, current_subforum)
            if not thread:
                return {'status': 'error', 'imported': sum(imported.values()), 'error': 'thread_parent_missing'}
            imported['forum-thread'] += 1

        # Import Posts
        posts = extracted.get('posts') or []
        imported_posts = []
        parent_thread = self._resolve_parent_thread(extracted)  # TODO warning not created
        for post_data in posts:
            # TODO PASS SUBFORUMS LIST
            post = self._upsert_post(post_data, parent_thread)
            if post:
                imported_posts.append((post, post_data))
                imported['post'] += 1

        # TODO Avoid reprocess -> use add for subtype  and create correlation
        seen_timestamps = [self._safe_timestamp(p[1].get('post_timestamp')) for p in imported_posts if self._safe_timestamp(p[1].get('post_timestamp'))]
        if seen_timestamps:
            date_values = {
                self._to_date_int(min(seen_timestamps)),
                self._to_date_int(max(seen_timestamps)),
            }
            for date_value in date_values:
                if current_subforum:
                    current_subforum.update_daterange(date_value)

        return {'status': 'success', 'imported': imported, 'warnings': warnings}

    def _upsert_forum(self, result, extracted, forum_type, forum_id):
        """Create/update a Forum object from extracted data."""
        fdata = extracted.get('forum') or {}
        name = fdata.get('forum_name')
        url = fdata.get('forum_url') or result.get('url')
        info = fdata.get('info')
        forum = Forum(forum_id)
        return forum.create(forum_type, name, url, info)

    def _upsert_subforum_recursive(self, sub_data, parent_subforum=None):
        """Recursively create/update subforums and parent links."""
        subforum = self._upsert_subforum(sub_data, parent_subforum)
        if not subforum:
            return
        for child in sub_data.get('subforums') or []:
            self._upsert_subforum_recursive(child, subforum)

    def _upsert_subforum(self, sub_data, parent_subforum=None):
        """Create/update one Subforum object and set parent."""
        if not sub_data or not sub_data.get('subforum_id'):
            return None
        subforum = Subforum(sub_data.get("subforum_id"), self.forum.id)
        return subforum.create(
            name=sub_data.get('subforum_name'),
            url=sub_data.get('subforum_url'),
            info=sub_data.get('description') or sub_data.get('info'),
            parent_global_id=(parent_subforum or self.forum).get_global_id(),  # TODO #########################
        )

    def _upsert_thread(self, thread_data, subforum):
        """Create/update one ForumThread object and set parent subforum."""
        if not thread_data or not thread_data.get('thread_id'):
            return None
        if not subforum:
            return None
        thread = ForumThread(thread_data.get("thread_id"), self.forum.id)
        thread.create(
            title=thread_data.get('thread_title'),
            url=thread_data.get('thread_url'),
            parent_global_id=subforum.get_global_id(),
        )
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
        return thread

    # TODO REMOVE ME ???
    def _resolve_parent_thread(self, extracted):
        """Resolve thread parent object from extracted.thread."""
        thread_data = extracted.get('thread')
        if not thread_data or not thread_data.get('thread_id'):
            return None
        return ForumThread(thread_data.get("thread_id"), self.forum.id)

    def _upsert_post(self, post_data, parent_thread):
        """Create/update one Post object and add it to its thread timeline."""
        post_id = post_data.get('post_id')
        post_timestamp = self._safe_timestamp(post_data.get('post_timestamp'))
        if not post_id or post_timestamp is None or not parent_thread:
            return None, []
        ts_int = int(post_timestamp)
        obj_id = f'{self.forum.type}/{self.forum.id}/{ts_int}/{post_id}' # TODO REMOVE FORUM TYPE ?????
        post = Post(obj_id)
        # TODO CREATE MISSING FIELDS
        # post._set_field('custom', json.dumdumpsdumpsdumpsdumpsps({
        #     'url': post_data.get('post_url'),
        #     'author_id': (post_data.get('author') or {}).get('author_id'),
        #     'author_username': (post_data.get('author') or {}).get('author_username'),
        #     'urls': (post_data.get('content') or {}).get('urls') or [],
        #     'images': (post_data.get('content') or {}).get('images') or [],
        #     'files': (post_data.get('content') or {}).get('files') or [],
        #     'reactions': post_data.get('reactions') or [],
        # }))
        # TODO REPLACE by functions
        quote_ids = (post_data.get('content') or {}).get('quoted_posts') or []
        # TODO FUNCTION
        content = (post_data.get('content') or {}).get('text'),
        post.create(post_id, post_timestamp, content, parent_thread, self.forum, state=post_data.get('post_state'), quote_ids=quote_ids)
        self._create_post_user_account(post_data.get('author'), post, post_timestamp)
        return post

    # TODO A POST MUST HAVE AN USER ACCOUNT
    def _create_post_user_account(self, author, post, timestamp):
        """Create/update the post author user-account and username metadata."""
        if not author or not author.get('author_id'):
            return None
        user_account = UserAccount(str(author.get('author_id')), self.forum.id)
        username = author.get('author_username')
        if username:
            username = Username(username, self.forum.id)
        else:
            username = None
        return user_account.create(post.get_date(), post, username, timestamp)

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
