#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import json
import logging
import os
import requests
import sys

from abc import ABC

sys.path.append(os.environ['AIL_BIN'])
#################################
# Import Project packages
#################################
from exporter.abstract_exporter import AbstractExporter
from lib.ail_core import get_ail_uuid

logger = logging.getLogger()

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
                logger.error(f"Webhook request failed for {self.url}\nReason: {response.reason}")
        except Exception as e:
            logger.error(f"Webhook request failed for {self.url}\nReason: Something went wrong {e}")


class WebHookExporterTracker(WebHookExporter):

    def __init__(self, url=''):
        super().__init__(url=url)

    # TODO Change exported keys
    def export(self, tracker, obj, matches=[]):
        self.set_url(tracker.get_webhook())
        data = {'version': 0,
                'type': 'tracker:match',
                'ail_uuid': get_ail_uuid(),
                'tracker': {
                    'uuid': tracker.get_uuid(),
                    'type': tracker.get_type(),
                    'tags': list(tracker.get_tags()),
                    'tracker': tracker.get_tracked(),
                },
                'obj': {'type': obj.get_type(),
                        'subtype': obj.get_subtype(r_str=True),
                        'id': obj.get_id(),
                        'tags': list(obj.get_tags()),
                        'url': obj.get_link()
                        },
                }
        if matches:
            data['matches'] = matches

        # data = json.dumps(data)
        self._export(data)
