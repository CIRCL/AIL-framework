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

sys.path.append(os.path.join(os.environ['AIL_HOME'], 'update', 'bin'))
from ail_updater import AIL_Updater

class Updater(AIL_Updater):
    """default Updater."""

    def __init__(self, version):
        super(Updater, self).__init__(version)
        self.r_serv_onion = self.config.get_redis_conn("ARDB_Onion")

    def update(self):
        """
        Update Domain Languages
        """
        self.r_serv_onion.sunionstore('domain_update_v3.4', 'full_onion_up', 'full_regular_up')
        self.r_serv.set('update:nb_elem_to_convert', self.r_serv_onion.scard('domain_update_v3.4'))
        self.r_serv.set('update:nb_elem_converted',0)

        # Add background update
        self.r_serv.sadd('ail:to_update', self.version)

if __name__ == '__main__':

    updater = Updater('v3.4')
    updater.run_update()
