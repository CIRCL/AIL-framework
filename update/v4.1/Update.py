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

    def update(self):
        r_tracking = redis.StrictRedis( host=localhost,
                                  port=6382),
                                  db=2,
                                  decode_responses=True )

        # FLUSH OLD DB
        r_tracking.flushdb()

if __name__ == '__main__':

    updater = Updater('v4.1')


    updater.run_update()
