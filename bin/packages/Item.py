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

def get_item_date(item_id):
    l_directory = item_id.split('/')
    return '{}{}{}'.format(l_directory[-4], l_directory[-3], l_directory[-2])
