#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

# import idna  # punycode  or .encode('idna').decode()

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
config_loader = None

def punycode_encode(text):
    return text.encode('idna').decode()

def punycode_decode(text):
    return text.encode().decode('idna')


class Mail(AbstractDaterangeObject):
    """
    AIL Message Object. (strings)
    """

    def __init__(self, id): # TODO modify me to get convert ID if punycode
        super(Mail, self).__init__('mail', id)

    def _get_content(self):
        self._get_field('content')

    def get_content(self, r_type='str'):
        """
        Returns content
        """
        if '@' in self.id:
            return self.id
        else:
            return self._get_content()

    def punycode_encode(self, text):
        return punycode_encode(text)

    def punycode_decode(self, text):
        return punycode_decode(text)

    def get_username(self):
        return self.get_content().rplit('@', 1)[0]

    def get_domain(self):
        return self.get_content().rplit('@', 1)[-1]

    # TODO PLUG CRED DB

    def get_date(self):
        return Date.get_today_date_str()

    def get_nb_seen(self):
        return self.get_nb_correlation('message') + self.get_nb_correlation('item')

    def get_source(self):  # TODO remove ME
        """
        Returns source/feeder name
        """
        return 'mail'

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf0e0', 'color': 'grey', 'radius': 5}

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

    def create(self, content, tags=[]):
        self._add_create()
        if content != self.id:
            self._set_field('content', content)
        for tag in tags:
            self.add_tag(tag)
        return self.id

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self): # TODO DELETE CORRELATION
        self._delete()
        self.delete_dates()
        r_object.srem(f'{self.type}:all', self.id)


def create(content, tags=[]):  # TODO sanityze mail
    content = content.strip().lower()
    punycoded = punycode_encode(content)
    if punycoded != content:
        obj_id = sha256(content.encode()).hexdigest()
        obj = Mail(obj_id)
    else:
        obj = Mail(content)
    if not obj.exists():
        obj.create(content, tags=tags)
    return obj

class Mails(AbstractDaterangeObjects):
    """
       Mails Objects
    """
    def __init__(self):
        super().__init__('mail', Mail)

    def get_name(self):
        return 'Mails'

    def get_icon(self):
        return {'fa': 'fas', 'icon': 'envelope'}

    def get_link(self, flask_context=False):   # TODO CHANGE TO UI TARGET
        if flask_context:
            url = url_for('objects_mail.objects_mails')
        else:
            url = f'{baseurl}/objects/mails'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search.lower()

def _remove_all_mails():
    for obj in Mails().get_iterator():
        obj.delete()

#### API ####
def api_get_mail(obj_id):
    obj = Mail(obj_id)
    if not obj.exists():
        return {"status": "error", "reason": "Unknown mail"}, 404
    meta = obj.get_meta({'content', 'icon', 'link'})
    return meta, 200
