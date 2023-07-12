#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
Update AIL
============================

Update AIL in the background

"""

import os
import logging
import logging.config
import sys
import subprocess

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_logger
from lib import ail_updates

logging.config.dictConfig(ail_logger.get_config(name='updates'))
def launch_background_upgrade(version):
    logger = logging.getLogger()
    logger.warning(f'launching background update {version}')
    update = ail_updates.AILBackgroundUpdate(version)
    nb_done = update.get_nb_scripts_done()
    update.start()
    scripts = update.get_scripts()
    scripts = scripts[nb_done:]
    for script in scripts:
        print('launching background script update', script)
        # launch script
        update.start_script(script)
        script_path = update.get_script_path()
        if script_path:
            try:
                process = subprocess.run(['python', script_path])
                if process.returncode != 0:
                    stderr = process.stderr
                    if stderr:
                        error = stderr.decode()
                        logger.error(error)
                        update.set_error(error)
                    else:
                        update.set_error('Error Updater Script')
                        logger.error('Error Updater Script')
                    sys.exit(0)
            except Exception as e:
                update.set_error(str(e))
                logger.error(str(e))
                sys.exit(0)

        if not update.get_error():
            update.end_script()
        else:
            logger.warning('Updater exited on error')
            sys.exit(0)

    update.end()
    logger.warning(f'ending background update {version}')


if __name__ == "__main__":
    if ail_updates.is_update_background_running():
        v = ail_updates.get_update_background_version()
        launch_background_upgrade(v)
    else:
        for ver in ail_updates.get_update_background_to_launch():
            launch_background_upgrade(ver)
