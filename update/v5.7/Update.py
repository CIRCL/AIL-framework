#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from datetime import datetime

sys.path.append(os.environ['AIL_HOME'])
##################################
# Import Project packages
##################################
from update.bin.ail_updater import AIL_Updater
from lib import ail_orgs
from lib import ail_users
from lib import Investigations
from lib.ConfigLoader import ConfigLoader
from lib import chats_viewer
from lib import Tracker

class Updater(AIL_Updater):
    """default Updater."""

    def __init__(self, version):
        super(Updater, self).__init__(version)


if __name__ == '__main__':
    config_loader = ConfigLoader()
    r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
    config_loader = None
    date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # USERS
    print('Updating Users ...')
    # create role_list
    ail_users._create_roles()

    # Create Default Org
    org = ail_orgs.create_default_org()
    org_uuid = org.get_uuid()

    for user_id in ail_users.get_users():
        if ail_users.get_user_role(user_id) == 'analyst':
            ail_users.set_user_role(user_id, 'user')
        ail_users.edit_user('admin@admin.test', user_id, org_uuid=org_uuid)
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'creator', 'admin@admin.test')
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'created_at', date)
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'last_edit', date)
        r_serv_db.srem(f'ail:users:role:analyst', user_id)
        user_role = ail_users.get_user_role(user_id)
        ail_users.set_user_role(user_id, user_role)
        # ADD User to ORG
        org.add_user(user_id)

    # INVESTIGATIONS
    print('Updating Investigations ...')
    for inv_uuid in Investigations.get_all_investigations():
        inv = Investigations.Investigation(inv_uuid)
        inv.set_level(1, None)
        inv._set_field('creator_org', org_uuid)

    print('Updating Trackers ...')
    for tracker_uuid in Tracker.get_trackers():
        tracker = Tracker.Tracker(tracker_uuid)
        tracker._set_field('creator_org', org_uuid)

    print('Updating Retro Hunts ...')
    for retro_hunt_uuid in Tracker.get_all_retro_hunt_tasks():
        retro = Tracker.RetroHunt(retro_hunt_uuid)
        retro.set_level(1, None)
        retro._set_field('creator_org', org_uuid)

    chats_viewer.fix_chats_with_messages()

    updater = Updater('v5.7')
    updater.run_update()

