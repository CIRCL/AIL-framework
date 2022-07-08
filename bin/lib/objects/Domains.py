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

    def get_first_seen(selfr_int=False, separator=True):
        first_seen = r_onion.hget(f'{self.domain_type}_metadata:{self.id}', 'first_seen')
        if first_seen:
            if separator:
                first_seen = f'{first_seen[0:4]}/{first_seen[4:6]}/{first_seen[6:8]}'
                first_seen = int(first_seen)
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

    def get_ports(self):
        l_ports = r_onion.hget(f'{self.domain_type}_metadata:{self.id}', 'ports')
        if l_ports:
            return l_ports.split(";")
        return []

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

    ############################################################################
    ############################################################################
    ############################################################################

    def exist_correlation(self):
        pass

    ############################################################################
    ############################################################################



#if __name__ == '__main__':
