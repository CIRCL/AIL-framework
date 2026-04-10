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

# Config
config_loader = ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

class Updater(AIL_Updater):
    """default Updater."""

    def __init__(self, version):
        super(Updater, self).__init__(version)


if __name__ == '__main__':
    updater = Updater('v6.8')
    updater.run_update()
    ail_updates.add_background_update('v6.8')
