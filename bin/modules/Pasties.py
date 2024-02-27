#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Pasties Module
======================
This module spots domain-pasties services for further processing
"""

##################################
# Import External packages
##################################
import os
import sys
import time

from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import crawlers

# TODO add url validator

pasties_blocklist_urls = set()
pasties_domains = {}

class Pasties(AbstractModule):
    """
    Pasties module for AIL framework
    """

    def __init__(self):
        super(Pasties, self).__init__()
        self.faup = Faup()

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        self.pasties = {}
        self.urls_blocklist = set()
        self.load_pasties_domains()

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def load_pasties_domains(self):
        self.pasties = {}
        self.urls_blocklist = set()

        domains_pasties = os.path.join(os.environ['AIL_HOME'], 'files/domains_pasties')
        if os.path.exists(domains_pasties):
            with open(domains_pasties) as f:
                for line in f:
                    url = line.strip()
                    if url:  # TODO validate line
                        self.faup.decode(url)
                        url_decoded = self.faup.get()
                        host = url_decoded['host']
                        # if url_decoded.get('port', ''):
                        #     host = f'{host}:{url_decoded["port"]}'
                        path = url_decoded.get('resource_path', '')
                        # print(url_decoded)
                        if path and path != '/':
                            if path[-1] != '/':
                                path = f'{path}/'
                        else:
                            path = None

                        if host in self.pasties:
                            if path:
                                self.pasties[host].add(path)
                        else:
                            if path:
                                self.pasties[host] = {path}
                            else:
                                self.pasties[host] = set()

        url_blocklist = os.path.join(os.environ['AIL_HOME'], 'files/domains_pasties_blacklist')
        if os.path.exists(url_blocklist):
            with open(url_blocklist) as f:
                for line in f:
                    url = line.strip()
                    self.faup.decode(url)
                    url_decoded = self.faup.get()
                    host = url_decoded['host']
                    # if url_decoded.get('port', ''):
                    #     host = f'{host}:{url_decoded["port"]}'
                    path = url_decoded.get('resource_path', '')
                    url = f'{host}{path}'
                    if url_decoded['query_string']:
                        url = url + url_decoded['query_string']
                    self.urls_blocklist.add(url)

    def send_to_crawler(self, url, obj_id):
        if not self.r_cache.exists(f'{self.module_name}:url:{url}'):
            self.r_cache.set(f'{self.module_name}:url:{url}', int(time.time()))
            self.r_cache.expire(f'{self.module_name}:url:{url}', 86400)
            crawlers.create_task(url, depth=0, har=False, screenshot=False, proxy='force_tor', priority=60, parent=obj_id)

    def compute(self, message):
        url = message.split()

        self.faup.decode(url)
        url_decoded = self.faup.get()
        # print(url_decoded)
        url_host = url_decoded['host']
        # if url_decoded.get('port', ''):
        #     url_host = f'{url_host}:{url_decoded["port"]}'
        path = url_decoded.get('resource_path', '')
        if url_host in self.pasties:
            if url.startswith('http://'):
                if url[7:] in self.urls_blocklist:
                    return None
            elif url.startswith('https://'):
                if url[8:] in self.urls_blocklist:
                    return None
            else:
                if url in self.urls_blocklist:
                    return None

            if not self.pasties[url_host]:
                if path and path != '/':
                    print('send to crawler', url_host, url)
                    self.send_to_crawler(url, self.obj.id)
            else:
                if path.endswith('/'):
                    path_end = path[:-1]
                else:
                    path_end = f'{path}/'
                for url_path in self.pasties[url_host]:
                    if path.startswith(url_path):
                        if url_path != path and url_path != path_end:
                            print('send to crawler', url_path, url)
                            self.send_to_crawler(url, self.obj.id)
                            break


if __name__ == '__main__':
    module = Pasties()
    module.run()
