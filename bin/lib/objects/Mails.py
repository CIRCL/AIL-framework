#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

import re

# import idna  # punycode  or .encode('idna').decode()

from hashlib import sha256
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects
from lib.ail_core import sscan_iterator
from lib.ConfigLoader import ConfigLoader
from packages import Date
# from lib.data_retention_engine import update_obj_date, get_obj_date_first

from flask import url_for

config_loader = ConfigLoader()
r_object = config_loader.get_db_conn("Kvrocks_Objects")
r_search = config_loader.get_db_conn("Kvrocks_Searchs")
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
        return self._get_field('content')

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
        return self.get_content().rsplit('@', 1)[0]

    def get_domain(self):
        return self.get_content().rsplit('@', 1)[-1]

    def get_username_domain(self):
        return self.get_content().rsplit('@', 1)

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
        self.index()
        return self.id

    def index(self):
        username, domain = self.get_username_domain()
        index_mail(username, domain)

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self): # TODO DELETE CORRELATION
        self._delete()
        self.delete_dates()
        r_object.srem(f'{self.type}:all', self.id)


def create(content, tags=[]):  # TODO sanityze mail
    content = content.strip().lower()
    try:
        punycoded = punycode_encode(content)
    except UnicodeError as e:
        print(content)
        return None

    if punycoded != content:
        obj_id = sha256(content.encode()).hexdigest()
        obj = Mail(obj_id)
    else:
        obj = Mail(content)
    if not obj.exists():
        obj.create(content, tags=tags)
    return obj

def get_mail_id(content):
    content = content.strip().lower()
    try:
        punycoded = punycode_encode(content)
    except UnicodeError as e:
        print(content)
        return None

    if punycoded != content:
        return sha256(content.encode()).hexdigest()
    else:
        return content

def get_mail(content):
    return Mail(get_mail_id(content))

def index_mail(username, domain):
    # TODO check domain validity
    r_search.sadd('m:domains', domain)
    r_search.sadd('m:usernames', username)
    r_search.sadd(f'm:d:{domain}', username)
    r_search.sadd(f'm:u:{username}', domain)

def get_domain_nb_mails(domain):
    return r_search.scard(f'm:d:{domain}')

def is_indexed_domain(domain):
    return r_search.exists(f'm:d:{domain}')

def is_indexed_username(username):
    return r_search.exists(f'm:u:{username}')


def search_domain(s_domain=None, r_pos=False, page=1, nb=500):
    if not s_domain:
        domains = []
        total = r_search.scard('m:domains')
        start = nb * (page - 1)
        stop = start + nb - 1
        cursor = 0
        for domain in r_search.smembers('m:domains'):
            if start <= cursor <= stop:
                domains.append(domain)
            elif cursor > stop:
                break
            cursor += 1
        return total, domains
    else:
        domains = {}
        re_search = re.compile(s_domain)
        total, results = get_cache_search_mail(s_domain=s_domain, page=page, nb=nb)
        if results is None:
            results = []
            start = nb * (page - 1)
            stop = start + nb - 1
            cursor = 0
            for domain in sscan_iterator(r_search, 'm:domains'):
                if s_domain in domain:
                    results.append(domain)
                    if start <= cursor <= stop:
                        domains[domain] = {}
                        if r_pos:
                            res = re.search(re_search, domain)
                            if res:
                                domains[domain]['hl-start'] = res.start()
                                domains[domain]['hl-end'] = res.end()
                                domains[domain]['content'] = domain
                    cursor += 1
            total = len(results)
            if results:
                cache_search_mail(results, s_domain=s_domain)
        else:
            for domain in results:
                domains[domain] = {}
                if r_pos:
                    res = re.search(re_search, domain)
                    if res:
                        domains[domain]['hl-start'] = res.start()
                        domains[domain]['hl-end'] = res.end()
                        domains[domain]['content'] = domain
        return total, domains

def search_domain_username(domain, s_username=None, r_pos=False, page=1, nb=500):
    objs = {}
    if not s_username:
        total = r_search.scard(f'm:d:{domain}')
        start = nb * (page - 1)
        stop = start + nb - 1
        cursor = 0
        for username in sscan_iterator(r_search, f'm:d:{domain}'):
            if start <= cursor <= stop:
                content = f'{username}@{domain}'
                obj_id = get_mail_id(content)
                objs[obj_id] = {}
                objs[obj_id]['content'] = content
            elif cursor > stop:
                break
            cursor += 1
    else:
        re_search = re.compile(s_username)
        total, results = get_cache_search_mail(domain=domain, s_username=s_username, page=page, nb=nb)
        if results is None:
            results = []
            start = nb * (page - 1)
            stop = start + nb - 1
            cursor = 0
            for username in sscan_iterator(r_search, f'm:d:{domain}'):
                if s_username in username:
                    results.append(username)
                    if start <= cursor <= stop:
                        content = f'{username}@{domain}'
                        obj_id = get_mail_id(content)
                        objs[obj_id] = {}
                        if r_pos:
                            res = re.search(re_search, username)
                            if res:
                                objs[obj_id]['hl-start'] = res.start()
                                objs[obj_id]['hl-end'] = res.end()
                                objs[obj_id]['content'] = content
                    cursor += 1
            total = len(results)
            if results:
                cache_search_mail(results, domain=domain, s_username=s_username)
        else:
            for user in results:
                content = f'{user}@{domain}'
                obj_id = get_mail_id(content)
                objs[obj_id] = {}
                if r_pos:
                    res = re.search(re_search, user)
                    if res:
                        objs[obj_id]['hl-start'] = res.start()
                        objs[obj_id]['hl-end'] = res.end()
                        objs[obj_id]['content'] = content
    return total, objs


def search_username_domain(username, s_domain=None, r_pos=False, page=1, nb=500):
    objs = {}
    if not s_domain:
        total = r_search.scard(f'm:u:{username}')
        start = nb * (page - 1)
        stop = start + nb - 1
        cursor = 0
        for domain in sscan_iterator(r_search, f'm:u:{username}'):
            if start <= cursor <= stop:
                content = f'{username}@{domain}'
                obj_id = get_mail_id(content)
                objs[obj_id] = {}
                objs[obj_id]['content'] = content
            if cursor > stop:
                break
            cursor += 1
    else:
        total, results = get_cache_search_mail(username=username, s_domain=s_domain, page=page, nb=page)
        re_search = re.compile(s_domain)
        if results is None:  # TODO no results
            results = []
            start = nb * (page - 1)
            stop = start + nb
            cursor = 0
            for domain in sscan_iterator(r_search, f'm:u:{username}'):
                if s_domain in domain:
                    results.append(domain)
                    if start <= cursor <= stop:
                        content = f'{username}@{domain}'
                        obj_id = get_mail_id(content)
                        objs[obj_id] = {}
                        if r_pos:
                            res = re.search(re_search, domain)
                            if res:
                                objs[obj_id]['hl-start'] = len(username) + 1 + res.start()
                                objs[obj_id]['hl-end'] = len(username) + 1 + res.end()
                                objs[obj_id]['content'] = content
                    cursor += 1
            total = len(results)
            if results:
                cache_search_mail(results, username=username, s_domain=s_domain)
        else:
            for dom in results:
                content = f'{username}@{dom}'
                obj_id = get_mail_id(content)
                objs[obj_id] = {}
                if r_pos:
                    res = re.search(re_search, dom)
                    if res:
                        objs[obj_id]['hl-start'] = len(username) + 1 + res.start()
                        objs[obj_id]['hl-end'] = len(username) + 1 + res.end()
                        objs[obj_id]['content'] = content
    return total, objs


def search_mail(mail=None, username=None, domain=None, s_username=None, s_domain=None, r_pos=False, page=1, nb=500):
    if mail:
        m = get_mail(mail)
        if m.exists():
            return 1, m.get_id()

    if domain:
        if is_indexed_domain(domain):
            return search_domain_username(domain, s_username=s_username, r_pos=r_pos, page=page, nb=nb)
    elif username:
        if is_indexed_username(username):
            return search_username_domain(username, s_domain=s_domain, r_pos=r_pos, page=page, nb=nb)
    elif s_domain:
        return search_domain(s_domain=s_domain, r_pos=r_pos, page=page, nb=nb)
    return None, None

def cache_search_mail(to_cache, username='', domain='', s_username='', s_domain=''):
    for result in to_cache:
        r_cache.rpush(f'm:{username}:{domain}:{s_username}:{s_domain}', result)
    r_cache.expire(f'm:{username}:{domain}:{s_username}:{s_domain}', 1800)

def get_cache_search_mail(username='', domain='', s_username='', s_domain='', page=1, nb=500):
    total = r_cache.llen(f'm:{username}:{domain}:{s_username}:{s_domain}')
    if not total:
        return None, None
    else:
        r_cache.expire(f'm:{username}:{domain}:{s_username}:{s_domain}', 1800)
        start = nb * (page - 1)
        stop = start + nb - 1
        return total, r_cache.lrange(f'm:{username}:{domain}:{s_username}:{s_domain}', start, stop)


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

    def get_domain_meta(self, domains):
        dict_domain = {}
        for domain in domains:
            dict_domain[domain] = {'nb': get_domain_nb_mails(domain)}
        return dict_domain

def _index_all_mails():
    for obj in Mails().get_iterator():
        print(obj.get_id())
        obj.index()

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


if __name__ == '__main__':
    _index_all_mails()
