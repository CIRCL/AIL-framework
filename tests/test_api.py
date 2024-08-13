#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest

from pyail import PyAIL

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_users

from lib.ConfigLoader import ConfigLoader

class TestApiV1(unittest.TestCase):

    def setUp(self):
        config = ConfigLoader()
        port = config.get_config_str('Flask', 'port')
        self.ail = PyAIL(f'https://localhost:{port}', ail_users.get_user_token('admin@admin.test'), ssl=False)

    # GET /api/v1/ping
    def test_0001_api_ping(self):
        r = self.ail.ping_ail()
        self.assertEqual(r.get('status'), 'pong')
        print()
        print('----------------------------------------------------')
        print('  AIL successfully reached Flask / Web interface')
        print('----------------------------------------------------')
        print()

    # # GET /api/v1/uuid
    # def test_0001_api_uuid(self):
    #     r = self.ail.get_uuid()
    #
    # # GET /api/v1/version
    # def test_0001_api_version(self):
    #     r = self.ail.get_version()


if __name__ == "__main__":
    unittest.main(exit=False)
