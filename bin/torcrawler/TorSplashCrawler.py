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

from scrapy_splash import SplashRequest

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process

class TorSplashCrawler():

    def __init__(self, splash_url, crawler_options):
        self.process = CrawlerProcess({'LOG_ENABLED': False})
        self.crawler = Crawler(self.TorSplashSpider, {
            'USER_AGENT': crawler_options['user_agent'],
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
            'CLOSESPIDER_PAGECOUNT': crawler_options['closespider_pagecount'],
            'DEPTH_LIMIT': crawler_options['depth_limit']
            })

    def crawl(self, type, crawler_options, date, requested_mode, url, domain, port, original_item):
        self.process.crawl(self.crawler, type=type, crawler_options=crawler_options, date=date, requested_mode=requested_mode, url=url, domain=domain, port=port, original_item=original_item)
        self.process.start()

    class TorSplashSpider(Spider):
        name = 'TorSplashSpider'

        def __init__(self, type, crawler_options, date, requested_mode, url, domain, port, original_item, *args, **kwargs):
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

            self.arg_crawler = {  'html': crawler_options['html'],
                                  'wait': 10,
                                  'render_all': 1,
                                  'har': crawler_options['har'],
                                  'png': crawler_options['png']}

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

            self.crawler_path = os.path.join(self.p.config.get("Directories", "crawled"), date_str )

            self.crawled_paste_filemame = os.path.join(os.environ['AIL_HOME'], self.p.config.get("Directories", "pastes"),
                                            self.p.config.get("Directories", "crawled"), date_str )

            self.crawled_har = os.path.join(os.environ['AIL_HOME'], self.p.config.get("Directories", "crawled_screenshot"), date_str )
            self.crawled_screenshot = os.path.join(os.environ['AIL_HOME'], self.p.config.get("Directories", "crawled_screenshot") )

        def start_requests(self):
            yield SplashRequest(
                self.start_urls,
                self.parse,
                errback=self.errback_catcher,
                endpoint='render.json',
                meta={'father': self.original_item, 'root_key': None},
                args=self.arg_crawler
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
                if len(self.domains[0]) > 215:
                    UUID = self.domains[0][-215:]+str(uuid.uuid4())
                else:
                    UUID = self.domains[0]+str(uuid.uuid4())
                filename_paste_full = os.path.join(self.crawled_paste_filemame, UUID)
                relative_filename_paste = os.path.join(self.crawler_path, UUID)
                filename_har = os.path.join(self.crawled_har, UUID)

                # # TODO: modify me
                # save new paste on disk
                if self.save_crawled_paste(relative_filename_paste, response.data['html']):

                    # add this paste to the domain crawled set # TODO: # FIXME:  put this on cache ?
                    #self.r_serv_onion.sadd('temp:crawled_domain_pastes:{}'.format(self.domains[0]), filename_paste)

                    self.r_serv_onion.sadd('{}_up:{}'.format(self.type, self.full_date), self.domains[0])
                    self.r_serv_onion.sadd('full_{}_up'.format(self.type), self.domains[0])
                    self.r_serv_onion.sadd('month_{}_up:{}'.format(self.type, self.date_month), self.domains[0])

                    # create onion metadata
                    if not self.r_serv_onion.exists('{}_metadata:{}'.format(self.type, self.domains[0])):
                        self.r_serv_onion.hset('{}_metadata:{}'.format(self.type, self.domains[0]), 'first_seen', self.full_date)

                    # create root_key
                    if self.root_key is None:
                        self.root_key = relative_filename_paste
                        # Create/Update crawler history
                        self.r_serv_onion.zadd('crawler_history_{}:{}:{}'.format(self.type, self.domains[0], self.port), self.date_epoch, self.root_key)
                        # Update domain port number
                        all_domain_ports = self.r_serv_onion.hget('{}_metadata:{}'.format(self.type, self.domains[0]), 'ports')
                        if all_domain_ports:
                            all_domain_ports = all_domain_ports.split(';')
                        else:
                            all_domain_ports = []
                        if self.port not in all_domain_ports:
                            all_domain_ports.append(self.port)
                            self.r_serv_onion.hset('{}_metadata:{}'.format(self.type, self.domains[0]), 'ports', ';'.join(all_domain_ports))

                    #create paste metadata
                    self.r_serv_metadata.hset('paste_metadata:{}'.format(relative_filename_paste), 'super_father', self.root_key)
                    self.r_serv_metadata.hset('paste_metadata:{}'.format(relative_filename_paste), 'father', response.meta['father'])
                    self.r_serv_metadata.hset('paste_metadata:{}'.format(relative_filename_paste), 'domain', '{}:{}'.format(self.domains[0], self.port))
                    self.r_serv_metadata.hset('paste_metadata:{}'.format(relative_filename_paste), 'real_link', response.url)

                    self.r_serv_metadata.sadd('paste_children:'+response.meta['father'], relative_filename_paste)

                    if 'png' in response.data:
                        size_screenshot = (len(response.data['png'])*3) /4

                        if size_screenshot < 5000000 or self.requested_mode: #bytes or manual/auto
                            image_content = base64.standard_b64decode(response.data['png'].encode())
                            hash = sha256(image_content).hexdigest()
                            img_dir_path = os.path.join(hash[0:2], hash[2:4], hash[4:6], hash[6:8], hash[8:10], hash[10:12])
                            filename_img = os.path.join(self.crawled_screenshot, 'screenshot', img_dir_path, hash[12:] +'.png')
                            dirname = os.path.dirname(filename_img)
                            if not os.path.exists(dirname):
                                os.makedirs(dirname)
                            if not os.path.exists(filename_img):
                                with open(filename_img, 'wb') as f:
                                    f.write(image_content)
                            # add item metadata
                            self.r_serv_metadata.hset('paste_metadata:{}'.format(relative_filename_paste), 'screenshot', hash)
                            # add sha256 metadata
                            self.r_serv_onion.sadd('screenshot:{}'.format(hash), relative_filename_paste)

                    if 'har' in response.data:
                        dirname = os.path.dirname(filename_har)
                        if not os.path.exists(dirname):
                            os.makedirs(dirname)
                        with open(filename_har+'.json', 'wb') as f:
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
                            meta={'father': relative_filename_paste, 'root_key': response.meta['root_key']},
                            args=self.arg_crawler
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
                if response:
                    response_root_key = response.meta['root_key']
                else:
                    response_root_key = None
                yield SplashRequest(
                    url,
                    self.parse,
                    errback=self.errback_catcher,
                    endpoint='render.json',
                    meta={'father': father, 'root_key': response.meta['root_key']},
                    args=self.arg_crawler
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
