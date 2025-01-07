#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest

from pyail import PyAIL, PyAILError

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_users
from lib import ail_logger
from lib.ConfigLoader import ConfigLoader

test_logger = ail_logger.get_test_config(create=True)

class TestApiV1(unittest.TestCase):

    def setUp(self):
        config = ConfigLoader()
        port = config.get_config_str('Flask', 'port')
        try:
            self.ail = PyAIL(f'https://localhost:{port}', ail_users.get_user_token('admin@admin.test'), ssl=False)
        except Exception as e:
            print()
            print('----------------------------------------------------')
            test_logger.warning(f'Flask / Web interface is unreachable: {e}')
            print('----------------------------------------------------')
            print()
            raise e

    # GET /api/v1/ping
    def test_0001_api_ping(self):
        print()
        print('----------------------------------------------------')
        try:
            r = self.ail.ping()
            self.assertEqual(r.get('status'), 'pong')
            test_logger.info('AIL successfully reached Flask / Web interface')
        except (AssertionError, PyAILError) as ae:
            test_logger.warning(f'Flask / Web interface is unreachable: {ae}')
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
