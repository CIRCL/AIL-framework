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
from pubsublogger import publisher
sys.path.append(os.environ['AIL_BIN'])
from Helper import Process

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader
import d4

# # TODO: lauch me in core screen
# # TODO: check if already launched in core screen

if __name__ == '__main__':
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'D4_client'
    p = Process(config_section)
    publisher.info("""D4_client is Running""")

    last_refresh = time.time()
    d4_client = d4.create_d4_client()

    while True:
        if last_refresh < d4.get_config_last_update_time():
            d4_client = d4.create_d4_client()
            last_refresh = time.time()
            print('D4 Client: config updated')

        dns_record = p.get_from_set()
        if dns_record is None:
            publisher.debug("Script D4_client is idling 1s")
            time.sleep(1)
            continue

        if d4_client:
            # Send DNS Record to D4Server
            d4_client.send_manual_data(dns_record)
