#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_object import AbstractObject

from lib.item_basic import get_item_children, get_item_date, get_item_url
from lib import data_retention_engine

config_loader = ConfigLoader()
r_onion = config_loader.get_redis_conn("ARDB_Onion")
config_loader = None


################################################################################
################################################################################
################################################################################

class Domain(AbstractObject):
    """
    AIL Decoded Object. (strings)
    """

    # id: domain name
    def __init__(self, id):
        super(Domain, self).__init__('domain', id)
        self.domain_type = self.get_domain_type()

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    def get_domain_type(self):
        if str(self.id).endswith('.onion'):
            return 'onion'
        else:
            return 'regular'

    def get_first_seen(self, r_int=False, separator=True):
        first_seen = r_onion.hget(f'{self.domain_type}_metadata:{self.id}', 'first_seen')
        if first_seen:
            if separator:
                first_seen = f'{first_seen[0:4]}/{first_seen[4:6]}/{first_seen[6:8]}'
            elif r_int==True:
                first_seen = int(first_seen)
        return first_seen

    def get_last_check(self, r_int=False, separator=True):
        last_check = r_onion.hget(f'{self.domain_type}_metadata:{self.id}', 'last_check')
        if last_check is not None:
            if separator:
                last_check = f'{last_check[0:4]}/{last_check[4:6]}/{last_check[6:8]}'
            elif r_format=="int":
                last_check = int(last_check)
        return last_check

    def _set_first_seen(self, date):
        r_onion.hset(f'{self.domain_type}_metadata:{self.id}', 'first_seen', date)

    def _set_last_check(self, date):
        r_onion.hset(f'{self.domain_type}_metadata:{self.id}', 'last_check', date)

    def update_daterange(self, date):
        first_seen = self.get_first_seen(r_int=True)
        last_check = self.get_last_check(r_int=True)
        if not first_seen:
            self._set_first_seen(date)
            self._set_last_check(date)
        elif int(first_seen) > date:
            self._set_first_seen(date)
        elif int(last_check) < date:
            self._set_last_check(date)

    def get_last_origin(self):
        return r_onion.hget(f'{self.domain_type}_metadata:{self.id}', 'paste_parent')

    def set_last_origin(self, origin_id):
        r_onion.hset(f'{self.domain_type}_metadata:{self.id}', 'paste_parent', origin_id)

    def is_up(self, ports=[]):
        if not ports:
            ports = self.get_ports()
        for port in ports:
            res = r_onion.zrevrange(f'crawler_history_{self.domain_type}:{self.id}:{port}', 0, 0, withscores=True)
            if res:
                item_core, epoch = res[0]
                try:
                    epoch = int(item_core)
                except:
                    print('True')
                    return True
        print('False')
        return False

    def was_up(self):
        return r_onion.hexists(f'{self.domain_type}_metadata:{self.id}', 'ports')

    def get_ports(self, r_set=False):
        l_ports = r_onion.hget(f'{self.domain_type}_metadata:{self.id}', 'ports')
        if l_ports:
            l_ports = l_ports.split(";")
            if r_set:
                return set(l_ports)
            else:
                return l_ports
        return []

    def _set_ports(self, ports):
        ports = ';'.join(ports)
        r_onion.hset(f'{self.domain_type}_metadata:{self.id}', 'ports', ports)

    def add_ports(self, port):
        ports = self.get_ports(r_set=True)
        ports.add(port)
        self._set_ports(ports)

    def get_history_by_port(self, port, status=False, root=False):
        '''
        Return .

        :return:
        :rtype: list of tuple (item_core, epoch)
        '''
        history_tuple = r_onion.zrange(f'crawler_history_{self.domain_type}:{self.id}:{port}', 0, -1, withscores=True)
        history = []
        for root_id, epoch in history_tuple:
            dict_history = {}
            epoch = int(epoch) # force int
            dict_history["epoch"] = epoch
            dict_history["date"] = time.strftime('%Y/%m/%d - %H:%M.%S', time.gmtime(epoch_val))
            try:
                int(root_item)
                if status:
                    dict_history['status'] = False
            except ValueError:
                if status:
                    dict_history['status'] = True
                if root:
                    dict_history['root'] = root_id
            history.append(dict_history)
        return history

    def get_languages(self):
        return r_onion.smembers(f'domain:language:{self.id}')

    def get_meta_keys(self):
        return ['type', 'first_seen', 'last_check', 'last_origin', 'ports', 'status', 'tags', 'languages']

    # options: set of optional meta fields
    def get_meta(self, options=set()):
        meta = {}
        meta['type'] = self.domain_type
        meta['first_seen'] = self.get_first_seen()
        meta['last_check'] = self.get_last_check()
        meta['tags'] = self.get_tags()
        meta['ports'] = self.get_ports()
        meta['status'] = self.is_up(ports=meta['ports'])

        if 'last_origin' in options:
            meta['last_origin'] = self.get_last_origin()
        #meta['is_tags_safe'] = ##################################
        if 'languages' in options:
            meta['languages'] = self.get_languages()
        #meta['screenshot'] =
        return meta


    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('crawler_splash.showDomain', domain=self.id)
        else:
            url = f'{baseurl}/crawlers/showDomain?domain={self.id}'
        return url

    def get_svg_icon(self):
        color = '#3DA760'
        if self.get_domain_type() == 'onion':
            style = 'fas'
            icon = '\uf06e'
        else:
            style = 'fab'
            icon = '\uf13b'
        return {'style': style, 'icon': icon, 'color':color, 'radius':5}

    def is_crawled_item(self, item_id):
        domain_lenght = len(self.id)
        if len(item_id) > (domain_lenght+48):
            if item_id[-36-domain_lenght:-36] == self.id:
                return True
        return False

    def get_crawled_items(self, root_id):
        crawled_items = self.get_crawled_items_children(root_id)
        crawled_items.append(root_id)
        return crawled_items

    def get_crawled_items_children(self, root_id):
        crawled_items = []
        for item_id in get_item_children(root_id):
            if self.is_crawled_item(item_id):
                crawled_items.append(item_id)
                crawled_items.extend(self.get_crawled_items_children(self.id, item_id))
        return crawled_items

    def get_all_urls(self, date=False): ## parameters to add first_seen/last_seen ??????????????????????????????
        if date:
            urls = {}
        else:
            urls = set()
        for port in self.get_ports():
            for history in self.get_history_by_port(port, root=True):
                if history.get('root'):
                    for item_id in self.get_crawled_items(history.get('root')):
                        url = get_item_url(item_id)
                        if url:
                            if date:
                                item_date = int(get_item_date(item_id))
                                if url not in urls:
                                    urls[url] = {'first_seen': item_date,'last_seen': item_date}
                                else: # update first_seen / last_seen
                                    if item_date < urls[url]['first_seen']:
                                        all_url[url]['first_seen'] = item_date
                                    if item_date > urls[url]['last_seen']:
                                        all_url[url]['last_seen'] = item_date
                            else:
                                urls.add(url)
        return urls

    def get_misp_object(self):
        # create domain-ip obj
        obj_attrs = []
        obj = MISPObject('domain-crawled', standalone=True)
        obj.first_seen = self.get_first_seen()
        obj.last_seen = self.get_last_check()

        obj_attrs.append( obj.add_attribute('domain', value=self.id) )
        urls = self.get_all_urls(date=True)
        for url in urls:
            attribute = obj.add_attribute('url', value=url)
            attribute.first_seen = str(urls[url]['first_seen'])
            attribute.last_seen = str(urls[url]['last_seen'])
            obj_attrs.append( attribute )
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def add_language(self, language):
        r_onion.sadd('all_domains_languages', language)
        r_onion.sadd(f'all_domains_languages:{self.domain_type}', language)
        r_onion.sadd(f'language:domains:{self.domain_type}:{language}', self.id)
        r_onion.sadd(f'domain:language:{self.id}', language)


    ############################################################################
    ############################################################################


    def create(self, first_seen, last_check, ports, status, tags, languages):


        r_onion.hset(f'{self.domain_type}_metadata:{self.id}', 'first_seen', first_seen)
        r_onion.hset(f'{self.domain_type}_metadata:{self.id}', 'last_check', last_check)

        for language in languages:
            self.add_language(language)

    #### CRAWLER ####

    # add root_item to history
    # if domain down -> root_item = epoch
    def _add_history_root_item(self, root_item, epoch, port):
        # Create/Update crawler history
        r_onion.zadd(f'crawler_history_{self.domain_type}:{self.id}:{port}', epoch, int(root_item))

    # if domain down -> root_item = epoch
    def add_history(self, epoch, port, root_item=None, date=None):
        if not date:
            date = time.strftime('%Y%m%d', time.gmtime(epoch))
        try:
            int(root_item)
        except ValueError:
            root_item = None

        data_retention_engine.update_object_date('domain', self.domain_type, date)
        update_first_object_date(date, self.domain_type)
        update_last_object_date(date, self.domain_type)
        # UP
        if root_item:
            r_onion.srem(f'full_{self.domain_type}_down', self.id)
            r_onion.sadd(f'full_{self.domain_type}_up', self.id)
            r_onion.sadd(f'{self.domain_type}_up:{date}', self.id) # # TODO:  -> store first day
            r_onion.sadd(f'month_{self.domain_type}_up:{date[0:6]}', self.id) # # TODO:  -> store first month
            self._add_history_root_item(root_item, epoch, port)
        else:
            if port:
                r_onion.sadd(f'{self.domain_type}_down:{date}', self.id) # # TODO:  -> store first month
                self._add_history_root_item(epoch, epoch, port)
            else:
                r_onion.sadd(f'{self.domain_type}_down:{date}', self.id)
                if not self.was_up():
                    r_onion.sadd(f'full_{self.domain_type}_down', self.id)

    def add_crawled_item(self, url, port, item_id, item_father):
        r_metadata.hset(f'paste_metadata:{item_id}', 'father', item_father)
        r_metadata.hset(f'paste_metadata:{item_id}', 'domain', f'{self.id}:{port}')
        r_metadata.hset(f'paste_metadata:{item_id}', 'real_link', url)
        # add this item_id to his father
        r_metadata.sadd(f'paste_children:{item_father}', item_id)

    ##-- CRAWLER --##


    ############################################################################
    ############################################################################

def get_all_domains_types():
    return ['onion', 'regular'] # i2p

def get_all_domains_languages():
    return r_onion.smembers('all_domains_languages')

def get_domains_up_by_type(domain_type):
    return r_onion.smembers(f'full_{domain_type}_up')

def get_domains_down_by_type(domain_type):
    return r_onion.smembers(f'full_{domain_type}_down')

def get_first_object_date(subtype, field=''):
    first_date = r_onion.zscore('objs:first_date', f'domain:{subtype}:{field}')
    if not first_date:
        first_date = 99999999
    return int(first_date)

def get_last_object_date(subtype, field=''):
    last_date = r_onion.zscore('objs:last_date', f'domain:{subtype}:{field}')
    if not last_date:
        last_date = 0
    return int(last_date)

def _set_first_object_date(date, subtype, field=''):
    return r_onion.zadd('objs:first_date', f'domain:{subtype}:{field}', date)

def _set_last_object_date(date, subtype, field=''):
    return r_onion.zadd('objs:last_date', f'domain:{subtype}:{field}', date)

def update_first_object_date(date, subtype, field=''):
    first_date = get_first_object_date(subtype, field=field)
    if int(date) < first_date:
        _set_first_object_date(date, subtype, field=field)
        return date
    else:
        return first_date

def update_last_object_date(date, subtype, field=''):
    last_date = get_last_object_date(subtype, field=field)
    if int(date) > last_date:
        _set_last_object_date(date, subtype, field=field)
        return date
    else:
        return last_date


################################################################################
################################################################################

#if __name__ == '__main__':
