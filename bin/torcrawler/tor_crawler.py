#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import json
import redis
from TorSplashCrawler import TorSplashCrawler

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import crawlers

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('usage:', 'tor_crawler.py', 'uuid')
        exit(1)


    config_loader = ConfigLoader.ConfigLoader()
    redis_cache = config_loader.get_redis_conn("Redis_Cache")
    config_loader = None

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

    if crawler_options['cookiejar_uuid']:
        cookies = crawlers.load_crawler_cookies(crawler_options['cookiejar_uuid'], domain, crawler_type=service_type)
    else:
        cookies = []

    redis_cache.delete('crawler_request:{}'.format(uuid))

    try:
        crawler = TorSplashCrawler(splash_url, crawler_options)
        crawler.crawl(splash_url, service_type, crawler_options, date, requested_mode, url, domain, port, cookies, original_item)
    except Exception as e:
        print(e)
        print(e, file=sys.stderr)
