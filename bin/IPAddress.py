#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The IP Module
======================

This module is consuming the global channel.

It first performs a regex to find IP addresses and then matches those IPs to
some configured ip ranges.

The list of IP ranges are expected to be in CIDR format (e.g. 192.168.0.0/16)
and should be defined in the config.cfg file, under the [IP] section

"""

import time
import re
import sys
from pubsublogger import publisher
from packages import Paste
from Helper import Process
from ipaddress import IPv4Network, IPv4Address


def search_ip(message):
    paste = Paste.Paste(message)
    content = paste.get_p_content()
    # regex to find IPs
    reg_ip = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)', flags=re.MULTILINE)
    # list of the regex results in the Paste, may be null
    results = reg_ip.findall(content)
    matching_ips = []

    for ip in results:
        ip = '.'.join([str(int(x)) for x in ip.split('.')])
        address = IPv4Address(ip)
        for network in ip_networks:
            if address in network:
                matching_ips.append(address)

    if len(matching_ips) > 0:
        print('{} contains {} IPs'.format(paste.p_name, len(matching_ips)))
        publisher.warning('{} contains {} IPs'.format(paste.p_name, len(matching_ips)))

        #Tag message with IP
        msg = 'infoleak:automatic-detection="ip";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        #Send to duplicate
        p.populate_set_out(message, 'Duplicate')

if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'IP'
    # Setup the I/O queues
    p = Process(config_section)

    ip_networks = []
    networks = p.config.get("IP", "networks")
    if not networks:
        print('No IP ranges provided')
        sys.exit(0)
    try:
        for network in networks.split(","):
            ip_networks.append(IPv4Network(network))
            print(f'IP Range: {network}')
    except:
        print('Please provide a list of valid IP addresses')
        sys.exit(0)


    # Sent to the logging a description of the module
    publisher.info("Run IP module")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        search_ip(message)
