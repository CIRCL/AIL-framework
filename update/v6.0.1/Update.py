#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

sys.path.append(os.environ['AIL_HOME'])
##################################
# Import Project packages
##################################
from update.bin.ail_updater import AIL_Updater
from lib import ail_users
from lib import crawlers
from lib import Investigations
from lib import Tracker

def _fix_user_lowercase():
    r_tracking = Investigations.r_tracking
    r_tracker = Tracker.r_tracker
    r_crawler = crawlers.r_crawler

    for user_id in ail_users.get_users():
        l_user_id = user_id.lower()
        if user_id != l_user_id:
            print(f'Updating {user_id} ...')
            ail_users.kill_session_user(user_id)

            # Investigations
            for investigation_uuid in Investigations.get_user_all_investigations(user_id):
                r_tracking.srem(f'investigations:user:{user_id}', investigation_uuid)
                r_tracking.sadd(f'investigations:user:{l_user_id}', investigation_uuid)
                r_tracking.hset(f'investigations:data:{investigation_uuid}', 'creator_user', l_user_id)

            # Trackers
            for tracker_uuid in Tracker.get_user_trackers(user_id):
                tracker = Tracker.Tracker(tracker_uuid)
                tracker_type = tracker.get_type()

                r_tracker.rename(f'user:tracker:{user_id}:{tracker_type}', f'user:tracker:{l_user_id}:{tracker_type}')
                r_tracker.rename(f'user:tracker:{user_id}', f'user:tracker:{l_user_id}')

                # creator
                r_tracker.hset(f'tracker:{tracker_uuid}', 'user_id', l_user_id)

            try:
                r_tracker.rename(f'trackers:user:{user_id}', f'trackers:user:{l_user_id}')
            except Exception:
                pass

            # Cookiejar
            for cookiejar_uuid in crawlers.get_cookiejars_user(user_id):
                cookiejar = crawlers.Cookiejar(cookiejar_uuid)
                # creator
                cookiejar._set_user(l_user_id)

            try:
                r_crawler.rename(f'cookiejars:user:{user_id}', f'cookiejars:user:{l_user_id}')
            except Exception:
                pass

            # ail_user
            ail_users._fix_user_lowercase(user_id)


class Updater(AIL_Updater):
    """default Updater."""

    def __init__(self, version):
        super(Updater, self).__init__(version)


if __name__ == '__main__':
    _fix_user_lowercase()
    updater = Updater('v6.0.1')
    updater.run_update()
