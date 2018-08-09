#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import configparser
from TorSplashCrawler import TorSplashCrawler

if __name__ == '__main__':

    if len(sys.argv) != 4:
        print('usage:', 'tor_crawler.py', 'url', 'paste', 'super_father')
        exit(1)

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    splash_url = cfg.get("Crawler", "splash_url")
    http_proxy = cfg.get("Crawler", "http_proxy")
    crawler_depth_limit = cfg.getint("Crawler", "crawler_depth_limit")

    url = sys.argv[1]
    paste = sys.argv[2]
    super_father = sys.argv[3]

    crawler = TorSplashCrawler(splash_url, http_proxy, crawler_depth_limit)
    crawler.crawl(url, paste, super_father)
