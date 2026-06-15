#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest

if 'AIL_BIN' not in os.environ:
    os.environ['AIL_BIN'] = os.path.join(os.getcwd(), 'bin')
sys.path.append(os.environ['AIL_BIN'])

from lib.objects.Forums import Forum, r_object


class TestForumCrawlQueue(unittest.TestCase):

    def setUp(self):
        self.forum_id = 'test-forum-crawl-queue.local'
        self.forum = Forum(self.forum_id)
        self.keys = [
            f'forum:crawl:queue:{self.forum_id}',
            f'forum:crawl:items:{self.forum_id}',
            f'forum:crawl:queued:{self.forum_id}',
            f'forum:crawl:inflight:{self.forum_id}',
            f'forum:crawl:thread:account:{self.forum_id}',
            f'forum:crawl:config:subforums:excluded:{self.forum_id}',
            f'forum:crawl:config:subforums:to_crawl:{self.forum_id}',
            f'forum:crawl:account:subforums:{self.forum_id}:acc_1',
            f'forum:crawl:account:{self.forum_id}:acc_1',
            f'forum:crawl:accounts:{self.forum_id}',
            f'meta:forum:{self.forum_id}',
            f'child:subforum:{self.forum_id}:27',
            f'child:subforum:{self.forum_id}:28',
            f'meta:subforum:{self.forum_id}:28',
            f'meta:subforum:{self.forum_id}:29',
        ]
        self._cleanup()

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        for key in self.keys:
            r_object.delete(key)

    def _item(self, crawl_key='forum-thread:777:page:3', page=3):
        return {
            'crawl_key': crawl_key,
            'type': 'forum-thread',
            'id': '777',
            'parent': {
                'type': 'subforum',
                'id': '27',
            },
            'page': page,
            'url': 'https://forum0.com/threads/example.777/page-3',
            'referer': 'https://forum0.com/forums/example.27/',
            'preferred_account_ids': ['acc_1'],
            'preferred_account_fallback': False,
        }

    def test_validate_good_crawl_item(self):
        self.assertEqual(self.forum.validate_crawl_item(self._item()), (True, None))

    def test_validate_reject_missing_crawl_key(self):
        item = self._item()
        item.pop('crawl_key')
        self.assertEqual(self.forum.validate_crawl_item(item), (False, 'missing_crawl_key'))

    def test_validate_reject_invalid_type(self):
        item = self._item()
        item['type'] = 'post'
        self.assertEqual(self.forum.validate_crawl_item(item), (False, 'invalid_type'))

    def test_validate_reject_missing_id(self):
        item = self._item()
        item.pop('id')
        self.assertEqual(self.forum.validate_crawl_item(item), (False, 'missing_id'))

    def test_validate_reject_invalid_page(self):
        item = self._item(page=0)
        self.assertEqual(self.forum.validate_crawl_item(item), (False, 'invalid_page'))
        item = self._item(page='1')
        self.assertEqual(self.forum.validate_crawl_item(item), (False, 'invalid_page'))

    def test_enqueue_crawl_item(self):
        item = self._item()
        crawl_key = item['crawl_key']
        self.assertEqual(self.forum.enqueue_crawl_item(item, score=1), (True, None))
        self.assertEqual(r_object.zrange(self.keys[0], 0, -1), [crawl_key])
        self.assertTrue(r_object.sismember(self.keys[2], crawl_key))
        self.assertTrue(r_object.hexists(self.keys[1], crawl_key))

    def test_enqueue_duplicate_crawl_item(self):
        item = self._item()
        crawl_key = item['crawl_key']
        self.assertEqual(self.forum.enqueue_crawl_item(item, score=1), (True, None))
        self.assertEqual(self.forum.enqueue_crawl_item(item, score=2), (False, 'already_queued'))
        self.assertEqual(r_object.zrange(self.keys[0], 0, -1), [crawl_key])

    def test_get_crawl_item(self):
        item = self._item()
        self.forum.enqueue_crawl_item(item, score=1)
        stored = self.forum.get_crawl_item(item['crawl_key'])
        self.assertEqual(stored['crawl_key'], item['crawl_key'])
        self.assertEqual(stored['type'], item['type'])
        self.assertEqual(stored['parent'], item['parent'])
        self.assertNotIn('forum_id', stored)
        self.assertEqual(stored['preferred_account_ids'], ['acc_1'])

    def test_reserve_crawl_item(self):
        item = self._item()
        crawl_key = item['crawl_key']
        self.forum.enqueue_crawl_item(item, score=1)
        reserved, payload = self.forum.reserve_crawl_item(crawl_key, 'acc_1')
        self.assertTrue(reserved)
        self.assertEqual(payload['crawl_key'], crawl_key)
        self.assertEqual(r_object.zrange(self.keys[0], 0, -1), [])
        self.assertTrue(r_object.sismember(self.keys[2], crawl_key))
        self.assertTrue(r_object.hexists(self.keys[3], crawl_key))
        self.assertTrue(r_object.hexists(self.keys[1], crawl_key))

    def test_reserve_non_pending_item(self):
        self.assertEqual(self.forum.reserve_crawl_item('missing', 'acc_1'), (False, 'not_pending'))

    def test_complete_crawl_item(self):
        item = self._item()
        crawl_key = item['crawl_key']
        self.forum.enqueue_crawl_item(item, score=1)
        self.forum.reserve_crawl_item(crawl_key, 'acc_1')
        self.assertEqual(self.forum.complete_crawl_item(crawl_key), (True, None))
        self.assertFalse(r_object.zscore(self.keys[0], crawl_key))
        self.assertFalse(r_object.sismember(self.keys[2], crawl_key))
        self.assertFalse(r_object.hexists(self.keys[1], crawl_key))
        self.assertFalse(r_object.hexists(self.keys[3], crawl_key))

    def test_fail_crawl_item(self):
        item = self._item()
        crawl_key = item['crawl_key']
        self.forum.enqueue_crawl_item(item, score=1)
        self.forum.reserve_crawl_item(crawl_key, 'acc_1')
        self.assertEqual(self.forum.fail_crawl_item(crawl_key, error='failed'), (True, None))
        self.assertFalse(r_object.zscore(self.keys[0], crawl_key))
        self.assertFalse(r_object.sismember(self.keys[2], crawl_key))
        self.assertFalse(r_object.hexists(self.keys[1], crawl_key))
        self.assertFalse(r_object.hexists(self.keys[3], crawl_key))

    def test_pending_count(self):
        item_1 = self._item(crawl_key='forum-thread:777:page:1', page=1)
        item_2 = self._item(crawl_key='forum-thread:777:page:2', page=2)
        self.forum.enqueue_crawl_item(item_1, score=1)
        self.forum.enqueue_crawl_item(item_2, score=2)
        self.assertEqual(self.forum.get_nb_pending_crawl_items(), 2)
        self.forum.reserve_crawl_item(item_1['crawl_key'], 'acc_1')
        self.assertEqual(self.forum.get_nb_pending_crawl_items(), 1)

    def test_inflight_count(self):
        item = self._item()
        crawl_key = item['crawl_key']
        self.forum.enqueue_crawl_item(item, score=1)
        self.forum.reserve_crawl_item(crawl_key, 'acc_1')
        self.assertEqual(self.forum.get_nb_inflight_crawl_items(), 1)
        self.forum.complete_crawl_item(crawl_key)
        self.assertEqual(self.forum.get_nb_inflight_crawl_items(), 0)

    def _forum_item(self):
        return {
            'crawl_key': 'forum:index:page:1',
            'type': 'forum',
            'id': self.forum_id,
            'page': 1,
            'url': 'https://forum0.com/',
        }

    def _subforum_item(self, subforum_id='27'):
        return {
            'crawl_key': f'subforum:{subforum_id}:page:1',
            'type': 'subforum',
            'id': subforum_id,
            'page': 1,
            'url': f'https://forum0.com/forums/{subforum_id}/',
        }

    def _enable_forum(self, subforums_to_crawl=None, subforums_excluded=None):
        self.forum.set_crawl_config({
            'enabled': True,
            'javascript': False,
            'subforums_to_crawl': subforums_to_crawl or [],
            'subforums_excluded': subforums_excluded or [],
        })

    def _set_subforum_parent(self, subforum_id, parent_id):
        from lib.objects.Subforums import Subforum
        Subforum(subforum_id, self.forum_id).set_parent(obj_global_id=f'subforum:{self.forum_id}:{parent_id}')

    def test_forum_scope_allows_forum_item_when_enabled(self):
        self._enable_forum()
        self.assertEqual(self.forum.forum_allows_crawl_item(self._forum_item()), (True, 'allowed'))

    def test_forum_scope_rejects_when_disabled(self):
        self.forum.set_crawl_config({'enabled': False, 'javascript': False})
        self.assertEqual(self.forum.forum_allows_crawl_item(self._forum_item()), (False, 'forum_disabled'))

    def test_forum_scope_rejects_excluded_subforum(self):
        self._enable_forum(subforums_excluded=['27'])
        self.assertEqual(self.forum.forum_allows_crawl_item(self._subforum_item('27')), (False, 'excluded_subforum'))

    def test_forum_scope_allows_subforum_when_roots_empty(self):
        self._enable_forum()
        self.assertEqual(self.forum.forum_allows_crawl_item(self._subforum_item('27')), (True, 'allowed'))

    def test_forum_scope_allows_direct_root(self):
        self._enable_forum(subforums_to_crawl=['27'])
        self.assertEqual(self.forum.forum_allows_crawl_item(self._subforum_item('27')), (True, 'allowed'))

    def test_forum_scope_allows_descendant_root(self):
        self._enable_forum(subforums_to_crawl=['27'])
        self._set_subforum_parent('28', '27')
        self._set_subforum_parent('29', '28')
        self.assertEqual(self.forum.forum_allows_crawl_item(self._subforum_item('29')), (True, 'allowed'))

    def test_forum_scope_rejects_outside_roots(self):
        self._enable_forum(subforums_to_crawl=['27'])
        self.assertEqual(self.forum.forum_allows_crawl_item(self._subforum_item('29')), (False, 'outside_forum_scope'))

    def test_account_scope_allows_when_roots_empty(self):
        self.assertEqual(self.forum.account_allows_crawl_item('acc_1', self._subforum_item('27')), (True, 'allowed'))

    def test_account_scope_allows_direct_root(self):
        self.forum.add_crawl_account('acc_1', {'enabled': True, 'subforums_to_crawl': ['27']})
        self.assertEqual(self.forum.account_allows_crawl_item('acc_1', self._subforum_item('27')), (True, 'allowed'))

    def test_account_scope_allows_descendant_root(self):
        self.forum.add_crawl_account('acc_1', {'enabled': True, 'subforums_to_crawl': ['27']})
        self._set_subforum_parent('28', '27')
        self.assertEqual(self.forum.account_allows_crawl_item('acc_1', self._subforum_item('28')), (True, 'allowed'))

    def test_account_scope_rejects_outside_root(self):
        self.forum.add_crawl_account('acc_1', {'enabled': True, 'subforums_to_crawl': ['27']})
        self.assertEqual(self.forum.account_allows_crawl_item('acc_1', self._subforum_item('29')), (False, 'outside_account_scope'))

    def test_preferred_account_routing(self):
        item = self._item()
        item.pop('preferred_account_ids')
        self.assertEqual(self.forum.preferred_account_allows_item('acc_2', item), (True, 'allowed'))
        item['preferred_account_ids'] = ['acc_1']
        self.assertEqual(self.forum.preferred_account_allows_item('acc_1', item), (True, 'allowed'))
        self.assertEqual(self.forum.preferred_account_allows_item('acc_2', item), (False, 'not_preferred_account'))
        item['preferred_account_fallback'] = True
        self.assertEqual(self.forum.preferred_account_allows_item('acc_2', item), (True, 'allowed_fallback'))

    def test_thread_affinity(self):
        self.assertEqual(self.forum.thread_affinity_allows_account('777', 'acc_1'), (True, 'allowed'))
        self.forum.set_thread_crawl_account('777', 'acc_1')
        self.assertEqual(self.forum.thread_affinity_allows_account('777', 'acc_1'), (True, 'allowed'))
        self.assertEqual(self.forum.thread_affinity_allows_account('777', 'acc_2'), (False, 'thread_assigned_to_other_account'))

    def test_reserve_crawl_item_for_account_sets_affinity_and_inflight(self):
        self._enable_forum()
        item = self._item()
        crawl_key = item['crawl_key']
        self.forum.enqueue_crawl_item(item, score=1)
        reserved, payload = self.forum.reserve_crawl_item_for_account(crawl_key, 'acc_1')
        self.assertTrue(reserved)
        self.assertEqual(payload['crawl_key'], crawl_key)
        self.assertEqual(self.forum.get_thread_crawl_account('777'), 'acc_1')
        self.assertTrue(r_object.hexists(self.keys[3], crawl_key))
        self.assertEqual(r_object.zrange(self.keys[0], 0, -1), [])

    def test_reserve_crawl_item_for_account_rejects_other_thread_account(self):
        self._enable_forum()
        item = self._item(crawl_key='forum-thread:777:page:4', page=4)
        item['preferred_account_ids'] = ['acc_2']
        self.forum.enqueue_crawl_item(item, score=1)
        self.forum.set_thread_crawl_account('777', 'acc_1')
        self.assertEqual(self.forum.reserve_crawl_item_for_account(item['crawl_key'], 'acc_2'), (False, 'thread_assigned_to_other_account'))

    def test_reserve_crawl_item_for_account_releases_new_affinity_on_reserve_failure(self):
        from unittest.mock import patch
        self._enable_forum()
        item = self._item()
        self.forum.enqueue_crawl_item(item, score=1)
        with patch.object(self.forum, 'reserve_crawl_item', return_value=(False, 'not_pending')):
            self.assertEqual(self.forum.reserve_crawl_item_for_account(item['crawl_key'], 'acc_1'), (False, 'not_pending'))
        self.assertIsNone(self.forum.get_thread_crawl_account('777'))

    def test_fail_crawl_item_releases_thread_affinity(self):
        item = self._item()
        self.forum.enqueue_crawl_item(item, score=1)
        self.forum.reserve_crawl_item(item['crawl_key'], 'acc_1')
        self.forum.set_thread_crawl_account('777', 'acc_1')
        self.forum.fail_crawl_item(item['crawl_key'], error='failed')
        self.assertIsNone(self.forum.get_thread_crawl_account('777'))

    def test_fail_crawl_item_keeps_other_queued_thread_pages(self):
        item_1 = self._item(crawl_key='forum-thread:777:page:1', page=1)
        item_2 = self._item(crawl_key='forum-thread:777:page:2', page=2)
        self.forum.enqueue_crawl_item(item_1, score=1)
        self.forum.enqueue_crawl_item(item_2, score=2)
        self.forum.reserve_crawl_item(item_1['crawl_key'], 'acc_1')
        self.forum.set_thread_crawl_account('777', 'acc_1')
        self.forum.fail_crawl_item(item_1['crawl_key'], error='failed')
        self.assertEqual(self.forum.get_pending_crawl_keys(0, -1), [item_2['crawl_key']])


if __name__ == '__main__':
    unittest.main()
