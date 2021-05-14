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
from pubsublogger import publisher
import DomainClassifier.domainclassifier

##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from Helper import Process

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

        self.redis_logger.info("""ZMQ DomainClassifier is Running""")

        self.c = DomainClassifier.domainclassifier.Extract(rawtext="", nameservers=[addr_dns])

        self.cc = self.process.config.get("DomClassifier", "cc")
        self.cc_tld = self.process.config.get("DomClassifier", "cc_tld")

        # Send module state to logs
        self.redis_logger.info("Module %s initialized" % (self.module_name))


    def compute(self, message):
        try:
            item_content = item_basic.get_item_content(message)
            mimetype = item_basic.get_item_mimetype(message)
            item_basename = item_basic.get_basename(message)
            item_source = item_basic.get_source(message)
            item_date = item_basic.get_item_date(message)

            if mimetype.split('/')[0] == "text":
                self.c.text(rawtext=item_content)
                self.c.potentialdomain()
                self.c.validdomain(passive_dns=True, extended=False)
                self.redis_logger.debug(self.c.vdomain)

                if self.c.vdomain and d4.is_passive_dns_enabled():
                    for dns_record in self.c.vdomain:
                        self.process.populate_set_out(dns_record)

                localizeddomains = self.c.include(expression=self.cc_tld)
                if localizeddomains:
                    self.redis_logger.debug(localizeddomains)
                    self.redis_logger.warning(f"DomainC;{item_source};{item_date};{item_basename};Checked {localizeddomains} located in {self.cc_tld};{message}")
                localizeddomains = self.c.localizedomain(cc=self.cc)

                if localizeddomains:
                    self.redis_logger.debug(localizeddomains)
                    self.redis_logger.warning(f"DomainC;{item_source};{item_date};{item_basename};Checked {localizeddomains} located in {self.cc};{message}")

        except IOError as err:
            self.redis_logger.error(f"Duplicate;{item_source};{item_date};{item_basename};CRC Checksum Failed")
            raise Exception(f"CRC Checksum Failed on: {message}")


if __name__ == "__main__":
    module = DomClassifier()
    module.run()
