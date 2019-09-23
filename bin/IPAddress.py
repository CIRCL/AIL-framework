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
from pubsublogger import publisher
from packages import Paste
from Helper import Process


#
# Thanks to Syed Sadat Nazrul
# URL: https://medium.com/@sadatnazrul/checking-if-ipv4-address-in-network-python-af61a54d714d

def ip_to_binary(ip):
    octet_list_int = ip.split(".")
    octet_list_bin = [format(int(i), '08b') for i in octet_list_int]
    binary = ("").join(octet_list_bin)
    return binary

def get_addr_network(address, net_size):
    #Convert ip address to 32 bit binary
    ip_bin = ip_to_binary(address)
    #Extract Network ID from 32 binary
    network = ip_bin[0:32-(32-net_size)]    
    return network

def ip_in_prefix(ip_address, prefix):
    #CIDR based separation of address and network size
    [prefix_address, net_size] = prefix.split("/")
    #Convert string to int
    net_size = int(net_size)
    #Get the network ID of both prefix and ip based net size
    prefix_network = get_addr_network(prefix_address, net_size)
    ip_network = get_addr_network(ip_address, net_size)
    return ip_network == prefix_network

def search_ip(message):
    paste = Paste.Paste(message)
    content = paste.get_p_content()
    # regex to find IPs
    reg_ip = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)', flags=re.MULTILINE)
    # list of the regex results in the Paste, may be null
    results = reg_ip.findall(content)
    matching_ips = []

    print(results)

    for res in results:
        for network in ip_networks:
            if ip_in_prefix(res,network):
                matching_ips.append(res)

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

    ip_networks = p.config.get("IP", "networks").split(",")


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
