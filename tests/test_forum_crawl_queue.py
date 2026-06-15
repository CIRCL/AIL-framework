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


if __name__ == '__main__':
    unittest.main()
