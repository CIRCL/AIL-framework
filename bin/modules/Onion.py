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

class Onion(AbstractModule):
    """docstring for Onion module."""

    def __init__(self, queue=True):
        super(Onion, self).__init__(queue=queue)

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        self.pending_seconds = 10
        # regex timeout
        self.regex_timeout = config_loader.get_config_int("Onion", "max_execution_time")

        self.faup = crawlers.get_faup()

        # activate_crawler = p.config.get("Crawler", "activate_crawler")
        self.har = config_loader.get_config_boolean('Crawler', 'default_har')
        self.screenshot = config_loader.get_config_boolean('Crawler', 'default_screenshot')

        self.onion_regex = r"((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.onion)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
        # self.i2p_regex = r"((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.i2p)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
        re.compile(self.onion_regex)
        # re.compile(self.i2p_regex)

        self.logger.info(f"Module: {self.module_name} Launched")

        # TEMP var: SAVE I2P Domain (future I2P crawler)
        # self.save_i2p = config_loader.get_config_boolean("Onion", "save_i2p")

    def extract(self, obj, content, tag):
        extracted = []
        onions = self.regex_finditer(self.onion_regex, obj.get_global_id(), content)
        for onion in onions:
            start, end, value = onion
            url_unpack = crawlers.unpack_url(value)
            domain = url_unpack['domain']
            if crawlers.is_valid_onion_domain(domain):
                extracted.append([start, end, value, f'tag:{tag}'])
        return extracted

    def compute(self, message):
        onion_urls = []
        domains = []

        score = message
        item = self.get_obj()
        item_content = item.get_content()

        # max execution time on regex
        res = self.regex_findall(self.onion_regex, item.get_id(), item_content)
        for x in res:
            # String to tuple
            x = x[2:-2].replace(" '", "").split("',")
            url = x[0]
            url = url.lower()
            print(url)

            # TODO Crawl subdomain
            url_unpack = crawlers.unpack_url(url)
            domain = url_unpack['domain']
            if crawlers.is_valid_onion_domain(domain):
                domains.append(domain)
                onion_urls.append(url)

        if onion_urls:
            if crawlers.is_crawler_activated():
                for domain in domains:
                    task_uuid = crawlers.create_task(domain, parent=item.get_id(), priority=0,
                                                     har=self.har, screenshot=self.screenshot)
                    if task_uuid:
                        print(f'{domain} added to crawler queue: {task_uuid}')
            else:
                to_print = f'Onion;{item.get_source()};{item.get_date()};{item.get_basename()};'
                print(f'{to_print}Detected {len(domains)} .onion(s);{self.obj.get_global_id()}')
                self.redis_logger.warning(f'{to_print}Detected {len(domains)} .onion(s);{self.obj.get_global_id()}')

            # TAG Item
            tag = 'infoleak:automatic-detection="onion"'
            self.add_message_to_queue(message=tag, queue='Tags')


if __name__ == "__main__":
    module = Onion()
    module.run()
