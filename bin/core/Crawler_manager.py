#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import json
import os
import sys

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader
import crawlers

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

config_loader = ConfigLoader.ConfigLoader(config_file='crawlers.cfg')
SPLASH_MANAGER_URL = config_loader.get_config_str('Splash_Manager', 'splash_url')
api_key = config_loader.get_config_str('Splash_Manager', 'api_key')
crawlers_to_launch = config_loader.get_all_keys_values_from_section('Splash_Crawlers')
config_loader = None

import screen

if __name__ == '__main__':

    if not crawlers.ping_splash_manager():
        print('Error, Can\'t cnnect to Splash manager')

    crawlers.reload_splash_and_proxies_list()

    # # TODO: handle mutltiple splash_manager

    for crawler_splash in crawlers_to_launch:
        splash_name = crawler_splash[0]
        nb_crawlers = int(crawler_splash[1])

        all_crawler_urls = crawlers.get_splash_all_url(crawler_splash[0], r_list=True)
        if nb_crawlers > len(all_crawler_urls):
            print('Error, can\'t launch all Splash Dockers')
            print('Please launch {} additional {} Dockers'.format( nb_crawlers - len(all_crawler_urls), splash_name))
            nb_crawlers = len(all_crawler_urls)

        for i in range(0, int(nb_crawlers)):
            splash_url = all_crawler_urls[i]
            print(all_crawler_urls[i])

            crawlers.launch_ail_splash_crawler('http://127.0.0.1:8054', script_options='{} {}'.format(splash_name, splash_url))
