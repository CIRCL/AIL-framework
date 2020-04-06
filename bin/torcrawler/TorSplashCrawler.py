#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid
import datetime
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
#import ConfigLoader
import Screenshot
import crawlers

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
    if not ok and not reason:find("http") then
        return {
            error = reason,
            last_url = splash:url()
        }
    end
    if reason == "http504" then
        splash:set_result_status_code(504)
        return ''
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
        cookies = splash:get_cookies(),
        last_url = splash:url()
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
            'RETRY_TIMES': 2,
            'CLOSESPIDER_PAGECOUNT': crawler_options['closespider_pagecount'],
            'DEPTH_LIMIT': crawler_options['depth_limit'],
            'SPLASH_COOKIES_DEBUG': False
            })

    def crawl(self, type, crawler_options, date, requested_mode, url, domain, port, cookies, original_item):
        self.process.crawl(self.crawler, type=type, crawler_options=crawler_options, date=date, requested_mode=requested_mode, url=url, domain=domain, port=port, cookies=cookies, original_item=original_item)
        self.process.start()

    class TorSplashSpider(Spider):
        name = 'TorSplashSpider'

        def __init__(self, type, crawler_options, date, requested_mode, url, domain, port, cookies, original_item, *args, **kwargs):
            self.domain_type = type
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

            self.png = crawler_options['png']
            self.har = crawler_options['har']
            self.cookies = cookies

            config_section = 'Crawler'
            self.p = Process(config_section)
            self.item_dir = os.path.join(self.p.config.get("Directories", "crawled"), date_str )
            self.har_dir = os.path.join(os.environ['AIL_HOME'], self.p.config.get("Directories", "crawled_screenshot"), date_str )
            self.r_serv_log_submit = redis.StrictRedis(
                host=self.p.config.get("Redis_Log_submit", "host"),
                port=self.p.config.getint("Redis_Log_submit", "port"),
                db=self.p.config.getint("Redis_Log_submit", "db"),
                decode_responses=True)

            self.root_key = None

        def build_request_arg(self, cookies):
            return {'wait': 10,
                    'resource_timeout': 30, # /!\ Weird behaviour if timeout < resource_timeout /!\
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
                meta={'father': self.original_item, 'current_url': self.start_urls},
                args=l_cookies
            )

        # # TODO: remove duplicate and anchor
        def parse(self,response):
            #print(response.headers)
            #print(response.status)
            if response.status == 504:
                # no response
                #print('504 detected')
                pass

            # LUA ERROR # # TODO: print/display errors
            elif 'error' in response.data:
                if(response.data['error'] == 'network99'):
                    ## splash restart ##
                    error_retry = request.meta.get('error_retry', 0)
                    if error_retry < 3:
                        error_retry += 1
                        url= request.meta['current_url']
                        father = request.meta['father']

                        self.logger.error('Splash, ResponseNeverReceived for %s, retry in 10s ...', url)
                        time.sleep(10)
                        yield SplashRequest(
                            url,
                            self.parse,
                            errback=self.errback_catcher,
                            endpoint='execute',
                            cache_args=['lua_source'],
                            meta={'father': father, 'current_url': url, 'error_retry': error_retry},
                            args=self.build_request_arg(response.cookiejar)
                        )
                    else:
                        print('Connection to proxy refused')
                else:
                    print(response.data['error'])

            elif response.status != 200:
                print('other response: {}'.format(response.status))
                # detect connection to proxy refused
                error_log = (json.loads(response.body.decode()))
                print(error_log)
            #elif crawlers.is_redirection(self.domains[0], response.data['last_url']):
            #    pass # ignore response
            else:

                item_id = crawlers.create_item_id(self.item_dir, self.domains[0])
                self.save_crawled_item(item_id, response.data['html'])
                crawlers.create_item_metadata(item_id, self.domains[0], response.data['last_url'], self.port, response.meta['father'])

                if self.root_key is None:
                    self.root_key = item_id
                    crawlers.add_domain_root_item(item_id, self.domain_type, self.domains[0], self.date_epoch, self.port)
                    crawlers.create_domain_metadata(self.domain_type, self.domains[0], self.port, self.full_date, self.date_month)

                if 'cookies' in response.data:
                    all_cookies = response.data['cookies']
                else:
                    all_cookies = []

                # SCREENSHOT
                if 'png' in response.data:
                    sha256_string = Screenshot.save_crawled_screeshot(response.data['png'], 5000000, f_save=self.requested_mode)
                    if sha256_string:
                        Screenshot.save_item_relationship(sha256_string, item_id)
                        Screenshot.save_domain_relationship(sha256_string, self.domains[0])
                # HAR
                if 'har' in response.data:
                    crawlers.save_har(self.har_dir, item_id, response.data['har'])

                le = LinkExtractor(allow_domains=self.domains, unique=True)
                for link in le.extract_links(response):
                    l_cookies = self.build_request_arg(all_cookies)
                    yield SplashRequest(
                        link.url,
                        self.parse,
                        errback=self.errback_catcher,
                        endpoint='execute',
                        meta={'father': item_id, 'current_url': link.url},
                        args=l_cookies
                    )

        def errback_catcher(self, failure):
            # catch all errback failures,
            self.logger.error(repr(failure))

            if failure.check(ResponseNeverReceived):
                request = failure.request
                url= request.meta['current_url']
                father = request.meta['father']

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
                    meta={'father': father, 'current_url': url},
                    args=self.build_request_arg(response.cookiejar)
                )

            else:
                print('failure')
                #print(failure)
                print(failure.type)

        def save_crawled_item(self, item_id, item_content):
            gzip64encoded = crawlers.save_crawled_item(item_id, item_content)

            # Send item to queue
            # send paste to Global
            relay_message = "{0} {1}".format(item_id, gzip64encoded)
            self.p.populate_set_out(relay_message, 'Mixer')

            # increase nb of paste by feeder name
            self.r_serv_log_submit.hincrby("mixer_cache:list_feeder", "crawler", 1)

            # tag crawled paste
            msg = 'infoleak:submission="crawler";{}'.format(item_id)
            self.p.populate_set_out(msg, 'Tags')
