#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
Update AIL
============================

Update AIL in the background

"""

import os
import sys
import redis
import subprocess

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

def launch_background_upgrade(version, l_script_name):
    if r_serv.sismember('ail:to_update', version):
        r_serv.delete('ail:update_error')
        r_serv.set('ail:update_in_progress', version)
        r_serv.set('ail:current_background_update', version)

        for script_name in l_script_name:
            r_serv.set('ail:current_background_script', script_name)
            update_file = os.path.join(os.environ['AIL_HOME'], 'update', version, script_name)
            process = subprocess.run(['python' ,update_file])
            update_progress = r_serv.get('ail:current_background_script_stat')
            #if update_progress:
            #    if int(update_progress) != 100:
            #        r_serv.set('ail:update_error', 'Update {} Failed'.format(version))

        update_progress = r_serv.get('ail:current_background_script_stat')
        if update_progress:
            if int(update_progress) == 100:
                r_serv.delete('ail:update_in_progress')
                r_serv.delete('ail:current_background_script')
                r_serv.delete('ail:current_background_script_stat')
                r_serv.delete('ail:current_background_update')
                r_serv.srem('ail:to_update', version)

def clean_update_db():
    r_serv.delete('ail:update_error')
    r_serv.delete('ail:update_in_progress')
    r_serv.delete('ail:current_background_script')
    r_serv.delete('ail:current_background_script_stat')
    r_serv.delete('ail:current_background_update')

if __name__ == "__main__":

    config_loader = ConfigLoader.ConfigLoader()

    r_serv = config_loader.get_redis_conn("ARDB_DB")
    r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
    config_loader = None

    if r_serv.scard('ail:to_update') == 0:
        clean_update_db()


    launch_background_upgrade('v1.5', ['Update-ARDB_Onions.py', 'Update-ARDB_Metadata.py', 'Update-ARDB_Tags.py', 'Update-ARDB_Tags_background.py', 'Update-ARDB_Onions_screenshots.py'])
    launch_background_upgrade('v2.4', ['Update_domain.py'])
    launch_background_upgrade('v2.6', ['Update_screenshots.py'])
    launch_background_upgrade('v2.7', ['Update_domain_tags.py'])
    launch_background_upgrade('v3.4', ['Update_domain.py'])
