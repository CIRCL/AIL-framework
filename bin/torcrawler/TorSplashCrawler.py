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

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
from twisted.web._newclient import ResponseNeverReceived

from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.crawler import CrawlerProcess, Crawler

from scrapy_splash import SplashRequest

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process

class TorSplashCrawler():

    def __init__(self, splash_url, crawler_depth_limit):
        self.process = CrawlerProcess({'LOG_ENABLED': False})
        self.crawler = Crawler(self.TorSplashSpider, {
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 6.1; rv:24.0) Gecko/20100101 Firefox/24.0',
            'SPLASH_URL': splash_url,
            'ROBOTSTXT_OBEY': False,
            'DOWNLOADER_MIDDLEWARES': {'scrapy_splash.SplashCookiesMiddleware': 723,
                                       'scrapy_splash.SplashMiddleware': 725,
                                       'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
                                       },
            'SPIDER_MIDDLEWARES': {'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,},
            'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
            'HTTPERROR_ALLOW_ALL': True,
            'RETRY_TIMES': 2,
            'CLOSESPIDER_PAGECOUNT': 50,
            'DEPTH_LIMIT': crawler_depth_limit
            })

    def crawl(self, type, url, domain, original_paste, super_father):
        self.process.crawl(self.crawler, type=type, url=url, domain=domain,original_paste=original_paste, super_father=super_father)
        self.process.start()

    class TorSplashSpider(Spider):
        name = 'TorSplashSpider'

        def __init__(self, type, url, domain,original_paste, super_father, *args, **kwargs):
            self.type = type
            self.original_paste = original_paste
            self.super_father = super_father
            self.start_urls = url
            self.domains = [domain]
            date = datetime.datetime.now().strftime("%Y/%m/%d")
            self.full_date = datetime.datetime.now().strftime("%Y%m%d")
            self.date_month = datetime.datetime.now().strftime("%Y%m")

            config_section = 'Crawler'
            self.p = Process(config_section)

            self.r_cache = redis.StrictRedis(
                host=self.p.config.get("Redis_Cache", "host"),
                port=self.p.config.getint("Redis_Cache", "port"),
                db=self.p.config.getint("Redis_Cache", "db"),
                decode_responses=True)

            self.r_serv_log_submit = redis.StrictRedis(
                host=self.p.config.get("Redis_Log_submit", "host"),
                port=self.p.config.getint("Redis_Log_submit", "port"),
                db=self.p.config.getint("Redis_Log_submit", "db"),
                decode_responses=True)

            self.r_serv_metadata = redis.StrictRedis(
                host=self.p.config.get("ARDB_Metadata", "host"),
                port=self.p.config.getint("ARDB_Metadata", "port"),
                db=self.p.config.getint("ARDB_Metadata", "db"),
                decode_responses=True)

            self.r_serv_onion = redis.StrictRedis(
                host=self.p.config.get("ARDB_Onion", "host"),
                port=self.p.config.getint("ARDB_Onion", "port"),
                db=self.p.config.getint("ARDB_Onion", "db"),
                decode_responses=True)

            self.crawler_path = os.path.join(self.p.config.get("Directories", "crawled"), date )

            self.crawled_paste_filemame = os.path.join(os.environ['AIL_HOME'], self.p.config.get("Directories", "pastes"),
                                            self.p.config.get("Directories", "crawled"), date )

            self.crawled_screenshot = os.path.join(os.environ['AIL_HOME'], self.p.config.get("Directories", "crawled_screenshot"), date )

        def start_requests(self):
            yield SplashRequest(
                self.start_urls,
                self.parse,
                errback=self.errback_catcher,
                endpoint='render.json',
                meta={'father': self.original_paste},
                args={  'html': 1,
                        'wait': 10,
                        'render_all': 1,
                        'har': 1,
                        'png': 1}
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

                #avoid filename too big
                if self.domains[0] > 225:
                    UUID = self.domains[0][-215:]+str(uuid.uuid4())
                else
                    UUID = self.domains[0]+str(uuid.uuid4())
                filename_paste = os.path.join(self.crawled_paste_filemame, UUID)
                relative_filename_paste = os.path.join(self.crawler_path, UUID)
                filename_screenshot = os.path.join(self.crawled_screenshot, UUID +'.png')

                # save new paste on disk
                if self.save_crawled_paste(filename_paste, response.data['html']):

                    # add this paste to the domain crawled set # TODO: # FIXME:  put this on cache ?
                    #self.r_serv_onion.sadd('temp:crawled_domain_pastes:{}'.format(self.domains[0]), filename_paste)

                    self.r_serv_onion.sadd('{}_up:{}'.format(self.type, self.full_date), self.domains[0])
                    self.r_serv_onion.sadd('full_{}_up'.format(self.type), self.domains[0])
                    self.r_serv_onion.sadd('month_{}_up:{}'.format(self.type, self.date_month), self.domains[0])

                    # create onion metadata
                    if not self.r_serv_onion.exists('{}_metadata:{}'.format(self.type, self.domains[0])):
                        self.r_serv_onion.hset('{}_metadata:{}'.format(self.type, self.domains[0]), 'first_seen', self.full_date)
                    self.r_serv_onion.hset('{}_metadata:{}'.format(self.type, self.domains[0]), 'last_seen', self.full_date)

                    #create paste metadata
                    self.r_serv_metadata.hset('paste_metadata:'+filename_paste, 'super_father', self.super_father)
                    self.r_serv_metadata.hset('paste_metadata:'+filename_paste, 'father', response.meta['father'])
                    self.r_serv_metadata.hset('paste_metadata:'+filename_paste, 'domain', self.domains[0])
                    self.r_serv_metadata.hset('paste_metadata:'+filename_paste, 'real_link', response.url)

                    self.r_serv_metadata.sadd('paste_children:'+response.meta['father'], filename_paste)

                    dirname = os.path.dirname(filename_screenshot)
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)

                    size_screenshot = (len(response.data['png'])*3) /4

                    if size_screenshot < 5000000: #bytes
                        with open(filename_screenshot, 'wb') as f:
                            f.write(base64.standard_b64decode(response.data['png'].encode()))

                    with open(filename_screenshot+'har.txt', 'wb') as f:
                        f.write(json.dumps(response.data['har']).encode())

                    # save external links in set
                    #lext = LinkExtractor(deny_domains=self.domains, unique=True)
                    #for link in lext.extract_links(response):
                    #    self.r_serv_onion.sadd('domain_{}_external_links:{}'.format(self.type, self.domains[0]), link.url)
                    #    self.r_serv_metadata.sadd('paste_{}_external_links:{}'.format(self.type, filename_paste), link.url)

                    le = LinkExtractor(allow_domains=self.domains, unique=True)
                    for link in le.extract_links(response):
                        yield SplashRequest(
                            link.url,
                            self.parse,
                            errback=self.errback_catcher,
                            endpoint='render.json',
                            meta={'father': relative_filename_paste},
                            args={  'html': 1,
                                    'png': 1,
                                    'render_all': 1,
                                    'har': 1,
                                    'wait': 10}
                        )

        def errback_catcher(self, failure):
            # catch all errback failures,
            self.logger.error(repr(failure))

            if failure.check(ResponseNeverReceived):
                request = failure.request
                url = request.meta['splash']['args']['url']
                father = request.meta['father']

                self.logger.error('Splash, ResponseNeverReceived for %s, retry in 10s ...', url)
                time.sleep(10)
                yield SplashRequest(
                    url,
                    self.parse,
                    errback=self.errback_catcher,
                    endpoint='render.json',
                    meta={'father': father},
                    args={  'html': 1,
                            'png': 1,
                            'render_all': 1,
                            'har': 1,
                            'wait': 10}
                )

            else:
                print('failure')
                #print(failure)
                print(failure.type)
                #print(failure.request.meta['item'])

            '''
            #if isinstance(failure.value, HttpError):
            elif failure.check(HttpError):
                # you can get the response
                response = failure.value.response
                print('HttpError')
                self.logger.error('HttpError on %s', response.url)

            #elif isinstance(failure.value, DNSLookupError):
            elif failure.check(DNSLookupError):
                # this is the original request
                request = failure.request
                print(DNSLookupError)
                print('DNSLookupError')
                self.logger.error('DNSLookupError on %s', request.url)

            #elif isinstance(failure.value, TimeoutError):
            elif failure.check(TimeoutError):
                request = failure.request
                print('TimeoutError')
                print(TimeoutError)
                self.logger.error('TimeoutError on %s', request.url)
            '''

        def save_crawled_paste(self, filename, content):

            if os.path.isfile(filename):
                print('File: {} already exist in submitted pastes'.format(filename))
                return False

            try:
                gzipencoded = gzip.compress(content.encode())
                gzip64encoded = base64.standard_b64encode(gzipencoded).decode()
            except:
                print("file error: {}".format(filename))
                return False

            # send paste to Global
            relay_message = "{0} {1}".format(filename, gzip64encoded)
            self.p.populate_set_out(relay_message, 'Mixer')

            # increase nb of paste by feeder name
            self.r_serv_log_submit.hincrby("mixer_cache:list_feeder", "crawler", 1)

            # tag crawled paste
            msg = 'infoleak:submission="crawler";{}'.format(filename)
            self.p.populate_set_out(msg, 'Tags')
            return True
