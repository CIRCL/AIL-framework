#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest

import gzip
from base64 import b64encode

sys.path.append(os.environ['AIL_BIN'])

# Modules Classes
from ApiKey import ApiKey
from Categ import Categ
from CreditCards import CreditCards
from DomClassifier import DomClassifier
from Global import Global
from Keys import Keys
from Onion import Onion

# project packages
import lib.crawlers as crawlers
import packages.Item as Item

class Test_Module_ApiKey(unittest.TestCase):

    def setUp(self):
        self.module_obj = ApiKey()

    def test_module(self):
        item_id = 'tests/2021/01/01/api_keys.gz'
        google_api_key = 'AIza00000000000000000000000_example-KEY'
        aws_access_key = 'AKIAIOSFODNN7EXAMPLE'
        aws_secret_key = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

        matches = self.module_obj.compute(f'{item_id} 3', r_result=True)
        self.assertCountEqual(matches[0], [google_api_key])
        self.assertCountEqual(matches[1], [aws_access_key])
        self.assertCountEqual(matches[2], [aws_secret_key])

class Test_Module_Categ(unittest.TestCase):

    def setUp(self):
        self.module_obj = Categ()

    def test_module(self):
        item_id = 'tests/2021/01/01/categ.gz'
        test_categ = ['CreditCards', 'Mail', 'Onion', 'Web', 'Credential', 'Cve']

        result = self.module_obj.compute(item_id, r_result=True)
        self.assertCountEqual(result, test_categ)

class Test_Module_CreditCards(unittest.TestCase):

    def setUp(self):
        self.module_obj = CreditCards()

    def test_module(self):
        item_id = 'tests/2021/01/01/credit_cards.gz 7'
        test_cards = ['341039324930797', # American Express
                        '6011613905509166', # Discover Card
                        '3547151714018657', # Japan Credit Bureau (JCB)
                        '5492981206527330', # 16 digits MasterCard
                        '4024007132849695', # '4532525919781' # 16-digit VISA, with separators
                     ]

        result = self.module_obj.compute(item_id, r_result=True)
        self.assertCountEqual(result, test_cards)

class Test_Module_DomClassifier(unittest.TestCase):

    def setUp(self):
        self.module_obj = DomClassifier()

    def test_module(self):
        item_id = 'tests/2021/01/01/domain_classifier.gz'
        result = self.module_obj.compute(item_id, r_result=True)
        self.assertTrue(len(result))

class Test_Module_Global(unittest.TestCase):

    def setUp(self):
        self.module_obj = Global()

    def test_module(self):
        # # TODO: delete item
        item_id = 'tests/2021/01/01/global.gz'
        item = Item.Item(item_id)
        item.delete()

        item_content = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit'
        item_content_1 = b64encode(gzip.compress(item_content)).decode()
        item_content_2 = b64encode(gzip.compress(item_content + b' more text')).decode()
        message = f'{item_id} {item_content_1}'

        # Test new item
        result = self.module_obj.compute(message, r_result=True)
        print(result)
        self.assertEqual(result, item_id)

        # Test duplicate
        result = self.module_obj.compute(message, r_result=True)
        print(result)
        self.assertIsNone(result)

        # Test same id with != content
        message = f'{item_id} {item_content_2}'
        result = self.module_obj.compute(message, r_result=True)
        print(result)
        self.assertIn(item_id[:-3], result)
        self.assertNotEqual(result, item_id)

        # cleanup
        item = Item.Item(result)
        item.delete()
        # # TODO: remove from queue

class Test_Module_Keys(unittest.TestCase):

    def setUp(self):
        self.module_obj = Keys()

    def test_module(self):
        item_id = 'tests/2021/01/01/keys.gz'
        # # TODO: check results
        result = self.module_obj.compute(item_id)

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

if __name__ == '__main__':
    unittest.main()
