#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Hosts Module
======================

This module is consuming the Redis-list created by the Global module.

It is looking for Hosts

"""

##################################
# Import External packages
##################################
import os
import re
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import regex_helper
#from lib.objects.Items import Item
from packages.Item import Item

class Hosts(AbstractModule):
    """
    Hosts module for AIL framework
    """

    def __init__(self):
        super(Hosts, self).__init__()

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        self.redis_cache_key = regex_helper.generate_redis_cache_key(self.module_name)

        # regex timeout
        self.regex_timeout = 30

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 1

        self.host_regex = r'\b([a-zA-Z\d-]{,63}(?:\.[a-zA-Z\d-]{,63})+)\b'
        re.compile(self.host_regex)

        self.redis_logger.info(f"Module: {self.module_name} Launched")


    def compute(self, message):
        item = Item(message)

        # mimetype = item_basic.get_item_mimetype(item.get_id())
        # if mimetype.split('/')[0] == "text":

        content = item.get_content()

        hosts = regex_helper.regex_findall(self.module_name, self.redis_cache_key, self.host_regex, item.get_id(), content)
        if hosts:
            print(f'{len(hosts)} host     {item.get_id()}')
            for host in hosts:
                #print(host)

                msg = f'{host} {item.get_id()}'
                self.send_message_to_queue(msg, 'Host')



if __name__ == '__main__':

    module = Hosts()
    module.run()
