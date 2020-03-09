#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import gzip
import base64
import uuid
import datetime
import base64
import redis
import json
import time

from hashlib import sha256

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
from twisted.web._newclient import ResponseNeverReceived

from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.crawler import CrawlerProcess, Crawler

from scrapy_splash import SplashRequest, SplashJsonResponse

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader

# script_lua_cookie = """
# function main(splash, args)
#
#   -- default config
#   -- load flash plugin
#   splash.plugins_enabled = true
#   splash.html5_media_enabled = true
#
#   -- to check
#   splash.request_body_enabled = true
#   splash.response_body_enabled = true
#
#   -- handle cookies
#   splash:init_cookies(args.cookies)
#
#   assert(splash:go{
#     args.url,
#     headers=args.headers,
#     http_method=args.http_method,
#     body=args.body
#     })
#
#   splash:wait(10)
#
#   -- Response
#   return {
#     url = splash:url(),
#     html = splash:html(),
#     har = splash:har(),
#     cookies = splash:get_cookies(),
#     png = splash:png(render_all=true)
#   }
# end
# """


script_cookie = """
function main(splash, args)
    -- Default values
    splash.js_enabled = true
    splash.private_mode_enabled = true
    splash.images_enabled = true
    splash.webgl_enabled = true
    splash.media_source_enabled = true
    -- Force enable things
    splash.plugins_enabled = true
    splash.request_body_enabled = true
    splash.response_body_enabled = true
    -- Would be nice
    splash.indexeddb_enabled = true
    splash.html5_media_enabled = true
    splash.http2_enabled = true
    -- User defined
    splash.resource_timeout = args.resource_timeout
    splash.timeout = args.timeout

   -- Allow to pass cookies
    splash:init_cookies(args.cookies)
    -- Run
    ok, reason = splash:go{args.url}
    if not ok then
        return {error = reason}
    end
    splash:wait{args.wait}
    -- Page instrumentation
    -- splash.scroll_position = {y=1000}
    splash:wait{args.wait}
    -- Response
    return {
        har = splash:har(),
        html = splash:html(),
        png = splash:png{render_all=true},
        cookies = splash:get_cookies()
    }
end
"""

class TorSplashCrawler():

    def __init__(self, splash_url, crawler_options):
        self.process = CrawlerProcess({'LOG_ENABLED': True})
        self.crawler = Crawler(self.TorSplashSpider, {
            'USER_AGENT': crawler_options['user_agent'],
            'SPLASH_URL': splash_url,
            'ROBOTSTXT_OBEY': False,
            'DOWNLOADER_MIDDLEWARES': {'scrapy_splash.SplashCookiesMiddleware': 723,
                                       'scrapy_splash.SplashMiddleware': 725,
                                       'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
                                       'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
                                       },
            'SPIDER_MIDDLEWARES': {'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,},
            'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
            'HTTPERROR_ALLOW_ALL': True,
            'RETRY_TIMES': 0,
            'CLOSESPIDER_PAGECOUNT': crawler_options['closespider_pagecount'],
            'DEPTH_LIMIT': crawler_options['depth_limit'],
            'SPLASH_COOKIES_DEBUG': True
            })

    def crawl(self, type, crawler_options, date, requested_mode, url, domain, port, cookies, original_item):
        self.process.crawl(self.crawler, type=type, crawler_options=crawler_options, date=date, requested_mode=requested_mode, url=url, domain=domain, port=port, cookies=cookies, original_item=original_item)
        self.process.start()

    class TorSplashSpider(Spider):
        name = 'TorSplashSpider'

        def __init__(self, type, crawler_options, date, requested_mode, url, domain, port, cookies, original_item, *args, **kwargs):
            self.type = type
            self.requested_mode = requested_mode
            self.original_item = original_item
            self.root_key = None
            self.start_urls = url
            self.domains = [domain]
            self.port = str(port)
            date_str = '{}/{}/{}'.format(date['date_day'][0:4], date['date_day'][4:6], date['date_day'][6:8])
            self.full_date = date['date_day']
            self.date_month = date['date_month']
            self.date_epoch = int(date['epoch'])

            print(requested_mode)
            self.png = True
            self.har = True

            self.cookies = cookies

        def build_request_arg(self, cookies):
            return {'wait': 10,
                    'resource_timeout': 10,
                    'timeout': 30,
                    'cookies': cookies,
                    'lua_source': script_cookie
                }

        def start_requests(self):
            l_cookies = self.build_request_arg(self.cookies)
            yield SplashRequest(
                self.start_urls,
                self.parse,
                errback=self.errback_catcher,
                endpoint='execute',
                #meta={'father': self.original_item, 'root_key': None},
                args=l_cookies
                #session_id="foo"
            )

        def parse(self,response):
            #print(response.headers)
            #print(response.status)
            if response.status == 504:
                # down ?
                print('504 detected')
            elif response.status != 200:
                print('other response: {}'.format(response.status))
                #print(error_log)
                #detect connection to proxy refused
                error_log = (json.loads(response.body.decode()))
                if(error_log['info']['text'] == 'Connection to proxy refused'):
                    print('Connection to proxy refused')
            else:
                # DEBUG:
                print('----')
                print(response.data.keys())

                # LUA Script Errors
                if 'error' in response.data:
                    print(response.data['error'])
                else:
                    print(response.data['html'])
                    pass

                #print(response.data['cookies'])
                if 'cookies' in response.data:
                    all_cookies = response.data['cookies']
                    for cookie in all_cookies:
                        print('------------------------')
                        print(cookie['name'])
                        print(cookie['value'])
                        print(cookie)
                    # for cookie in all_cookies:
                    #     print(cookie.name)
                else:
                    all_cookies = []


                #    if 'png' in response.data:


                #if 'har' in response.data:

                le = LinkExtractor(allow_domains=self.domains, unique=True)
                for link in le.extract_links(response):
                    l_cookies = self.build_request_arg(all_cookies)
                    yield SplashRequest(
                        link.url,
                        self.parse,
                        errback=self.errback_catcher,
                        endpoint='execute',
                        #meta={'father': 'inter', 'root_key': response.meta['root_key'], 'session_id': '092384901834adef'},
                        #meta={'father': 'inter', 'root_key': 'ido', 'session_id': '092384901834adef'},
                        args=l_cookies
                        #session_id="foo"
                    )

        def errback_catcher(self, failure):
            # catch all errback failures,
            self.logger.error(repr(failure))

            if failure.check(ResponseNeverReceived):
                request = failure.request
                #url = request.meta['splash']['args']['url']
                url= 'ido'
                #father = request.meta['father']
                father = 'ido'

                self.logger.error('Splash, ResponseNeverReceived for %s, retry in 10s ...', url)
                time.sleep(10)
                if response:
                    response_root_key = response.meta['root_key']
                else:
                    response_root_key = None
                yield SplashRequest(
                    url,
                    self.parse,
                    errback=self.errback_catcher,
                    endpoint='execute',
                    cache_args=['lua_source'],
                    #meta={'father': father, 'root_key': response.meta['root_key']},
                    #meta={'father': father, 'root_key': 'ido'},
                    args=self.build_request_arg(response.cookiejar)
                    #session_id="foo"
                )

            else:
                print('failure')
                #print(failure)
                print(failure.type)
                #print(failure.request.meta['item'])
