#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
module
====================

This module send tagged pastes to MISP or THE HIVE Project

"""
import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.exceptions import MISPConnectionError
from lib import Tag
from exporter.MISPExporter import MISPExporterAutoDaily
from exporter.TheHiveExporter import TheHiveExporterAlertTag

class MISP_Thehive_Auto_Push(AbstractModule):
    """MISP_Hive_Feeder module for AIL framework"""

    def __init__(self):
        super(MISP_Thehive_Auto_Push, self).__init__()

        # refresh Tracked Regex
        self.tags = Tag.refresh_auto_push()
        self.last_refresh = time.time()

        self.misp_exporter = MISPExporterAutoDaily()
        self.the_hive_exporter = TheHiveExporterAlertTag()

        # Send module state to logs
        self.logger.info(f"Module {self.module_name} initialized")

    def compute(self, message):
        if self.last_refresh < Tag.get_last_auto_push_refreshed() < 0:
            self.tags = Tag.refresh_auto_push()
            self.last_refresh = time.time()
            self.logger.debug('Tags Auto Push refreshed')

        tag = message
        item = self.get_obj()
        item_id = item.get_id()

        # enabled
        if 'misp' in self.tags:
            if tag in self.tags['misp']:
                r = self.misp_exporter.export(item, tag)
                if r == -1:
                    Tag.set_auto_push_status('misp', 'ConnectionError')
                else:
                    Tag.set_auto_push_status('misp', '')
                    self.logger.info(f'MISP Pushed: {tag} -> {item_id}')

        if 'thehive' in self.tags:
            if tag in self.tags['thehive']:
                r = self.the_hive_exporter.export(item, tag)
                if r == -1:
                    Tag.set_auto_push_status('thehive', 'ConnectionError')
                elif r == -2:
                    Tag.set_auto_push_status('thehive', 'Request Entity Too Large')
                else:
                    Tag.set_auto_push_status('thehive', '')
                    self.logger.info(f'thehive Pushed: {tag} -> {item_id}')


if __name__ == "__main__":
    module = MISP_Thehive_Auto_Push()
    module.run()
