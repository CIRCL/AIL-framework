#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The DomClassifier Module
============================

The DomClassifier modules extract and classify Internet domains/hostnames/IP addresses from
the out output of the Global module.

"""
import os
import sys
import time
from pubsublogger import publisher

import DomainClassifier.domainclassifier
from Helper import Process

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import d4
import item_basic


def main():
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'DomClassifier'

    p = Process(config_section)
    addr_dns = p.config.get("DomClassifier", "dns")

    publisher.info("""ZMQ DomainClassifier is Running""")

    c = DomainClassifier.domainclassifier.Extract(rawtext="", nameservers=[addr_dns])

    cc = p.config.get("DomClassifier", "cc")
    cc_tld = p.config.get("DomClassifier", "cc_tld")

    while True:
        try:
            item_id = p.get_from_set()

            if item_id is None:
                publisher.debug("Script DomClassifier is idling 1s")
                time.sleep(1)
                continue

            item_content = item_basic.get_item_content(item_id)
            mimetype = item_basic.get_item_mimetype(item_id)
            item_basename = item_basic.get_basename(item_id)
            item_source = item_basic.get_source(item_id)
            item_date = item_basic.get_item_date(item_id)

            if mimetype.split('/')[0] == "text":
                c.text(rawtext=item_content)
                c.potentialdomain()
                c.validdomain(passive_dns=True, extended=False)
                print(c.vdomain)

                if c.vdomain and d4.is_passive_dns_enabled():
                    for dns_record in c.vdomain:
                        p.populate_set_out(dns_record)

                localizeddomains = c.include(expression=cc_tld)
                if localizeddomains:
                    print(localizeddomains)
                    publisher.warning(f"DomainC;{item_source};{item_date};{item_basename};Checked {localizeddomains} located in {cc_tld};{item_id}")
                localizeddomains = c.localizedomain(cc=cc)

                if localizeddomains:
                    print(localizeddomains)
                    publisher.warning(f"DomainC;{item_source};{item_date};{item_basename};Checked {localizeddomains} located in {cc};{item_id}")

        except IOError:
            print("CRC Checksum Failed on :", item_id)
            publisher.error(f"Duplicate;{item_source};{item_date};{item_basename};CRC Checksum Failed")

if __name__ == "__main__":
    main()
