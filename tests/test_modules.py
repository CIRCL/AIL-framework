#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest

import gzip
from base64 import b64encode
from distutils.dir_util import copy_tree

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
# Modules Classes
from modules.ApiKey import ApiKey
from modules.Categ import Categ
from modules.CreditCards import CreditCards
from modules.DomClassifier import DomClassifier
from modules.Global import Global
from modules.Keys import Keys
from modules.Onion import Onion
from modules.Telegram import Telegram

# project packages
import lib.objects.Items as Items

#### COPY SAMPLES ####
config_loader = ConfigLoader()
ITEMS_FOLDER = Items.ITEMS_FOLDER
TESTS_ITEMS_FOLDER = os.path.join(ITEMS_FOLDER, 'tests')
sample_dir = os.path.join(os.environ['AIL_HOME'], 'samples')
copy_tree(sample_dir, TESTS_ITEMS_FOLDER)


#### ---- ####

class TestModuleApiKey(unittest.TestCase):

    def setUp(self):
        self.module = ApiKey()
        self.module.debug = True

    def test_module(self):
        item_id = 'tests/2021/01/01/api_keys.gz'
        self.module.obj = Items.Item(item_id)
        google_api_key = 'AIza00000000000000000000000_example-KEY'
        aws_access_key = 'AKIAIOSFODNN7EXAMPLE'
        aws_secret_key = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

        matches = self.module.compute('3', r_result=True)
        self.assertCountEqual(matches[0], {google_api_key})
        self.assertCountEqual(matches[1], {aws_access_key})
        self.assertCountEqual(matches[2], {aws_secret_key})


class TestModuleCateg(unittest.TestCase):

    def setUp(self):
        self.module = Categ()
        self.module.debug = True

    def test_module(self):
        item_id = 'tests/2021/01/01/categ.gz'
        self.module.obj = Items.Item(item_id)
        test_categ = ['CreditCards', 'Mail', 'Onion', 'Urls', 'Credential', 'Cve']

        result = self.module.compute(None, r_result=True)
        self.assertCountEqual(result, test_categ)


class TestModuleCreditCards(unittest.TestCase):

    def setUp(self):
        self.module = CreditCards()
        self.module.debug = True

    def test_module(self):
        item_id = 'tests/2021/01/01/credit_cards.gz'
        self.module.obj = Items.Item(item_id)
        test_cards = ['341039324930797',   # American Express
                      '6011613905509166',  # Discover Card
                      '3547151714018657',  # Japan Credit Bureau (JCB)
                      '5492981206527330',  # 16 digits MasterCard
                      '4024007132849695',  # '4532525919781' # 16-digit VISA, with separators
                      ]

        result = self.module.compute('7', r_result=True)
        self.assertCountEqual(result, test_cards)


class TestModuleDomClassifier(unittest.TestCase):

    def setUp(self):
        self.module = DomClassifier()
        self.module.debug = True

    def test_module(self):
        test_host = 'foo.be'
        item_id = 'tests/2021/01/01/domain_classifier.gz'
        self.module.obj = Items.Item(item_id)
        result = self.module.compute(f'{test_host}', r_result=True)
        self.assertTrue(len(result))


class TestModuleGlobal(unittest.TestCase):

    def setUp(self):
        self.module = Global()
        self.module.debug = True

    def test_module(self):
        # # TODO: delete item
        item_id = 'tests/2021/01/01/global.gz'
        item = Items.Item(item_id)
        item.delete()

        item_content = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit'
        item_content_1 = b64encode(gzip.compress(item_content)).decode()
        item_content_2 = b64encode(gzip.compress(item_content + b' more text ...')).decode()

        self.module.obj = Items.Item(item_id)
        # Test new item
        result = self.module.compute(item_content_1, r_result=True)
        self.assertEqual(result, item_id)

        # Test duplicate
        result = self.module.compute(item_content_1, r_result=True)
        self.assertIsNone(result)

        # Test same id with != content
        item = Items.Item('tests/2021/01/01/global_831875da824fc86ab5cc0e835755b520.gz')
        item.delete()
        result = self.module.compute(item_content_2, r_result=True)
        self.assertIn(item_id[:-3], result)
        self.assertNotEqual(result, item_id)

        # cleanup
        # item = Items.Item(result)
        # item.delete()
        # # TODO: remove from queue


class TestModuleKeys(unittest.TestCase):

    def setUp(self):
        self.module = Keys()
        self.module.debug = True

    def test_module(self):
        item_id = 'tests/2021/01/01/keys.gz'
        self.module.obj = Items.Item(item_id)
        # # TODO: check results
        self.module.compute(None)


class TestModuleOnion(unittest.TestCase):

    def setUp(self):
        self.module = Onion()
        self.module.debug = True

    def test_module(self):
        item_id = 'tests/2021/01/01/onion.gz'
        self.module.obj = Items.Item(item_id)
        # domain_1 = 'eswpccgr5xyovsahffkehgleqthrasfpfdblwbs4lstd345dwq5qumqd.onion'
        # domain_2 = 'www.facebookcorewwwi.onion'

        self.module.compute(f'3')


class TestModuleTelegram(unittest.TestCase):

    def setUp(self):
        self.module = Telegram()
        self.module.debug = True

    def test_module(self):
        item_id = 'tests/2021/01/01/keys.gz'
        self.module.obj = Items.Item(item_id)
        # # TODO: check results
        self.module.compute(None)


if __name__ == '__main__':
    unittest.main()
