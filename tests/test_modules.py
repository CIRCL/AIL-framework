#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest

sys.path.append(os.environ['AIL_BIN'])

# Modules Classes
from Onion import Onion

# projects packages
import lib.crawlers as crawlers

class Test_Module_Onion(unittest.TestCase):

    def setUp(self):
        self.module_obj = Onion()

    def test_module(self):
        item_id = 'tests/2021/01/01/onion.gz'
        domain_1 = 'eswpccgr5xyovsahffkehgleqthrasfpfdblwbs4lstd345dwq5qumqd.onion'
        domain_2 = 'www.facebookcorewwwi.onion'
        crawlers.queue_test_clean_up('onion', domain_1, 'tests/2021/01/01/onion.gz')

        self.module_obj.compute(f'{item_id} 3')
        if crawlers.is_crawler_activated():
            ## check domain queues
            # all domains queue
            self.assertTrue(crawlers.is_domain_in_queue('onion', domain_1))
            # all url/item queue
            self.assertTrue(crawlers.is_item_in_queue('onion', f'http://{domain_1}', item_id))
            # domain blacklist
            self.assertFalse(crawlers.is_domain_in_queue('onion', domain_2))
            # invalid onion
            self.assertFalse(crawlers.is_domain_in_queue('onion', 'invalid.onion'))

            # clean DB
            crawlers.queue_test_clean_up('onion', domain_1, 'tests/2021/01/01/onion.gz')
        else:
            # # TODO: check warning logs
            pass
