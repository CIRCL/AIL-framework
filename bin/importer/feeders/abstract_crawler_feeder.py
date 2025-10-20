#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Abstract Crawled Capture JSON Feeder Importer Module
================

Process Feeder Json (example: Manual lacus feeder)

"""
import os
import sys

from abc import ABC

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.feeders.Default import DefaultFeeder
from lib import crawlers


class AbstractCrawlerFeeder(DefaultFeeder, ABC):

    def __init__(self, name, logger, json_data):
        super().__init__(json_data)
        self.obj = None
        self.name = name
        self.crawler_processor = crawlers.CrawlerCapturesProcessor(logger)

    def get_domain_id(self):
        return self.crawler_processor.domain.id

    def process_capture(self):
        return self.crawler_processor.process(self.get_payload())

    # RENAME TO process payload + get_objs ????????????
    def get_obj(self):
        pass

    # Create additional correlation or objects from meta field
    def process_meta(self):
        """
        Process JSON meta filed.
        """
        # objs = []
        # meta = self.get_meta()
        # return objs
        pass
