#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import redis

import Flask_config
import Date

PASTES_FOLDER = Flask_config.PASTES_FOLDER

def exist_item(item_id):
    if os.path.isfile(os.path.join(PASTES_FOLDER, item_id)):
        return True
    else:
        return False
