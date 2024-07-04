#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import json
import sys
import logging

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

LOGGING_CONFIG = os.path.join(os.environ['AIL_HOME'], 'configs', 'logging.json')

def get_config(name=None):
    if not name:
        name = 'ail.log'
    else:
        name = f'{name}.log'
    with open(LOGGING_CONFIG, 'r') as f:
        config = json.load(f)
        config['handlers']['file']['filename'] = os.path.join(os.environ['AIL_HOME'], 'logs', name)
    return config
