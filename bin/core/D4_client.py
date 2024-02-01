#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The D4_Client Module
============================

The D4_Client modules send all DNS records to a D4 Server.
Data produced by D4 sensors are ingested into
a Passive DNS server which can be queried later to search for the Passive DNS records.
"""

import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
#################################
from modules.abstract_module import AbstractModule
from lib import d4

# # TODO: launch me in core screen
# # TODO: check if already launched in core screen

class D4Client(AbstractModule):
    """
        D4Client module for AIL framework
    """

    def __init__(self):
        super(D4Client, self).__init__()

        self.d4_client = d4.create_d4_client()
        self.last_refresh = time.time()
        self.last_config_check = time.time()

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def compute(self, dns_record):
        # Refresh D4 Client
        if self.last_config_check < int(time.time()) - 30:
            print('refresh rrrr')
            if self.last_refresh < d4.get_config_last_update_time():
                self.d4_client = d4.create_d4_client()
                self.last_refresh = time.time()
                print('D4 Client: config updated')
            self.last_config_check = time.time()

        if self.d4_client:
            # Send DNS Record to D4Server
            self.d4_client.send_manual_data(dns_record)


if __name__ == '__main__':
    module = D4Client()
    module.run()
