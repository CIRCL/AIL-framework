#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

sys.path.append(os.environ['AIL_HOME'])
##################################
# Import Project packages
##################################
from update.bin.old_ail_updater import AIL_Updater

class Updater(AIL_Updater):
    """default Updater."""

    def __init__(self, version):
        super(Updater, self).__init__(version)

    def update(self):
        r_tracking = redis.StrictRedis(host='localhost',
                                       port=6382,
                                       db=2,
                                       decode_responses=True)
        # FLUSH OLD DB
        r_tracking.flushdb()


if __name__ == '__main__':
    updater = Updater('v4.1')
    updater.run_update()
