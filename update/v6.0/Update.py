#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

sys.path.append(os.environ['AIL_HOME'])
##################################
# Import Project packages
##################################
from update.bin.ail_updater import AIL_Updater
from lib.ConfigLoader import ConfigLoader
from lib import ail_updates

class Updater(AIL_Updater):
    """default Updater."""

    def __init__(self, version):
        super(Updater, self).__init__(version)


if __name__ == '__main__':
    config_loader = ConfigLoader()
    r_queues = config_loader.get_redis_conn("Redis_Queues")
    config_loader = None
    r_queues.delete('modules')
    updater = Updater('v6.0')
    updater.run_update()
