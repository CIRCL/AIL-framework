#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import sys,os

sys.path.append(os.environ['AIL_BIN'])

from Helper import Process

class TestHelper(unittest.TestCase):

    def setUp(self):

        config_section = 'Keys'


    def test_Process_Constructor_using_key_module(self):

        conf_section = 'Keys'
        process = Process(conf_section)
        self.assertEqual(process.subscriber_name, 'Keys')
