#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import os
import requests
import sys

from abc import ABC

sys.path.append(os.environ['AIL_BIN'])
#################################
# Import Project packages
#################################
from exporter.abstract_exporter import AbstractExporter

# from ConfigLoader import ConfigLoader
# from lib.objects.abstract_object import AbstractObject
# from lib.Tracker import Tracker

class WebHookExporter(AbstractExporter, ABC):
    def __init__(self, url=''):
        super().__init__()
        self.url = url

    def set_url(self, url):
        self.url = url

    def _export(self, data):
        try:
            response = requests.post(self.url, json=data)
            if response.status_code >= 400:
                print(f"Webhook request failed for {self.url}\nReason: {response.reason}")
                # self.redis_logger.error(f"Webhook request failed for {webhook_to_post}\nReason: {response.reason}")
        except Exception as e:
            print(f"Webhook request failed for {self.url}\nReason: Something went wrong {e}")
            # self.redis_logger.error(f"Webhook request failed for {webhook_to_post}\nReason: Something went wrong")


class WebHookExporterTracker(WebHookExporter):

    def __init__(self, url=''):
        super().__init__(url=url)

    # TODO Change exported keys
    def export(self, tracker, obj):
        self.set_url(tracker.get_webhook())
        data = {'trackerId': tracker.get_uuid(),
                'trackerType': tracker.get_type(),
                'tags': tracker.get_tags(),
                'tracker': tracker.get_tracked(),
                # object
                'itemId': obj.get_id(),
                'itemURL': obj.get_link()}
        # Item
        # data['itemDate'] = obj.get_date()
        # data["itemSource"] = obj.get_source()

        self._export(data)
