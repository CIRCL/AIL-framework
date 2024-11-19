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
from packages import Date
# from lib.data_retention_engine import update_obj_date, get_obj_date_first

from flask import url_for

config_loader = ConfigLoader()
r_object = config_loader.get_db_conn("Kvrocks_Objects")
r_cache = config_loader.get_redis_conn("Redis_Cache")
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
IMAGE_FOLDER = config_loader.get_files_directory('images')
config_loader = None

# SET x1,y1:x2,y2:x3,y3:x4,y4:extracted_text

class Barcode(AbstractDaterangeObject):
    """
    AIL Message Object. (strings)
    """

    def __init__(self, id):
        super(Barcode, self).__init__('barcode', id)

    def get_content(self, r_type='str'):
        """
        Returns content
        """
        global_id = self.get_global_id()
        content = r_cache.get(f'content:{global_id}')
        if not content:
            content = self._get_field('content')
            # Set Cache
            if content:
                global_id = self.get_global_id()
                r_cache.set(f'content:{global_id}', content)
                r_cache.expire(f'content:{global_id}', 300)
        if r_type == 'str':
            return content
        elif r_type == 'bytes':
            if content:
                return content.encode()

    def get_date(self):  # TODO
        return Date.get_today_date_str()

    def get_nb_seen(self):
        return self.get_nb_correlation('image') + self.get_nb_correlation('screenshot')

    def get_source(self):  # TODO
        """
        Returns source/feeder name
        """
        return 'barcode'

    def get_basename(self):  # TODO
        return 'barcode'

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):  # TODO
        return {'style': 'fas', 'icon': '\uf02a', 'color': 'yellow', 'radius': 5}

    def get_misp_object(self):  # TODO
        pass
    #     obj = MISPObject('instant-message', standalone=True)
    #     obj_date = self.get_date()
    #     if obj_date:
    #         obj.first_seen = obj_date
    #     else:
    #         self.logger.warning(
    #             f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={obj_date}')
    #
    #     # obj_attrs = [obj.add_attribute('first-seen', value=obj_date),
    #     #              obj.add_attribute('raw-data', value=self.id, data=self.get_raw_content()),
    #     #              obj.add_attribute('sensor', value=get_ail_uuid())]
    #     obj_attrs = []
    #     for obj_attr in obj_attrs:
    #         for tag in self.get_tags():
    #             obj_attr.add_tag(tag)
    #     return obj

    # options: set of optional meta fields
    def get_meta(self, options=None):
        """
        :type options: set
        """
        if options is None:
            options = set()
        meta = self._get_meta(options=options)
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

    def create(self, content, im_obj, tags=[]):
        self._set_field('content', content)
        if im_obj.type == 'screenshot':
            for date in im_obj.get_dates():
                self._add(date, None)
        else:
            self._copy_from(im_obj.type, im_obj.get_id())

        for tag in tags:
            self.add_tag(tag)
        return self.id

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        r_object.delete(f'barcode:{self.id}')


def create(content, im_obj, tags=[]):
    if content:
        obj_id = sha256(content.encode()).hexdigest()
        obj = Barcode(obj_id)
        if not obj.exists():
            obj.create(content, im_obj, tags=tags)
        return obj

class Barcodes(AbstractDaterangeObjects):
    """
        Barcodes Objects
    """
    def __init__(self):
        super().__init__('barcode', Barcode)

    def get_name(self):
        return 'Barcodes'

    def get_icon(self):
        return {'fa': 'fas', 'icon': 'barcode'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_barcode.objects_barcodes')
        else:
            url = f'{baseurl}/objects/barcodes'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search  # TODO


#### API ####
def api_get_barcode(obj_id):
    obj = Barcode(obj_id)
    if not obj.exists():
        return {"status": "error", "reason": "Unknown barcode"}, 404
    meta = obj.get_meta({'content', 'icon', 'link'})
    return meta, 200
