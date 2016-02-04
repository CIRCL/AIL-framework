#!/usr/bin/env python
# -*-coding:UTF-8 -*

"""
The DomClassifier Module
============================

The DomClassifier modules is fetching the list of files to be
processed and index each file with a full-text indexer (Whoosh until now).

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

    publisher.info("""ZMQ DomainClassifier is Running""")

    c = DomainClassifier.domainclassifier.Extract(rawtext="")

    cc = p.config.get("DomClassifier", "cc")
    cc_tld = p.config.get("DomClassifier", "cc_tld")

    while True:
        try:
            message = p.get_from_set()

            if message is not None:
                PST = Paste.Paste(message)
            else:
                publisher.debug("Script DomClassifier is idling 10s")
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
                    publisher.warning('DomainC;{};{};{};Checked {} located in {}'.format(
                        PST.p_source, PST.p_date, PST.p_name, localizeddomains, cc_tld))
                localizeddomains = c.localizedomain(cc=cc)
                if localizeddomains:
                    print(localizeddomains)
                    publisher.warning('DomainC;{};{};{};Checked {} located in {}'.format(
                        PST.p_source, PST.p_date, PST.p_name, localizeddomains, cc))
        except IOError:
            print "CRC Checksum Failed on :", PST.p_path
            publisher.error('Duplicate;{};{};{};CRC Checksum Failed'.format(
                PST.p_source, PST.p_date, PST.p_name))

if __name__ == "__main__":
    main()
