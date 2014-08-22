#!/usr/bin/env python2
# -*-coding:UTF-8 -*
import redis
import pprint
import time
import dns.exception
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher

# Country and ASN lookup
from cymru.ip2asn.dns import DNSClient as ip2asn
import socket
import pycountry
import ipaddress

import Helper

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'PubSub_Categ'
    config_channel = 'channel_3'
    subscriber_name = "urls"

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # Publisher
    pub_config_section = "PubSub_Url"
    pub_config_channel = 'channel'
    h.zmq_pub(pub_config_section, pub_config_channel)

    # Subscriber
    h.zmq_sub(config_section)

    # REDIS #
    r_serv2 = redis.StrictRedis(
        host=h.config.get("Redis_Cache", "host"),
        port=h.config.getint("Redis_Cache", "port"),
        db=h.config.getint("Redis_Cache", "db"))

    # Country to log as critical
    cc_critical = h.config.get("PubSub_Url", "cc_critical")

    # FUNCTIONS #
    publisher.info("Script URL subscribed to channel web_categ")

    message = h.redis_rpop()
    prec_filename = None

    url_regex = "(http|https|ftp)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*"

    while True:
        try:
            if message is not None:
                channel, filename, word, score = message.split()

                if prec_filename is None or filename != prec_filename:
                    domains_list = []
                    PST = Paste.Paste(filename)
                    client = ip2asn()
                    for x in PST.get_regex(url_regex):
                        scheme, credential, subdomain, domain, host, tld, \
                            port, resource_path, query_string, f1, f2, f3, \
                            f4 = x
                        domains_list.append(domain)
                        h.zmq_pub_send(str(x))
                        publisher.debug('{} Published'.format(x))

                        if f1 == "onion":
                            print domain

                        hostl = unicode(subdomain+domain)
                        try:
                            socket.setdefaulttimeout(2)
                            ip = socket.gethostbyname(unicode(hostl))
                        except:
                            # If the resolver is not giving any IPv4 address,
                            # ASN/CC lookup is skip.
                            continue

                        try:
                            l = client.lookup(socket.inet_aton(ip), qType='IP')
                        except ipaddress.AddressValueError:
                            continue
                        cc = getattr(l, 'cc')
                        asn = getattr(l, 'asn')

                        # EU is not an official ISO 3166 code (but used by RIPE
                        # IP allocation)
                        if cc is not None and cc != "EU":
                            print hostl, asn, cc, \
                                pycountry.countries.get(alpha2=cc).name
                            if cc == cc_critical:
                                publisher.warning(
                                    'Url;{};{};{};Detected {} {}'.format(
                                        PST.p_source, PST.p_date, PST.p_name,
                                        hostl, cc))
                        else:
                            print hostl, asn, cc

                    A_values = lib_refine.checking_A_record(r_serv2,
                                                            domains_list)
                    if A_values[0] >= 1:
                        PST.__setattr__(channel, A_values)
                        PST.save_attribute_redis(channel, (A_values[0],
                                                 list(A_values[1])))

                        pprint.pprint(A_values)
                        publisher.info('Url;{};{};{};Checked {} URL'.format(
                            PST.p_source, PST.p_date, PST.p_name, A_values[0]))
                prec_filename = filename

            else:
                if h.redis_queue_shutdown():
                    print "Shutdown Flag Up: Terminating"
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                publisher.debug("Script url is Idling 10s")
                time.sleep(10)

            message = h.redis_rpop()
        except dns.exception.Timeout:
            print "dns.exception.Timeout", A_values
