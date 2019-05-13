#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import json
import redis
import configparser
from TorSplashCrawler import TorSplashCrawler

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('usage:', 'tor_crawler.py', 'uuid')
        exit(1)

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    redis_cache = redis.StrictRedis(
        host=cfg.get("Redis_Cache", "host"),
        port=cfg.getint("Redis_Cache", "port"),
        db=cfg.getint("Redis_Cache", "db"),
        decode_responses=True)

    # get crawler config key
    uuid = sys.argv[1]

    # get configs
    crawler_json = json.loads(redis_cache.get('crawler_request:{}'.format(uuid)))

    splash_url = crawler_json['splash_url']
    service_type = crawler_json['service_type']
    url = crawler_json['url']
    domain = crawler_json['domain']
    port = crawler_json['port']
    original_item = crawler_json['item']
    crawler_options = crawler_json['crawler_options']
    date = crawler_json['date']
    requested_mode = crawler_json['requested']

    redis_cache.delete('crawler_request:{}'.format(uuid))

    crawler = TorSplashCrawler(splash_url, crawler_options)
    crawler.crawl(service_type, crawler_options, date, requested_mode, url, domain, port, original_item)
