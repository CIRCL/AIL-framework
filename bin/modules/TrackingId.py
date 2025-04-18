#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Keys Module
======================

This module is consuming the Redis-list created by the Global module.

It is looking for PGP, private and encrypted private,
RSA private key, certificate messages

"""

##################################
# Import External packages
##################################
import os
import re
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects import GTrackers


class TrackingId(AbstractModule):
    """
    Keys module for AIL framework
    """

    def __init__(self):
        super(TrackingId, self).__init__()

        self.gtm_regex = r"GTM-[A-Z0-9]{6,8}"
        re.compile(self.gtm_regex)
        self.analytics_gtm_regex = r"G-[A-Z0-9]{10}"
        re.compile(self.analytics_gtm_regex)

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

    def compute(self, message): # TODO RESTRICT TO CRAWLED CONTENT ????
        obj = self.get_obj()
        content = obj.get_content()
        to_tag = False
        nb = 0
        source = self.obj.get_source()
        if not self.obj.type == 'item':
            return None
        if source != 'crawled':
            return None

        date = self.obj.get_date()

        # if 'googletagmanager.com' in content:
        if 'GTM-' in content:
            g_ids = self.regex_findall(self.gtm_regex, obj.get_global_id(), content)
            if g_ids:
                to_tag = True
                for g_id in g_ids:
                    gt = GTrackers.create(g_id)
                    gt.add(date, self.obj)
                    nb += 1

        if 'G-' in content:
            g_ids = self.regex_findall(self.analytics_gtm_regex, obj.get_global_id(), content)
            if g_ids:
                to_tag = True
                for g_id in g_ids:
                    gt = GTrackers.create(g_id)
                    gt.add(date, self.obj)
                    nb += 1

        if to_tag:
            msg = f'Extracted {nb} google tracker;{self.obj.get_global_id()}'
            self.logger.info(msg)
            # Tags
            tag = 'infoleak:automatic-detection="tracking-id"'
            self.add_message_to_queue(message=tag, queue='Tags')

        return None


if __name__ == '__main__':
    module = TrackingId()
    module.run()
