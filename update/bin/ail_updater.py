#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import time
import redis
import datetime

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

class AIL_Updater(object):
    """docstring for AIL_Updater."""

    def __init__(self, new_version):
        self.version = new_version
        self.start_time = time.time()

        self.config = ConfigLoader.ConfigLoader()
        self.r_serv = self.config.get_redis_conn("ARDB_DB")

        self.f_version = float(self.version[1:])
        self.current_f_version = self.r_serv.get('ail:version')
        if self.current_f_version:
            self.current_f_version = float(self.current_f_version[1:])
        else:
            self.current_f_version = 0

    def update(self):
        """
        AIL DB update
        """
        pass

    def end_update(self):
        """
        Update DB version
        """
        #Set current ail version
        self.r_serv.hset('ail:update_date', self.version, datetime.datetime.now().strftime("%Y%m%d"))
        #Set current ail version
        if self.f_version > self.current_f_version:
            self.r_serv.set('ail:version', self.version)

    def run_update(self):
        self.update()
        self.end_update()
