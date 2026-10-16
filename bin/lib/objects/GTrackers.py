#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from hashlib import sha256
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects
from lib.ConfigLoader import ConfigLoader
from lib.ail_misp import finalize_misp_object
from packages import Date
# from lib.data_retention_engine import update_obj_date, get_obj_date_first

from flask import url_for

config_loader = ConfigLoader()
r_object = config_loader.get_db_conn("Kvrocks_Objects")
r_cache = config_loader.get_redis_conn("Redis_Cache")
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


class GTracker(AbstractDaterangeObject):
    """
    AIL Gtracker Object. (strings)
    """

    def __init__(self, id): # TODO modify me to get convert ID if punycode
        super(GTracker, self).__init__('gtracker', id)

    # def get_domain(self):
    #     return self.get_content().rplit('@', 1)[-1]

    def get_date(self):
        return Date.get_today_date_str()

    def get_nb_seen(self):
        return self.get_nb_correlation('domain')

    def get_source(self):  # TODO remove ME
        """
        Returns source/feeder name
        """
        return 'gtracker'

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'fab', 'icon': '\uf1a0', 'color': 'grey', 'radius': 5}

    def get_misp_object(self):
        obj = MISPObject('tracking-id', strict=True, standalone=False)
        obj.add_attribute('id', value=self.id)
        if self.id.startswith('GTM-'):
            obj.add_attribute('tracker', value='Google Tag Manager')
        elif self.id.startswith(('G-', 'UA-')):
            obj.add_attribute('tracker', value='Google Analytics')
        return finalize_misp_object(obj, self.get_global_id(), self.get_tags(), self.get_first_seen(), self.get_last_seen())

    def get_meta(self, options=None, flask_context=False):
        """
        :type options: set
        """
        if options is None:
            options = set()
        meta = self._get_meta(options=options, flask_context=flask_context)
        meta['tags'] = self.get_tags()
        meta['content'] = self.get_content()

        # optional meta fields
        if 'investigations' in options:
            meta['investigations'] = self.get_investigations()
        if 'link' in options:
            meta['link'] = self.get_link(flask_context=True)
        if 'icon' in options:
            meta['svg_icon'] = self.get_svg_icon()
        return meta

    def create(self, tags=[]):
        self._add_create()
        for tag in tags:
            self.add_tag(tag)
        return self.id

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self): # TODO DELETE CORRELATION
        self._delete()
        self.delete_dates()
        r_object.srem(f'{self.type}:all', self.id)


def create(content, tags=[]):
    content = content.strip()
    obj = GTracker(content)
    if not obj.exists():
        obj.create(tags=tags)
    return obj

class GTrackers(AbstractDaterangeObjects):
    """
       GTrackers Objects
    """
    def __init__(self):
        super().__init__('gtracker', GTracker)

    def get_name(self):
        return 'GTrackers'

    def get_icon(self):
        return {'fa': 'fab', 'icon': 'google'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_gtracker.objects_gtrackers')
        else:
            url = f'{baseurl}/objects/gtrackers'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search.lower()

def _remove_all_objects():
    for obj in GTrackers().get_iterator():
        obj.delete()

#### API ####
def api_get_gtracker(obj_id):
    obj = GTracker(obj_id)
    if not obj.exists():
        return {"status": "error", "reason": "Unknown Google Tracking"}, 404
    meta = obj.get_meta({'content', 'icon', 'link'})
    return meta, 200
