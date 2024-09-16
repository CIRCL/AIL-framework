#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_updates
from lib.ConfigLoader import ConfigLoader
from packages.git_status import clear_git_meta_cache

class AIL_Updater(object):
    """docstring for AIL_Updater."""

    def __init__(self, new_version):
        self.version = new_version
        self.start_time = time.time()

        self.config = ConfigLoader()
        self.r_serv = self.config.get_db_conn("Kvrocks_DB")

        self.f_version = float(self.version[1:])
        self.current_f_version = ail_updates.get_ail_float_version()
        clear_git_meta_cache()

    def update(self):
        """
        AIL DB update
        """
        pass

    def end_update(self):
        """
        Update DB version
        """
        ail_updates.add_ail_update(self.version)

    def run_update(self):
        self.update()
        self.end_update()
