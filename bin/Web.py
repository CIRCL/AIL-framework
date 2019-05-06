#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Web Module
============================

This module tries to parse URLs and warns if some defined contry code are present.

"""

import redis
import pprint
import time
import os
import dns.exception
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher
from pyfaup.faup import Faup
import re

# Country and ASN lookup
from cymru.ip2asn.dns import DNSClient as ip2asn
import socket
import pycountry
import ipaddress

from Helper import Process

# Used to prevent concat with empty fields due to url parsing
def avoidNone(a_string):
    if a_string is None:
        return ""
    else:
        return a_string

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Web'

    p = Process(config_section)

    # REDIS #
    r_serv2 = redis.StrictRedis(
        host=p.config.get("Redis_Cache", "host"),
        port=p.config.getint("Redis_Cache", "port"),
        db=p.config.getint("Redis_Cache", "db"),
        decode_responses=True)

    # Protocol file path
    protocolsfile_path = os.path.join(os.environ['AIL_HOME'],
                         p.config.get("Directories", "protocolsfile"))

    # Country to log as critical
    cc_critical = p.config.get("Url", "cc_critical")

    # FUNCTIONS #
    publisher.info("Script URL subscribed to channel web_categ")

    # FIXME For retro compatibility
    channel = 'web_categ'

    message = p.get_from_set()
    prec_filename = None
    faup = Faup()

    # Get all uri from protocolsfile (Used for Curve)
    uri_scheme = ""
    with open(protocolsfile_path, 'r') as scheme_file:
        for scheme in scheme_file:
            uri_scheme += scheme[:-1]+"|"
    uri_scheme = uri_scheme[:-1]

    url_regex = "("+uri_scheme+")\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*"

    while True:
        if message is not None:
            filename, score = message.split()

            if prec_filename is None or filename != prec_filename:
                domains_list = []
                PST = Paste.Paste(filename)
                client = ip2asn()
                for x in PST.get_regex(url_regex):
                    matching_url = re.search(url_regex, PST.get_p_content())
                    url = matching_url.group(0)

                    to_send = "{} {} {}".format(url, PST._get_p_date(), filename)
                    p.populate_set_out(to_send, 'Url')

                    faup.decode(url)
                    domain = faup.get_domain()
                    subdomain = faup.get_subdomain()

                    publisher.debug('{} Published'.format(url))

                    if subdomain is not None:
                        ## TODO: # FIXME: remove me
                        try:
                            subdomain = subdomain.decode()
                        except:
                            pass

                    if domain is not None:
                        ## TODO: # FIXME: remove me
                        try:
                            domain = domain.decode()
                        except:
                            pass
                        domains_list.append(domain)

                    hostl = avoidNone(subdomain) + avoidNone(domain)

                    try:
                        socket.setdefaulttimeout(1)
                        ip = socket.gethostbyname(hostl)
                    except:
                        # If the resolver is not giving any IPv4 address,
                        # ASN/CC lookup is skip.
                        continue

                    try:
                        l = client.lookup(ip, qType='IP')

                    except ipaddress.AddressValueError:
                        continue
                    cc = getattr(l, 'cc')
                    asn = ''
                    if getattr(l, 'asn') is not None:
                        asn = getattr(l, 'asn')[2:] #remobe b'

                    # EU is not an official ISO 3166 code (but used by RIPE
                    # IP allocation)
                    if cc is not None and cc != "EU":
                        print(hostl, asn, cc, \
                            pycountry.countries.get(alpha_2=cc).name)
                        if cc == cc_critical:
                            to_print = 'Url;{};{};{};Detected {} {}'.format(
                                    PST.p_source, PST.p_date, PST.p_name,
                                    hostl, cc)
                            #publisher.warning(to_print)
                            print(to_print)
                    else:
                        print(hostl, asn, cc)

                A_values = lib_refine.checking_A_record(r_serv2,
                                                        domains_list)

                if A_values[0] >= 1:
                    PST.__setattr__(channel, A_values)
                    PST.save_attribute_redis(channel, (A_values[0],
                                             list(A_values[1])))


                    pprint.pprint(A_values)
                    publisher.info('Url;{};{};{};Checked {} URL;{}'.format(
                        PST.p_source, PST.p_date, PST.p_name, A_values[0], PST.p_rel_path))
            prec_filename = filename

        else:
            publisher.debug("Script url is Idling 10s")
            print('Sleeping')
            time.sleep(10)

        message = p.get_from_set()
