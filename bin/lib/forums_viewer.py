#!/usr/bin/python3

"""
Chats Viewer
===================


"""
import os
import sys
import time
import uuid

from datetime import datetime, timezone

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects import Forums
from lib.objects import Subforums
from lib.objects import ForumThreads
from lib.objects import Posts
# from lib.objects.BarCodes import Barcode
# from lib.objects.QrCodes import Qrcode
# from lib.objects.Ocrs import Ocr
from lib.objects import UsersAccount
from lib.objects import Usernames
from lib import Language
from lib import Tag
from packages import Date

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_obj = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

def get_forums():
    return Forums.get_forums()

#### API ####

def api_get_forums_meta():
    forums = []
    for forum_id in get_forums():
        forums.append(Forums.Forum(forum_id).get_meta({'forum_type', 'info', 'name', 'orphan_subforums', 'subforums', 'url'}, flask_context=True))


if __name__ == '__main__':
    pass
