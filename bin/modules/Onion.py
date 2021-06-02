#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Onion Module
============================

This module extract url from item and returning only ones which are tor
related (.onion). All These urls are send to the crawler discovery queue.

Requirements
------------

*Need running Redis instances. (Redis)

"""
import time
import datetime
import os
import sys
import re

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import crawlers
from lib import regex_helper
from packages.Item import Item

## Manually fetch first page if crawler is disabled
# import base64
# import subprocess
#
# torclient_host = '127.0.0.1'
# torclient_port = 9050
#
# def fetch(p, r_cache, urls, domains):
#     now = datetime.datetime.now()
#     path = os.path.join('onions', str(now.year).zfill(4),
#                         str(now.month).zfill(2),
#                         str(now.day).zfill(2),
#                         str(int(time.mktime(now.utctimetuple()))))
#     failed = []
#     downloaded = []
#     print('{} Urls to fetch'.format(len(urls)))
#     for url, domain in zip(urls, domains):
#         if r_cache.exists(url) or url in failed:
#             continue
#         to_fetch = base64.standard_b64encode(url.encode('utf8'))
#         print('fetching url: {}'.format(to_fetch))
#         process = subprocess.Popen(["python", './tor_fetcher.py', to_fetch],
#                                    stdout=subprocess.PIPE)
#         while process.poll() is None:
#             time.sleep(1)
#
#         if process.returncode == 0:
#             r_cache.setbit(url, 0, 1)
#             r_cache.expire(url, 360000)
#             downloaded.append(url)
#             print('downloaded : {}'.format(downloaded))
#             '''tempfile = process.stdout.read().strip()
#             tempfile = tempfile.decode('utf8')
#             #with open(tempfile, 'r') as f:
#                 filename = path + domain + '.gz'
#                 fetched = f.read()
#                 content = base64.standard_b64decode(fetched)
#                 save_path = os.path.join(os.environ['AIL_HOME'],
#                                          p.config.get("Directories", "pastes"),
#                                          filename)
#                 dirname = os.path.dirname(save_path)
#                 if not os.path.exists(dirname):
#                     os.makedirs(dirname)
#                 with open(save_path, 'w') as ff:
#                     ff.write(content)
#                 p.populate_set_out(save_path, 'Global')
#                 p.populate_set_out(url, 'ValidOnion')
#                 p.populate_set_out(fetched, 'FetchedOnion')'''
#             yield url
#             #os.unlink(tempfile)
#         else:
#             r_cache.setbit(url, 0, 0)
#             r_cache.expire(url, 3600)
#             failed.append(url)
#             print('Failed at downloading', url)
#             print(process.stdout.read())
#     print('Failed:', len(failed), 'Downloaded:', len(downloaded))


class Onion(AbstractModule):
    """docstring for Onion module."""

    def __init__(self):
        super(Onion, self).__init__()

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")
        self.r_onion = config_loader.get_redis_conn("ARDB_Onion")

        self.pending_seconds = config_loader.get_config_int("Onion", "max_execution_time")
        # regex timeout
        self.regex_timeout = 30

        self.faup = crawlers.get_faup()
        self.redis_cache_key = regex_helper.generate_redis_cache_key(self.module_name)

        # activate_crawler = p.config.get("Crawler", "activate_crawler")


        self.url_regex = "((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.onion)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
        self.i2p_regex = "((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.i2p)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
        re.compile(self.url_regex)
        re.compile(self.i2p_regex)

        self.redis_logger.info(f"Module: {self.module_name} Launched")

        # TEMP var: SAVE I2P Domain (future I2P crawler)
        self.save_i2p = config_loader.get_config_boolean("Onion", "save_i2p")

    def compute(self, message):
        # list of tuples: (url, subdomains, domain)
        urls_to_crawl = []

        id, score = message.split()
        item = Item(id)
        item_content = item.get_content()

        # max execution time on regex
        res = regex_helper.regex_findall(self.module_name, self.redis_cache_key, self.url_regex, item.get_id(), item_content)
        for x in res:
            # String to tuple
            x = x[2:-2].replace(" '", "").split("',")
            url = x[0]
            subdomain = x[4].lower()
            self.faup.decode(url)
            url_unpack = self.faup.get()
            try:    ## TODO: # FIXME: check faup version
                domain = url_unpack['domain'].decode().lower()
            except Exception as e:
                domain = url_unpack['domain'].lower()

            if crawlers.is_valid_onion_domain(domain):
                urls_to_crawl.append((url, subdomain, domain))

        to_print = f'Onion;{item.get_source()};{item.get_date()};{item.get_basename()};'
        if not urls_to_crawl:
            self.redis_logger.info(f'{to_print}Onion related;{item.get_id()}')
            return

        # TAG Item
        msg = f'infoleak:automatic-detection="onion";{item.get_id()}'
        self.send_message_to_queue(msg, 'Tags')

        if crawlers.is_crawler_activated():
            for to_crawl in urls_to_crawl:
                print(f'{to_crawl[2]} added to crawler queue: {to_crawl[0]}')
                crawlers.add_item_to_discovery_queue('onion', to_crawl[2], to_crawl[1], to_crawl[0], item.get_id())
        else:
            print(f'{to_print}Detected {len(urls_to_crawl)} .onion(s);{item.get_id()}')
            self.redis_logger.warning(f'{to_print}Detected {len(urls_to_crawl)} .onion(s);{item.get_id()}')
            # keep manual fetcher ????
            ## Manually fetch first page if crawler is disabled
            # for url in fetch(p, r_cache, urls, domains_list):
            #     publisher.info('{}Checked {};{}'.format(to_print, url, PST.p_rel_path))

if __name__ == "__main__":

    module = Onion()
    module.run()
