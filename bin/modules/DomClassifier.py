#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The DomClassifier Module
============================

The DomClassifier modules extract and classify Internet domains/hostnames/IP addresses from
the out output of the Global module.

"""

##################################
# Import External packages
##################################
import os
import sys
import DomainClassifier.domainclassifier

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import d4


class DomClassifier(AbstractModule):
    """
    DomClassifier module for AIL framework
    """

    def __init__(self):
        super(DomClassifier, self).__init__()

        config_loader = ConfigLoader()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        addr_dns = config_loader.get_config_str("DomClassifier", "dns")

        redis_host = config_loader.get_config_str('Redis_Cache', 'host')
        redis_port = config_loader.get_config_int('Redis_Cache', 'port')
        redis_db = config_loader.get_config_int('Redis_Cache', 'db')
        self.dom_classifier = DomainClassifier.domainclassifier.Extract(rawtext="", nameservers=[addr_dns],
                                                                        redis_host=redis_host,
                                                                        redis_port=redis_port, redis_db=redis_db,
                                                                        re_timeout=30)

        self.cc = config_loader.get_config_str("DomClassifier", "cc")
        self.cc_tld = config_loader.get_config_str("DomClassifier", "cc_tld")

        # Send module state to logs
        self.logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message, r_result=False):
        host = message

        item = self.get_obj()
        item_basename = item.get_basename()
        item_date = item.get_date()
        item_source = item.get_source()
        try:

            self.dom_classifier.text(rawtext=host)
            if not self.dom_classifier.domain:
                return
            print(self.dom_classifier.domain)
            self.dom_classifier.validdomain(passive_dns=True, extended=False)
            # self.logger.debug(self.dom_classifier.vdomain)

            print(self.dom_classifier.vdomain)
            print()

            if self.dom_classifier.vdomain and d4.is_passive_dns_enabled():
                for dns_record in self.dom_classifier.vdomain:
                    self.add_message_to_queue(obj=None, message=dns_record)

            if self.cc_tld:
                localizeddomains = self.dom_classifier.include(expression=self.cc_tld)
                if localizeddomains:
                    print(localizeddomains)
                    self.redis_logger.warning(f"DomainC;{item_source};{item_date};{item_basename};Checked {localizeddomains} located in {self.cc_tld};{item.get_id()}")

            if self.cc:
                localizeddomains = self.dom_classifier.localizedomain(cc=self.cc)
                if localizeddomains:
                    print(localizeddomains)
                    self.redis_logger.warning(f"DomainC;{item_source};{item_date};{item_basename};Checked {localizeddomains} located in {self.cc};{item.get_id()}")

            if r_result:
                return self.dom_classifier.vdomain

        except IOError as err:
            self.redis_logger.error(f"Duplicate;{item_source};{item_date};{item_basename};CRC Checksum Failed")
            raise Exception(f"CRC Checksum Failed on: {item.get_id()}")


if __name__ == "__main__":
    module = DomClassifier()
    module.run()
