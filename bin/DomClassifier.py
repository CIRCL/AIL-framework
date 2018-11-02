#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The DomClassifier Module
============================

The DomClassifier modules extract and classify Internet domains/hostnames/IP addresses from
the out output of the Global module.

"""
import time
from packages import Paste
from pubsublogger import publisher

import DomainClassifier.domainclassifier
from Helper import Process


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
            message = p.get_from_set()

            if message is not None:
                PST = Paste.Paste(message)
            else:
                publisher.debug("Script DomClassifier is idling 1s")
                time.sleep(1)
                continue
            paste = PST.get_p_content()
            mimetype = PST._get_p_encoding()

            if mimetype == "text/plain":
                c.text(rawtext=paste)
                c.potentialdomain()
                c.validdomain(rtype=['A'], extended=True)
                localizeddomains = c.include(expression=cc_tld)
                if localizeddomains:
                    print(localizeddomains)
                    publisher.warning('DomainC;{};{};{};Checked {} located in {};{}'.format(
                        PST.p_source, PST.p_date, PST.p_name, localizeddomains, cc_tld, PST.p_rel_path))
                localizeddomains = c.localizedomain(cc=cc)
                if localizeddomains:
                    print(localizeddomains)
                    publisher.warning('DomainC;{};{};{};Checked {} located in {};{}'.format(
                        PST.p_source, PST.p_date, PST.p_name, localizeddomains, cc, PST.p_rel_path))
        except IOError:
            print("CRC Checksum Failed on :", PST.p_rel_path)
            publisher.error('Duplicate;{};{};{};CRC Checksum Failed'.format(
                PST.p_source, PST.p_date, PST.p_name))

if __name__ == "__main__":
    main()
