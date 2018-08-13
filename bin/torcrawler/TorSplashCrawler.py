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

from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy.crawler import CrawlerProcess, Crawler

from scrapy_splash import SplashRequest

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process

class TorSplashCrawler():

    def __init__(self, splash_url, http_proxy, crawler_depth_limit):
        self.process = CrawlerProcess({'LOG_ENABLED': False})
        self.crawler = Crawler(self.TorSplashSpider, {
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 6.1; rv:24.0) Gecko/20100101 Firefox/24.0',
            'SPLASH_URL': splash_url,
            'HTTP_PROXY': http_proxy,
            'ROBOTSTXT_OBEY': False,
            'DOWNLOADER_MIDDLEWARES': {'scrapy_splash.SplashCookiesMiddleware': 723,
                                       'scrapy_splash.SplashMiddleware': 725,
                                       'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
                                       },
            'SPIDER_MIDDLEWARES': {'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,},
            'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
            'DEPTH_LIMIT': crawler_depth_limit
            })

    def crawl(self, url, domain, original_paste, super_father):
        self.process.crawl(self.crawler, url=url, domain=domain,original_paste=original_paste, super_father=super_father)
        self.process.start()

    class TorSplashSpider(Spider):
        name = 'TorSplashSpider'

        def __init__(self, url, domain,original_paste, super_father, *args, **kwargs):
            self.original_paste = original_paste
            self.super_father = super_father
            self.start_urls = url
            self.domains = [domain]
            date = datetime.datetime.now().strftime("%Y/%m/%d")
            self.full_date = datetime.datetime.now().strftime("%Y%m%d")

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

            self.crawled_paste_filemame = os.path.join(os.environ['AIL_HOME'], self.p.config.get("Directories", "pastes"),
                                            self.p.config.get("Directories", "crawled"), date )

            self.crawled_screenshot = os.path.join(os.environ['AIL_HOME'], self.p.config.get("Directories", "crawled_screenshot"), date )

        def start_requests(self):
            yield SplashRequest(
                self.start_urls,
                self.parse,
                endpoint='render.json',
                meta={'parent': self.original_paste},
                args={  'html': 1,
                        'wait': 10,
                        'render_all': 1,
                        'png': 1}
            )

        def parse(self,response):
            print(response.headers)
            print(response.status)

            # # TODO: # FIXME:
            self.r_cache.setbit(response.url, 0, 1)
            self.r_cache.expire(response.url, 360000)

            UUID = self.domains[0]+str(uuid.uuid4())
            filename_paste = os.path.join(self.crawled_paste_filemame, UUID)
            filename_screenshot = os.path.join(self.crawled_screenshot, UUID +'.png')

            # save new paste on disk
            if self.save_crawled_paste(filename_paste, response.data['html']):

                # create onion metadata
                if not self.r_serv_onion.exists('onion_metadata:{}'.format(self.domain[0])):
                    self.r_serv_onion.hset('onion_metadata:{}'.format(self.domain[0]), 'first_seen', self.full_date)
                self.r_serv_onion.hset('onion_metadata:{}'.format(self.domain[0]), 'last_seen', self.full_date)

                # add onion screenshot history
                self.r_serv_onion.sadd('onion_history:{}'.format(self.domain[0]), self.full_date)

                #create paste metadata
                self.r_serv_metadata.hset('paste_metadata:'+filename_paste, 'super_father', self.super_father)
                self.r_serv_metadata.hset('paste_metadata:'+filename_paste, 'father', response.meta['parent'])
                self.r_serv_metadata.hset('paste_metadata:'+filename_paste, 'domain', self.domains[0])
                self.r_serv_metadata.hset('paste_metadata:'+filename_paste, 'real_link', response.url)

                self.r_serv_metadata.sadd('paste_children:'+response.meta['parent'], filename_paste)

                dirname = os.path.dirname(filename_screenshot)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)

                print(sys.getsizeof(response.data['png']))
                print(sys.getsizeof(response.data['html']))
                print(self.domains[0])



                with open(filename_screenshot, 'wb') as f:
                    f.write(base64.standard_b64decode(response.data['png'].encode()))

                # save external links in set
                lext = LinkExtractor(deny_domains=self.domains, unique=True)
                for link in lext.extract_links(response):
                    self.r_serv_metadata.sadd('paste_crawler:filename_paste', link)

                #le = LinkExtractor(unique=True)
                le = LinkExtractor(allow_domains=self.domains, unique=True)
                for link in le.extract_links(response):
                    self.r_cache.setbit(link, 0, 0)
                    self.r_cache.expire(link, 360000)
                    yield SplashRequest(
                        link.url,
                        self.parse,
                        endpoint='render.json',
                        meta={'parent': UUID},
                        args={  'html': 1,
                                'png': 1,
                                'render_all': 1,
                                'wait': 10}
                    )

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
