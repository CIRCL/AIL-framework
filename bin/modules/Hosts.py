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

import DomainClassifier.domainclassifier

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader

class Hosts(AbstractModule):
    """
    Hosts module for AIL framework
    """

    def __init__(self):
        super(Hosts, self).__init__()

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        # regex timeout
        self.regex_timeout = 30

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        redis_host = config_loader.get_config_str('Redis_Cache', 'host')
        redis_port = config_loader.get_config_int('Redis_Cache', 'port')
        redis_db = config_loader.get_config_int('Redis_Cache', 'db')
        self.dom_classifier = DomainClassifier.domainclassifier.Extract(rawtext="",
                                                                        redis_host=redis_host,
                                                                        redis_port=redis_port,
                                                                        redis_db=redis_db,
                                                                        re_timeout=30)
        self.logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        obj = self.get_obj()

        content = obj.get_content()
        self.dom_classifier.text(content)
        if self.dom_classifier.domain:
            print(f'{len(self.dom_classifier.domain)} host     {obj.get_id()}')
            # print(self.dom_classifier.domain)
            for domain in self.dom_classifier.domain:
                if domain:
                    self.add_message_to_queue(message=domain, queue='Host')


if __name__ == '__main__':
    module = Hosts()
    module.run()
