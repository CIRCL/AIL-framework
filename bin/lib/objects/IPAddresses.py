#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import ipaddress
import sys

from pymisp import MISPObject

import requests


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects
from lib.ConfigLoader import ConfigLoader
from lib import crawlers
from lib.objects import Domains
from packages import git_status
from packages import Date
# from lib.data_retention_engine import update_obj_date, get_obj_date_first

from flask import url_for

config_loader = ConfigLoader()
# r_db = config_loader.get_db_conn("Kvrocks_DB")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
# r_cache = config_loader.get_redis_conn("Redis_Cache")
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None

def is_ipv4(ip):
    try:
        ipaddress.IPv4Address(str(ip))
        return True
    except:
        return False

def is_ipv6(ip):
    try:
        ipaddress.IPv6Address(str(ip))
        return True
    except:
        return False

def is_ip(ip):
    try:
        ipaddress.ip_address(str(ip))
        return True
    except:
        return False

def sanitize_ip(ip):
    try:
        ip = ipaddress.ip_address(str(ip))
        return str(ip)
    except:
        return None

def get_ip_type(ip):
    ip = ipaddress.ip_address(str(ip))
    if isinstance(ip, ipaddress.IPv4Address):
        return 'ipv4'
    elif isinstance(ip, ipaddress.IPv6Address):
        return 'ipv6'
    else:
        return None

class IP(AbstractDaterangeObject):
    """
    AIL IP Object. (strings)
    """

    def __init__(self, id):
        super(IP, self).__init__('ip', id)

    def get_date(self):
        return Date.get_today_date_str()

    def get_nb_seen(self):
        return self.get_nb_correlation('ssh-key')

    def get_source(self):  # TODO remove ME
        """
        Returns source/feeder name
        """
        return 'ip'

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf233', 'color': 'yellow', 'radius': 5}

    def get_misp_object(self):  # TODO
        return None
        # obj = MISPObject('passive-ssh', standalone=True)
        # first_seen = self.get_first_seen()
        # last_seen = self.get_last_seen()
        # if not first_seen:
        #     first_seen = self.get_date()
        #     last_seen = first_seen
        # obj.first_seen = first_seen
        # obj.last_seen = last_seen
        # # hassh ???
        # obj_attrs = [obj.add_attribute('first-seen', value=first_seen),
        #              obj.add_attribute('last_seen', value=last_seen),
        #              obj.add_attribute('fingerprint', value=self.id)]
        # for obj_attr in obj_attrs:
        #     for tag in self.get_tags():
        #         obj_attr.add_tag(tag)
        # return obj

    # options: set of optional meta fields
    def get_meta(self, options=None):  # TODO get HOSTS
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


def create(ip_address, tags=[]):
    ip_address = ip_address.strip()
    obj = IP(ip_address)
    if not obj.exists():
        obj.create(tags=tags)
    return obj

class IPs(AbstractDaterangeObjects):
    """
       IPs Objects
    """
    def __init__(self):
        super().__init__('ip', IP)

    def get_name(self):
        return 'IPs'

    def get_icon(self):
        return {'fa': 'fas', 'icon': 'server'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_ssh.objects_ssh_keys')
        else:
            url = f'{baseurl}/objects/ips'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search.lower()

def _remove_all_objects():
    for obj in Ips().get_iterator():
        obj.delete()


#### API ####
def api_get_ssh_key(obj_id):
    obj = IP(obj_id)
    if not obj.exists():
        return {"status": "error", "reason": "Unknown IP"}, 404
    meta = obj.get_meta({'content', 'icon', 'link'})
    return meta, 200

