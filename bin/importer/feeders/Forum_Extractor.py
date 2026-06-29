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
class Forum_ExtractorFeeder(DefaultFeeder):
    """Ingest forum-extractor output into AIL forum objects."""

    def __init__(self, json_data):
        super().__init__(json_data)
        self.name = 'forum-extractor'
        self.logger = logging.getLogger(self.__class__.__name__)
        self.forum = None
        self.seen_subforums = set()
        self.root_subforums = set()
        self.objs_to_process = set()

    def process_meta(self):
        """Import one forum-extractor result dictionary from self.json_meta."""
        meta = self.get_meta()
        status = meta.get('status')

        if status == 'success':
            objs = self._import_success(meta)
            print(objs)
            return objs
        if status == 'unsupported_page_type':
            self.logger.error(f"Forum extractor unsupported page type: {meta.get('page_type')}")
            return set()
        if status == 'error':
            self.logger.error(f"Forum extractor parser error: {meta.get('error')}", meta.get('error'))
            return set()

        self.logger.error(f'Forum extractor unknown status: {status}')
        return set()

    def _import_success(self, result):
        """Import a successful parser result payload."""
        forum_type = result.get('forum_type')
        forum_id = result.get('forum_id')
        extracted = result.get('extracted') or {}

        if not forum_type or not forum_id:
            # TODO Exception + logs
            return {'status': 'error', 'imported': 0, 'error': 'missing_forum_type_or_forum_id'}

        self.seen_subforums = set()
        self.root_subforums = set()

        # Forum
        self.forum = self._upsert_forum(result, extracted, forum_type, forum_id)
        if not self.forum:  # TODO ERROR EXIT + logs
            return {'status': 'error', 'imported': 0, 'error': 'forum_upsert_failed'}

        self.process_forum_hierarchy(result)

        # if view is subforum
        parent_subforum = self._upsert_subforum(extracted.get('parent_subforum'))
        current_subforum = self._upsert_subforum(extracted.get('current_subforum'))
        if parent_subforum and current_subforum:
            self._set_parent_once(current_subforum, parent_subforum.get_global_id())
            self.forum.remove_orphan_subforum(current_subforum.get_global_id())

        # Import SubForums
        for sub in extracted.get('subforums') or []:
            if result.get('page_type') == 'forum_index':
                self._upsert_subforum_recursive(sub, self.forum, root=True)
            else:
                self._upsert_subforum_recursive(sub, current_subforum or parent_subforum)

        self._mark_seen_subforum_orphans()

        imported = {'forum': 1, 'subforum': 0, 'forum-thread': 0, 'post': 0}

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
                print(post.id)
                self.objs_to_process.add(post)
        if posts:
            last_post = posts[-1]
            last_timestamp = int(last_post.get('post_timestamp'))
            self.forum.update_thread_last_time(parent_thread.id, int(last_timestamp))

        # TODO REMOVE ME ###############################################################################################
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
        print({'status': 'success', 'imported': imported})
        return self.objs_to_process

    def _upsert_forum(self, result, extracted, forum_type, forum_id):
        """Create/update a Forum object from extracted data."""
        forum = Forum(forum_id)
        return forum.create(forum_type)

    def process_forum_hierarchy(self, result):
        """Consume parser hierarchy edges before thread/post parent fallback logic."""
        for edge in (result.get('extracted') or {}).get('forum_hierarchy') or []:
            self.ensure_hierarchy_edge(edge)

    def ensure_hierarchy_edge(self, edge):
        """Create objects referenced by one hierarchy edge and set the child parent."""
        parent_type = edge.get('parent_type')
        child_type = edge.get('child_type')
        if (parent_type, child_type) not in {
            ('forum', 'subforum'),
            ('subforum', 'subforum'),
            ('subforum', 'forum-thread'),
        }:
            self.logger.warning(f'Invalid hierarchy type: parent {parent_type}, child {child_type}')
            return None

        parent_id = edge.get('parent_id')
        child_id = edge.get('child_id')
        if not parent_id or not child_id:
            self.logger.warning(f'Invalid hierarchy edge id: parent {parent_id}, child {child_id}')
            return None

        parent_obj = self.create_hierarchy_object(edge)
        child_obj = self.create_hierarchy_object(edge, parent=False)

        if self._set_parent_once(child_obj, parent_obj.get_global_id()):
            if parent_obj.type == 'subforum':
                parent_obj._add_subtype()
            if child_obj.type == 'subforum':
                child_obj._add_subtype()
                self.forum.remove_orphan_subforum(child_obj.get_global_id())
                if parent_type == 'forum':
                    self.root_subforums.add(child_obj.get_global_id())
            return child_obj
        return None

    def create_hierarchy_object(self, hierarchy, parent=True):
        if parent:
            str_name = 'parent_'
        else:
            str_name = 'child_'
        obj_type = hierarchy.get(f'{str_name}type')
        obj_id = hierarchy.get(f'{str_name}id')
        name = hierarchy.get(f'{str_name}name')

        if obj_type == 'forum':
            return self.forum
        if obj_type == 'subforum':
            subforum = Subforum(obj_id, self.forum.id)
            subforum.create(name=name)
            self.seen_subforums.add(subforum.get_global_id())
            return subforum
        if obj_type == 'forum-thread':
            thread = ForumThread(obj_id, self.forum.id)
            thread.create()
            return thread
        return None

    def _upsert_subforum_recursive(self, sub_data, parent_obj=None, root=False):
        """Recursively create/update subforums and parent links."""
        subforum = self._upsert_subforum(sub_data)
        if not subforum:
            return
        if parent_obj:
            if self._set_parent_once(subforum, parent_obj.get_global_id()):
                self.forum.remove_orphan_subforum(subforum.get_global_id())
                if root and parent_obj.get_type() == 'forum':
                    self.root_subforums.add(subforum.get_global_id())
        for child in sub_data.get('subforums') or []:
            self._upsert_subforum_recursive(child, subforum)

    def _upsert_subforum(self, sub_data):
        """Create/update one Subforum object without inventing a parent."""
        if not sub_data or not sub_data.get('subforum_id'):
            return None
        subforum = Subforum(sub_data.get('subforum_id'), self.forum.id)
        subforum.create(
            name=sub_data.get('subforum_name'),
            url=sub_data.get('subforum_url'),
            info=sub_data.get('info'),
        )
        self.seen_subforums.add(subforum.get_global_id())
        return subforum

    def _upsert_thread(self, thread_data, subforum):
        """Create/update one ForumThread object and set parent subforum when available."""
        if not thread_data or not thread_data.get('thread_id'):
            return None
        thread = ForumThread(thread_data.get('thread_id'), self.forum.id)
        if subforum:
            self._set_parent_once(thread, subforum.get_global_id())
        if not thread.get_parent():
            self.logger.warning(f'ForumThread has no parent for {thread.get_global_id()}')
            return None
        thread.create(
            name=thread_data.get('thread_title'),
            url=thread_data.get('thread_url'),
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

    def _set_parent_once(self, child_obj, parent_global_id):
        existing_parent = child_obj.get_parent()
        if existing_parent == parent_global_id:
            return True
        if existing_parent:
            self.logger.warning(f'Hierarchy parent conflict for {child_obj.get_global_id()}: existing={existing_parent} new={parent_global_id}')
            return False
        child_obj.set_parent(obj_global_id=parent_global_id)
        return True

    def _mark_seen_subforum_orphans(self):
        for subforum_global_id in self.seen_subforums:
            if subforum_global_id in self.root_subforums:
                continue
            _, _, obj_id = subforum_global_id.split(':', 2)
            subforum = Subforum(obj_id, self.forum.id)
            if not subforum.get_parent():
                self.forum.add_orphan_subforum(subforum_global_id)

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
        obj_id = f'{self.forum.id}/{ts_int}/{post_id}'
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
        content = (post_data.get('content') or {}).get('text')
        post.create(post_id, post_timestamp, content, parent_thread, self.forum, state=post_data.get('post_state'), quote_ids=quote_ids)
        user_account = self._create_post_user_account(post_data.get('author'), post, post_timestamp)
        return post

    # TODO A POST MUST HAVE AN USER ACCOUNT
    def _create_post_user_account(self, author, post, timestamp):
        """Create/update the post author user-account and username metadata."""
        if not author or not author.get('author_id'):
            return None
        username = author.get('author_username')
        user_id = str(author.get('author_id'))
        # user without id are set to 0
        if user_id == '0' and username:
            user_id = username.lower()
        user_account = UserAccount(user_id, self.forum.id)
        if username:
            username = Username(username.lower(), self.forum.id)
        else:
            username = None
        user_account.create(post.get_date(), post, username, timestamp)
        user_account.add_correlation('forum', '', self.forum.id)
        return user_account

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

# TODO SEND TO IMPORTER MODULE ????
def ingest_forum_extractor_result(result):
    """Convenience entrypoint to ingest a forum-extractor result dict."""
    return Forum_ExtractorFeeder(result).process_meta()
