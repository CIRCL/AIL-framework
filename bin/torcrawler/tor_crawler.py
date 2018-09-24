#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import configparser
from TorSplashCrawler import TorSplashCrawler

if __name__ == '__main__':

    if len(sys.argv) != 7:
        print(sys.argv)
        print('usage:', 'tor_crawler.py', 'splash_url', 'type', 'url', 'domain', 'paste', 'super_father')
        exit(1)

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    splash_url = sys.argv[1]
    type = sys.argv[2]
    crawler_depth_limit = cfg.getint("Crawler", "crawler_depth_limit")

    url = sys.argv[3]
    domain = sys.argv[4]
    paste = sys.argv[5]
    super_father = sys.argv[6]

    crawler = TorSplashCrawler(splash_url, crawler_depth_limit)
    crawler.crawl(type, url, domain, paste, super_father)
