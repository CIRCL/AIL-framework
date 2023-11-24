#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Bgp Monitor Feeder Importer Module
================

Process Bgp Monitor JSON

"""
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.feeders.Default import DefaultFeeder
from lib.objects.Items import Item


class BgpMonitorFeeder(DefaultFeeder):
    """BgpMonitorFeeder Feeder functions"""

    def __init__(self, json_data):
        super().__init__(json_data)
        self.name = 'bgp_monitor'

    def process_meta(self):
        """
        Process JSON meta filed.
        """
        # DIRTY FIX
        tag = 'infoleak:automatic-detection=bgp_monitor'
        item = Item(self.get_item_id())
        item.add_tag(tag)
        return set()
