#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
Update AIL
============================

Update AIL in the background

"""

import os
import sys
import subprocess

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_updates

def launch_background_upgrade(version, l_script_name):
    if ail_updates.is_version_in_background_update(version):
        ail_updates.start_background_update(version)

        for script_name in l_script_name:
            ail_updates.set_current_background_update_script(script_name)
            update_file = ail_updates.get_current_background_update_script_path(version, script_name)

            # # TODO: Get error output
            process = subprocess.run(['python' ,update_file])

        update_progress = ail_updates.get_current_background_update_progress()
        if update_progress == 100:
            ail_updates.end_background_update_script()
        # # TODO: Create Custom error
        # 'Please relaunch the bin/update-background.py script'
        # # TODO: Create Class background update

        ail_updates.end_background_update()

if __name__ == "__main__":

    if not ail_updates.exits_background_update_to_launch():
        ail_updates.clear_background_update()
    else:
        launch_background_upgrade('v1.5', ['Update-ARDB_Onions.py', 'Update-ARDB_Metadata.py', 'Update-ARDB_Tags.py', 'Update-ARDB_Tags_background.py', 'Update-ARDB_Onions_screenshots.py'])
        launch_background_upgrade('v2.4', ['Update_domain.py'])
        launch_background_upgrade('v2.6', ['Update_screenshots.py'])
        launch_background_upgrade('v2.7', ['Update_domain_tags.py'])
        launch_background_upgrade('v3.4', ['Update_domain.py'])
        launch_background_upgrade('v3.7', ['Update_trackers.py'])
