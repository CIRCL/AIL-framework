#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader
import crawlers

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

# # TODO: lauch me in core screen
# # TODO: check if already launched in tor screen

# # TODO: handle mutltiple splash_manager
if __name__ == '__main__':

    is_manager_connected = crawlers.ping_splash_manager()
    if not is_manager_connected:
        print('Error, Can\'t connect to Splash manager')
        session_uuid = None
    else:
        print('Splash manager connected')
        session_uuid = crawlers.get_splash_manager_session_uuid()
        is_manager_connected = crawlers.reload_splash_and_proxies_list()
        print(is_manager_connected)
        if is_manager_connected:
            if crawlers.test_ail_crawlers():
                crawlers.relaunch_crawlers()
    last_check = int(time.time())

    while True:

        # # TODO: avoid multiple ping

        # check if manager is connected
        if int(time.time()) - last_check > 60:
            is_manager_connected = crawlers.is_splash_manager_connected()
            current_session_uuid = crawlers.get_splash_manager_session_uuid()
            # reload proxy and splash list
            if current_session_uuid and current_session_uuid != session_uuid:
                is_manager_connected = crawlers.reload_splash_and_proxies_list()
                if is_manager_connected:
                    print('reload proxies and splash list')
                    if crawlers.test_ail_crawlers():
                        crawlers.relaunch_crawlers()
                    session_uuid = current_session_uuid
            if not is_manager_connected:
                print('Error, Can\'t connect to Splash manager')
            last_check = int(time.time())

            # # TODO: lauch crawlers if was never connected
        # refresh splash and proxy list
        elif False:
            crawlers.reload_splash_and_proxies_list()
            print('list of splash and proxies refreshed')
        else:
            time.sleep(5)

        # kill/launch new crawler / crawler manager check if already launched


    # # TODO: handle mutltiple splash_manager
    # catch reload request
