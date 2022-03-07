#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

class User(object):
    """AIL User."""

    def __init__(self, id):
        self.id = id
        if self.id == '__anonymous__':
            self.role = 'anonymous'
        else:
            self.role = None

    def get_role(self):
        pass

    
