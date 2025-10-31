#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Onion Module
============================

This module extract url from object and returning only ones which are tor
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
from lib.objects.Domains import Domain
from lib import crawlers
from lib import psl_faup

class Onion(AbstractModule):
    """docstring for Onion module."""

    def __init__(self, queue=True):
        super(Onion, self).__init__(queue=queue)

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        self.pending_seconds = 10
        # regex timeout
        self.regex_timeout = config_loader.get_config_int("Onion", "max_execution_time")

        # activate_crawler = p.config.get("Crawler", "activate_crawler")
        self.har = config_loader.get_config_boolean('Crawler', 'default_har')
        self.screenshot = config_loader.get_config_boolean('Crawler', 'default_screenshot')

        self.onion_regex = r"((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.onion)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
        self.i2p_regex = r"((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.i2p)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
        re.compile(self.onion_regex)
        re.compile(self.i2p_regex)

        self.logger.info(f"Module: {self.module_name} Launched")

    def extract(self, obj, content, tag): # TODO add I2P
        extracted = []
        if obj.type == 'item':
            if 'infoleak:submission="crawler"' in obj.get_tags():
                return extracted
        onions = self.regex_finditer(self.onion_regex, obj.get_global_id(), content)
        for onion in onions:
            start, end, value = onion
            # url
            if value.startswith("://"):
                value = value[3:]
            url_unpack = crawlers.unpack_url(value)
            if url_unpack:
                domain = url_unpack['domain']
                if crawlers.is_valid_onion_domain(domain):
                    extracted.append([start, end, value, f'tag:{tag}'])
        return extracted

    def compute(self, message):
        onion_urls = []
        i2p_urls = []
        domains = set()

        obj = self.get_obj()
        content = obj.get_content()

        # max execution time on regex
        res = self.regex_findall(self.onion_regex, obj.get_id(), content, r_set=True)
        for x in res:
            # String to tuple
            x = x[2:-2].replace(" '", "").split("',")
            url = x[0]
            if url.startswith("://"):
                url = url[3:]
            url = url.lower()

            # TODO Crawl subdomain
            if len(url) >= 62:
                # perf
                if len(url) == 69 and url.endswith(".onion"):
                    domain = url[7:]
                    domains.add(domain)
                    onion_urls.append(url)
                else:
                    domain = psl_faup.get_domain(url)
                    if domain:
                        if crawlers.is_valid_onion_domain(domain):
                            domains.add(domain)
                            onion_urls.append(url)

        res = self.regex_findall(self.i2p_regex, obj.get_id(), content, r_set=True)
        for x in res:
            # String to tuple
            x = x[2:-2].replace(" '", "").split("',")
            url = x[0]
            if url.startswith("://"):
                url = url[3:]
            url = url.lower()

            # perf
            if url.endswith('b32.i2p'):
                b32_url = url
                if url.startswith('http://'):
                    b32_url = url[7:]
                if crawlers.is_valid_i2p_b32_domain(b32_url):
                    domains.add(b32_url)
                    i2p_urls.append(b32_url)
                    continue
            elif url.endswith('.i2p'):
                dom_url = url
                if url.startswith('http://'):
                    dom_url = url[7:]
                if '.' not in dom_url[:-4]:
                    if crawlers.is_valid_i2p_domain(dom_url):
                        domains.add(dom_url)
                        i2p_urls.append(dom_url)
                        continue

            domain = psl_faup.get_domain(url)
            if domain:
                if crawlers.is_valid_i2p_domain(domain):
                    domains.add(domain)
                    i2p_urls.append(url)

        # Onion + I2P
        if domains:
            if crawlers.is_crawler_activated():
                for domain in domains:
                    dom = Domain(domain)
                    # Domain Crawled today or UP this month
                    if dom.is_down_today() or dom.is_up_this_month():
                        continue

                    task_uuid = crawlers.create_task(domain, parent=obj.get_id(), priority=0, new_task=True,
                                                     har=self.har, screenshot=self.screenshot)
                    if task_uuid:
                        print(f'{domain} added to crawler queue: {task_uuid}')
                    if self.obj.type == 'message':
                        # check if domain was up
                        if dom.was_up():
                            self.obj.add_correlation('domain', '', domain)
                            chat_subtype = obj.get_chat_instance()
                            chat_id = obj.get_chat_id()
                            dom.add_correlation('chat', chat_subtype, chat_id)
                        elif task_uuid and not dom.exists():
                            chat_subtype = obj.get_chat_instance()
                            chat_id = obj.get_chat_id()
                            crawlers.add_domain_correlation_cache(domain, f'chat:{chat_subtype}:{chat_id}')
                            crawlers.add_domain_correlation_cache(domain, self.obj.get_global_id())
            else:
                print(f'Detected {len(domains)} .onion/i2p;{self.obj.get_global_id()}')

            if onion_urls:
                # TAG Object
                tag = 'infoleak:automatic-detection="onion"'
                self.add_message_to_queue(message=tag, queue='Tags')


if __name__ == "__main__":
    module = Onion()
    module.run()
