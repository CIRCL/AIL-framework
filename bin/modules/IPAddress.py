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
import os
import re
import sys

from ipaddress import IPv4Network, IPv4Address

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import regex_helper

# TODO REWRITE ME -> PERF + IPV6 + Tracker ?

class IPAddress(AbstractModule):
    """IPAddress module for AIL framework"""

    def __init__(self):
        super(IPAddress, self).__init__()

        config_loader = ConfigLoader()

        # Config Load ip_networks
        self.ip_networks = set()
        networks = config_loader.get_config_str("IP", "networks")
        if not networks:
            print('No IP ranges provided')
            # sys.exit(0)
        else:
            try:
                for network in networks.split(","):
                    self.ip_networks.add(IPv4Network(network))
                    print(f'IP Range To Search: {network}')
            except:
                print('Please provide a list of valid IP addresses')
                sys.exit(0)

        self.re_ipv4 = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
        re.compile(self.re_ipv4)

        self.redis_cache_key = regex_helper.generate_redis_cache_key(self.module_name)
        self.max_execution_time = 60

        # Send module state to logs
        self.logger.info(f"Module {self.module_name} initialized")

    def compute(self, message, r_result=False):
        if not self.ip_networks:
            return None

        obj = self.get_obj()
        content = obj.get_content()

        # list of the regex results in the Item
        results = self.regex_findall(self.re_ipv4, obj.get_id(), content)
        results = set(results)
        matching_ips = []
        for ip in results:
            ip = '.'.join([str(int(x)) for x in ip.split('.')])
            address = IPv4Address(ip)
            for network in self.ip_networks:
                if address in network:
                    self.logger.info(address)
                    matching_ips.append(address)

        if len(matching_ips) > 0:
            self.logger.info(f'{self.obj.get_global_id()} contains {len(matching_ips)} IPs')

            # Tag message with IP
            tag = 'infoleak:automatic-detection="ip"'
            self.add_message_to_queue(message=tag, queue='Tags')


if __name__ == "__main__":
    module = IPAddress()
    module.run()
