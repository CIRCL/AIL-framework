#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
#import item_basic

config_loader = ConfigLoader.ConfigLoader()
r_serv_tracker = config_loader.get_redis_conn("ARDB_Tracker")
config_loader = None

def get_tracker_description(tracker_uuid):
    return r_serv_tracker.hget('tracker:{}'.format(term_uuid), 'description')

def get_email_subject(tracker_uuid):
    tracker_description = get_tracker_description(tracker_uuid)
    if not tracker_description:
        return "AIL framework: Tracker Alert"
    else:
        return 'AIL framework: {}'.format(tracker_description)
