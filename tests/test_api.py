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
from lib import Users

sys.path.append(os.environ['AIL_FLASK'])
sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'modules'))

class TestApiV1(unittest.TestCase):

    def setUp(self):
        # TODO GET HOST + PORT
        self.ail = PyAIL('https://localhost:7000', Users.get_user_token('admin@admin.test'), ssl=False)

    # GET /api/v1/ping
    def test_0001_api_ping(self):
        r = self.ail.ping_ail()
        self.assertEqual(r.get('status'), 'pong')

    # # GET /api/v1/uuid
    # def test_0001_api_uuid(self):
    #     r = self.ail.get_uuid()
    #
    # # GET /api/v1/version
    # def test_0001_api_version(self):
    #     r = self.ail.get_version()


if __name__ == "__main__":
    unittest.main(exit=False)
