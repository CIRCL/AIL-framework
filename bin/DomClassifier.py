#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The DomClassifier Module
============================

The DomClassifier modules extract and classify Internet domains/hostnames/IP addresses from
the out output of the Global module.

"""
import time
import datetime
import redis
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

    # ARDB #
    server_statistics = redis.StrictRedis(
        host=p.config.get("ARDB_Statistics", "host"),
        port=p.config.getint("ARDB_Statistics", "port"),
        db=p.config.getint("ARDB_Statistics", "db"),
        decode_responses=True)

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

            nb_domain = 0
            nb_tld_domain = 0

            if mimetype == "text/plain":
                c.text(rawtext=paste)
                c.potentialdomain()
                valid = c.validdomain(rtype=['A'], extended=True)
                nb_domain = len(set(valid))
                if nb_domain > 0:
                    localizeddomains = c.include(expression=cc_tld)
                    if localizeddomains:
                        nb_tld_domain = len(set(localizeddomains))
                        publisher.warning('DomainC;{};{};{};Checked {} located in {};{}'.format(
                            PST.p_source, PST.p_date, PST.p_name, localizeddomains, cc_tld, PST.p_path))

                    localizeddomains = c.localizedomain(cc=cc)
                    if localizeddomains:
                        nb_tld_domain = nb_tld_domain + len(set(localizeddomains))
                        publisher.warning('DomainC;{};{};{};Checked {} located in {};{}'.format(
                            PST.p_source, PST.p_date, PST.p_name, localizeddomains, cc, PST.p_path))

                    date = datetime.datetime.now().strftime("%Y%m")
                    server_statistics.hincrby('domain_by_tld:'+date, 'ALL', nb_domain)
                    if nb_tld_domain > 0:
                        server_statistics.hincrby('domain_by_tld:'+date, cc, nb_tld_domain)
        except IOError:
            print("CRC Checksum Failed on :", PST.p_path)
            publisher.error('Duplicate;{};{};{};CRC Checksum Failed'.format(
                PST.p_source, PST.p_date, PST.p_name))

if __name__ == "__main__":
    main()
