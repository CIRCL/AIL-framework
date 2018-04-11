#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import magic

from bin.packages.Paste import Paste
import bin.Keys as Keys
from bin.Helper import Process
import pubsublogger


class TestKeysModule(unittest.TestCase):

    def setUp(self):
        self.paste = Paste('samples/2018/01/01/keys_certificat_sample.gz')

        # Section name in bin/packages/modules.cfg
        self.config_section = 'Keys'

        # Setup the I/O queues
        p = Process(self.config_section)


    def test_search_key(self):
        with self.assertRaises(pubsublogger.exceptions.NoChannelError):
            Keys.search_key(self.paste)
