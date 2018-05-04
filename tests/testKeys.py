#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys,os
import unittest
import magic

sys.path.append(os.environ['AIL_BIN'])

from packages.Paste import Paste
import Keys as Keys
from Helper import Process
from pubsublogger import publisher


class TestKeysModule(unittest.TestCase):

    def setUp(self):
        self.paste = Paste('../samples/2018/01/01/keys_certificat_sample.gz')

        # Section name in bin/packages/modules.cfg
        self.config_section = 'Keys'

        # Setup the I/O queues
        p = Process(self.config_section)


    def test_search_key(self):
        with self.assertRaises(pubsublogger.exceptions.NoChannelError):
            Keys.search_key(self.paste)

    def test_search_key(self):
        with self.assertRaises(NameError):
            publisher.port = 6380
            publisher.channel = 'Script'
            Keys.search_key(self.paste)
