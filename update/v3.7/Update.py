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
import Tracker

sys.path.append(os.path.join(os.environ['AIL_HOME'], 'update', 'bin'))
from old_ail_updater import AIL_Updater

class Updater(AIL_Updater):
    """default Updater."""

    def __init__(self, version):
        super(Updater, self).__init__(version)

    def update(self):
        """
        Update Domain Languages
        """
        print('Fixing Tracker_uuid list ...')
        Tracker.fix_all_tracker_uuid_list()
        nb = 0
        for tracker_uuid in Tracker.get_all_tracker_uuid():
            self.r_serv.sadd('trackers_update_v3.7', tracker_uuid)
            nb += 1

        self.r_serv.set('update:nb_elem_to_convert', nb)
        self.r_serv.set('update:nb_elem_converted',0)

        # Add background update
        self.r_serv.sadd('ail:to_update', self.version)

if __name__ == '__main__':

    updater = Updater('v3.7')
    updater.run_update()
