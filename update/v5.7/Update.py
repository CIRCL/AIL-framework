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
from lib import ail_users
from lib import Investigations
from lib.ConfigLoader import ConfigLoader
from lib import chats_viewer

class Updater(AIL_Updater):
    """default Updater."""

    def __init__(self, version):
        super(Updater, self).__init__(version)


if __name__ == '__main__':
    config_loader = ConfigLoader()
    r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
    config_loader = None
    date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # ORGS
    # TODO CREATE DEFAULT ORG

    # USERS
    print('Updating Users ...')
    for user_id in ail_users.get_users():  # TODO ORG
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'creator', 'admin@admin.test')
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'created_at', date)
        r_serv_db.hset(f'ail:user:metadata:{user_id}', 'last_edit', date)

    # INVESTIGATIONS
    print('Updating Investigations ...')
    for inv_uuid in Investigations.get_all_investigations():  # TODO Creator ORG
        inv = Investigations.Investigation(inv_uuid)
        inv.set_level(1, None)

    chats_viewer.fix_chats_with_messages()

    updater = Updater('v5.7')
    updater.run_update()

