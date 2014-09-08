#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The ZMQ_Sub_DomainClassifier Module
============================

The ZMQ_Sub_DomainClassifier modules is fetching the list of files to be processed
and index each file with a full-text indexer (Whoosh until now).

"""
import redis
import ConfigParser
import time
from packages import Paste
from packages import ZMQ_PubSub
from pubsublogger import publisher

import DomainClassifier.domainclassifier
import os

configfile = './packages/config.cfg'


def main():
    """Main Function"""

    # CONFIG #
    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    # Redis
    r_serv1 = redis.StrictRedis(
        host=cfg.get("Redis_Queues", "host"),
        port=cfg.getint("Redis_Queues", "port"),
        db=cfg.getint("Redis_Queues", "db"))

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    # Subscriber
    channel = cfg.get("PubSub_Global", "channel")
    subscriber_name = "DomainClassifier"
    subscriber_config_section = "PubSub_Global"

    sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, channel, subscriber_name)

    # FUNCTIONS #
    publisher.info("""ZMQ DomainClassifier is Running""")
    c = DomainClassifier.domainclassifier.Extract(rawtext="")

    while True:
        try:
            message = sub.get_msg_from_queue(r_serv1)

            if message is not None:
                PST = Paste.Paste(message.split(" ", -1)[-1])
            else:
                if r_serv1.sismember("SHUTDOWN_FLAGS", "Indexer"):
                    r_serv1.srem("SHUTDOWN_FLAGS", "Indexer")
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                publisher.debug("Script DomainClassifier is idling 10s")
                time.sleep(1)
                continue
            docpath = message.split(" ", -1)[-1]
            paste = PST.get_p_content()
            mimetype = PST._get_p_encoding()
            if mimetype == "text/plain":
                c.text(rawtext=paste)
                c.potentialdomain()
                c.validdomain(rtype=['A'],extended=True)
                localizeddomains = c.include(expression=r'\.lu$')
                if localizeddomains:
                    print (localizeddomains)
                localizeddomains =  c.localizedomain(cc='LU')
                if localizeddomains:
                    print (localizeddomains)
        except IOError:
            print "CRC Checksum Failed on :", PST.p_path
            publisher.error('Duplicate;{};{};{};CRC Checksum Failed'.format(PST.p_source, PST.p_date, PST.p_name))
            pass


if __name__ == "__main__":
    main()
