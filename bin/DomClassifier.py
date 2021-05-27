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
import time
import DomainClassifier.domainclassifier

##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from packages.Item import Item

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import d4
import item_basic


class DomClassifier(AbstractModule):
    """
    DomClassifier module for AIL framework
    """

    def __init__(self):
        super(DomClassifier, self).__init__()

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 1

        addr_dns = self.process.config.get("DomClassifier", "dns")

        self.c = DomainClassifier.domainclassifier.Extract(rawtext="", nameservers=[addr_dns])

        self.cc = self.process.config.get("DomClassifier", "cc")
        self.cc_tld = self.process.config.get("DomClassifier", "cc_tld")

        # Send module state to logs
        self.redis_logger.info(f"Module: {self.module_name} Launched")


    def compute(self, message, r_result=False):
        item = Item(message)

        item_content = item.get_content()
        item_basename = item.get_basename()
        item_date = item.get_date()
        item_source = item.get_source()
        try:
            mimetype = item_basic.get_item_mimetype(item.get_id())

            if mimetype.split('/')[0] == "text":
                self.c.text(rawtext=item_content)
                self.c.potentialdomain()
                self.c.validdomain(passive_dns=True, extended=False)
                #self.redis_logger.debug(self.c.vdomain)

                if self.c.vdomain and d4.is_passive_dns_enabled():
                    for dns_record in self.c.vdomain:
                        self.send_message_to_queue(dns_record)

                localizeddomains = self.c.include(expression=self.cc_tld)
                if localizeddomains:
                    print(localizeddomains)
                    self.redis_logger.warning(f"DomainC;{item_source};{item_date};{item_basename};Checked {localizeddomains} located in {self.cc_tld};{item.get_id()}")

                localizeddomains = self.c.localizedomain(cc=self.cc)
                if localizeddomains:
                    print(localizeddomains)
                    self.redis_logger.warning(f"DomainC;{item_source};{item_date};{item_basename};Checked {localizeddomains} located in {self.cc};{item.get_id()}")

                if r_result:
                    return self.c.vdomain

        except IOError as err:
            self.redis_logger.error(f"Duplicate;{item_source};{item_date};{item_basename};CRC Checksum Failed")
            raise Exception(f"CRC Checksum Failed on: {item.get_id()}")


if __name__ == "__main__":
    module = DomClassifier()
    module.run()
