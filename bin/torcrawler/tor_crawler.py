#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import configparser
from TorSplashCrawler import TorSplashCrawler

if __name__ == '__main__':

    if len(sys.argv) != 8:
        print('usage:', 'tor_crawler.py', 'splash_url', 'http_proxy', 'type', 'url', 'domain', 'paste', 'super_father')
        exit(1)

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    splash_url = sys.argv[1]
    http_proxy = sys.argv[2]
    type = sys.argv[3]
    crawler_depth_limit = cfg.getint("Crawler", "crawler_depth_limit")

    url = sys.argv[4]
    domain = sys.argv[5]
    paste = sys.argv[6]
    super_father = sys.argv[7]

    crawler = TorSplashCrawler(splash_url, http_proxy, crawler_depth_limit)
    crawler.crawl(type, url, domain, paste, super_father)
