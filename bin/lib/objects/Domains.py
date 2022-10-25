#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import zipfile

from datetime import datetime
from flask import url_for
from io import BytesIO
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader
from lib.objects.abstract_object import AbstractObject

from lib.item_basic import get_item_children, get_item_date, get_item_url, get_item_har
from lib import data_retention_engine

from packages import Date

config_loader = ConfigLoader.ConfigLoader()
r_crawler = config_loader.get_db_conn("Kvrocks_Crawler")

r_metadata = config_loader.get_redis_conn("ARDB_Metadata") ######################################

baseurl = config_loader.get_config_str("Notifications", "ail_domain")
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
            return 'web'

    def exists(self):
        return r_crawler.exists(f'domain:meta:{self.id}')

    def get_first_seen(self, r_int=False, separator=True):
        first_seen = r_crawler.hget(f'domain:meta:{self.id}', 'first_seen')
        if first_seen:
            if r_int:
                first_seen = int(first_seen)
            elif separator:
                first_seen = f'{first_seen[0:4]}/{first_seen[4:6]}/{first_seen[6:8]}'
        return first_seen

    def get_last_check(self, r_int=False, separator=True):
        last_check = r_crawler.hget(f'domain:meta:{self.id}', 'last_check')
        if last_check is not None:
            if r_int:
                last_check = int(last_check)
            elif separator:
                last_check = f'{last_check[0:4]}/{last_check[4:6]}/{last_check[6:8]}'
        return last_check

    def _set_first_seen(self, date):
        r_crawler.hset(f'domain:meta:{self.id}', 'first_seen', date)

    def _set_last_check(self, date):
        r_crawler.hset(f'domain:meta:{self.id}', 'last_check', date)

    def update_daterange(self, date):
        date = int(date)
        first_seen = self.get_first_seen(r_int=True)
        last_check = self.get_last_check(r_int=True)
        if not first_seen:
            self._set_first_seen(date)
            self._set_last_check(date)
        elif int(first_seen) > date:
            self._set_first_seen(date)
        elif int(last_check) < date:
            self._set_last_check(date)

    def get_last_origin(self, obj=False):
        origin = {'item': r_crawler.hget(f'domain:meta:{self.id}', 'last_origin')}
        if obj and origin['item']:
            if origin['item'] != 'manual' and origin['item'] != 'auto':
                item_id = origin['item']
                origin['domain'] = r_metadata.hget(f'paste_metadata:{item_id}', 'domain')
                origin['url'] = r_metadata.hget(f'paste_metadata:{item_id}', 'url')
        return origin

    def set_last_origin(self, origin_id):
        r_crawler.hset(f'domain:meta:{self.id}', 'last_origin', origin_id)

    def is_up(self):
        res = r_crawler.zrevrange(f'domain:history:{self.id}', 0, 0, withscores=True)
        if res:
            item_core, epoch = res[0]
            try:
                int(item_core)
            except ValueError:
                return True
        return False

    def was_up(self):
        return r_crawler.exists(f'domain:history:{self.id}')

    def is_up_by_month(self, date_month):
        # FIXME DIRTY PATCH
        if r_crawler.exists(f'month_{self.domain_type}_up:{date_month}'):
            return r_crawler.sismember(f'month_{self.domain_type}_up:{date_month}', self.get_id())
        else:
            return False

    def is_up_this_month(self):
        date_month = datetime.now().strftime("%Y%m")
        return self.is_up_by_month(date_month)

    def is_down_by_day(self, date):
        # FIXME DIRTY PATCH
        if r_crawler.exists(f'{self.domain_type}_down:{date}'):
            return r_crawler.sismember(f'{self.domain_type}_down:{date}', self.id)
        else:
            return False

    def is_down_today(self):
        date = datetime.now().strftime("%Y%m%d")
        return self.is_down_by_day(date)

    def is_up_by_epoch(self, epoch):
        history = r_crawler.zrevrangebyscore(f'domain:history:{self.id}', int(epoch), int(epoch))
        if not history:
            return False
        else:
            history = history[0]
            try:
                int(history)
                return False
            except ValueError:
                return True

    def get_ports(self, r_set=False):
        l_ports = r_crawler.hget(f'domain:meta:{self.id}', 'ports')
        if l_ports:
            l_ports = l_ports.split(";")
        else:
            l_ports = []
        if r_set:
            return set(l_ports)
        else:
            return l_ports

    def _set_ports(self, ports):
        ports = ';'.join(str(p) for p in ports)
        r_crawler.hset(f'domain:meta:{self.id}', 'ports', ports)

    def add_ports(self, port):
        ports = self.get_ports(r_set=True)
        ports.add(port)
        self._set_ports(ports)

    def get_history(self, status=False, root=False):
        """
        Return .

        :return:
        :rtype: list of tuple (item_core, epoch)
        """
        history_tuple = r_crawler.zrange(f'domain:history:{self.id}', 0, -1, withscores=True)
        history = []
        for root_id, epoch in history_tuple:
            dict_history = {}
            epoch = int(epoch)  # force int
            dict_history["epoch"] = epoch
            dict_history["date"] = time.strftime('%Y/%m/%d - %H:%M.%S', time.gmtime(epoch))
            try:
                int(root_id)
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
        return r_crawler.smembers(f'domain:language:{self.id}')

    def get_meta_keys(self):
        return ['type', 'first_seen', 'last_check', 'last_origin', 'ports', 'status', 'tags', 'languages']

    # options: set of optional meta fields
    def get_meta(self, options=set()):
        meta = {'type': self.domain_type,
                'id': self.id,
                'domain': self.id, # TODO Remove me -> Fix templates
                'first_seen': self.get_first_seen(),
                'last_check': self.get_last_check(),
                'tags': self.get_tags(r_list=True),
                'status': self.is_up()
                }
        # meta['ports'] = self.get_ports()

        if 'last_origin' in options:
            meta['last_origin'] = self.get_last_origin(obj=True)
        # meta['is_tags_safe'] = ##################################
        if 'languages' in options:
            meta['languages'] = self.get_languages()
        # meta['screenshot'] =
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
        return {'style': style, 'icon': icon, 'color': color, 'radius': 5}

    def is_crawled_item(self, item_id):
        domain_length = len(self.id)
        if len(item_id) > (domain_length+48):
            if item_id[-36-domain_length:-36] == self.id:
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
                crawled_items.extend(self.get_crawled_items_children(item_id))
        return crawled_items

    def get_last_item_root(self):
        root_item = r_crawler.zrevrange(f'domain:history:{self.id}', 0, 0, withscores=True)
        if not root_item:
            return None
        root_item = root_item[0][0]
        try:
            int(root_item)
            return None
        except ValueError:
            pass
        return root_item

    def get_item_root_by_epoch(self, epoch):
        root_item = r_crawler.zrevrangebyscore(f'domain:history:{self.id}', int(epoch), int(epoch), withscores=True)
        if not root_item:
            return None
        root_item = root_item[0][0]
        try:
            int(root_item)
            return None
        except ValueError:
            pass
        return root_item

    def get_crawled_items_by_epoch(self, epoch=None):
        if epoch:
            root_item = self.get_item_root_by_epoch(epoch)
        else:
            root_item = self.get_last_item_root()
        if root_item:
            return self.get_crawled_items(root_item)

    # TODO FIXME
    def get_all_urls(self, date=False, epoch=None):
        if date:
            urls = {}
        else:
            urls = set()

        items = self.get_crawled_items_by_epoch(epoch=epoch)
        if items:
            for item_id in items:
                url = get_item_url(item_id)
                if url:
                    if date:
                        item_date = int(get_item_date(item_id))
                        if url not in urls:
                            urls[url] = {'first_seen': item_date, 'last_seen': item_date}
                        else: # update first_seen / last_seen
                            if item_date < urls[url]['first_seen']:
                                urls[url]['first_seen'] = item_date
                            if item_date > urls[url]['last_seen']:
                                urls[url]['last_seen'] = item_date
                    else:
                        urls.add(url)
        return urls

    def get_misp_object(self, epoch=None):
        # create domain-ip obj
        obj_attrs = []
        obj = MISPObject('domain-crawled', standalone=True)
        obj.first_seen = self.get_first_seen()
        obj.last_seen = self.get_last_check()

        obj_attrs.append(obj.add_attribute('domain', value=self.id))
        urls = self.get_all_urls(date=True, epoch=epoch)
        for url in urls:
            attribute = obj.add_attribute('url', value=url)
            attribute.first_seen = str(urls[url]['first_seen'])
            attribute.last_seen = str(urls[url]['last_seen'])
            obj_attrs.append(attribute)
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    # TODO ADD MISP Event Export
    # TODO DOWN DOMAIN
    def get_download_zip(self, epoch=None):
        hars_dir = ConfigLoader.get_hars_dir()
        items_dir = ConfigLoader.get_items_dir()
        screenshots_dir = ConfigLoader.get_screenshots_dir()
        items = self.get_crawled_items_by_epoch(epoch=epoch)
        if not items:
            return None
        map_file = 'ITEM ID    :    URL'
        # zip buffer
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "a") as zf:
            for item_id in items:
                url = get_item_url(item_id)
                basename = os.path.basename(item_id)
                # Item
                _write_in_zip_buffer(zf, os.path.join(items_dir, item_id), f'{basename}.gz')
                map_file = map_file + f'\n{item_id}    :    {url}'
                # HAR
                har = get_item_har(item_id)
                if har:
                    print(har)
                    _write_in_zip_buffer(zf, os.path.join(hars_dir, har), f'{basename}.json')
                # Screenshot
                screenshot = self._get_external_correlation('item', '', item_id, 'screenshot')
                if screenshot:
                    screenshot = screenshot['screenshot'].pop()[1:]
                    screenshot = os.path.join(screenshot[0:2], screenshot[2:4], screenshot[4:6], screenshot[6:8],
                                              screenshot[8:10], screenshot[10:12], screenshot[12:])
                    _write_in_zip_buffer(zf, os.path.join(screenshots_dir, f'{screenshot}.png'), f'{basename}.png')

            zf.writestr('_URL_MAP_', BytesIO(map_file.encode()).getvalue())
            misp_object = self.get_misp_object().to_json().encode()
            zf.writestr('misp.json', BytesIO(misp_object).getvalue())
        zip_buffer.seek(0)
        return zip_buffer

    def add_language(self, language):
        r_crawler.sadd('all_domains_languages', language)
        r_crawler.sadd(f'all_domains_languages:{self.domain_type}', language)
        r_crawler.sadd(f'language:domains:{self.domain_type}:{language}', self.id)
        r_crawler.sadd(f'domain:language:{self.id}', language)

    ############################################################################
    ############################################################################


    def create(self, first_seen, last_check, status, tags, languages):


        r_crawler.hset(f'domain:meta:{self.id}', 'first_seen', first_seen)
        r_crawler.hset(f'domain:meta:{self.id}', 'last_check', last_check)

        for language in languages:
            self.add_language(language)

    # add root_item to history
    # if domain down -> root_item = epoch
    def _add_history_root_item(self, root_item, epoch):
        # Create/Update crawler history
        r_crawler.zadd(f'domain:history:{self.id}', {root_item: epoch})

    # if domain down -> root_item = epoch
    def add_history(self, epoch, root_item=None, date=None):
        if not date:
            date = time.strftime('%Y%m%d', time.gmtime(epoch))
        try:
            root_item = int(root_item)
            status = False
        except (ValueError, TypeError):
            status = True

        data_retention_engine.update_object_date('domain', self.domain_type, date)
        # UP
        if status:
            r_crawler.srem(f'full_{self.domain_type}_down', self.id)
            r_crawler.sadd(f'full_{self.domain_type}_up', self.id)
            r_crawler.sadd(f'{self.domain_type}_up:{date}', self.id) # # TODO:  -> store first day
            r_crawler.sadd(f'month_{self.domain_type}_up:{date[0:6]}', self.id) # # TODO:  -> store first month
            self._add_history_root_item(root_item, epoch)
        else:
            r_crawler.sadd(f'{self.domain_type}_down:{date}', self.id)
            if self.was_up():
                self._add_history_root_item(epoch, epoch)
            else:
                r_crawler.sadd(f'full_{self.domain_type}_down', self.id)

    # TODO RENAME PASTE_METADATA
    def add_crawled_item(self, url, item_id, item_father):
        r_metadata.hset(f'paste_metadata:{item_id}', 'father', item_father)
        r_metadata.hset(f'paste_metadata:{item_id}', 'domain', self.id) # FIXME REMOVE ME -> extract for real link ?????????
        r_metadata.hset(f'paste_metadata:{item_id}', 'real_link', url)
        # add this item_id to his father
        r_metadata.sadd(f'paste_children:{item_father}', item_id)


############################################################################
# In memory zipfile
def _write_in_zip_buffer(zf, path, filename):
    with open(path, "rb") as f:
        content = f.read()
        zf.writestr( filename, BytesIO(content).getvalue())

############################################################################

def get_all_domains_types():
    return ['onion', 'web']  # i2p

def get_all_domains_languages():
    return r_crawler.smembers('all_domains_languages')

def get_domains_up_by_type(domain_type):
    return r_crawler.smembers(f'full_{domain_type}_up')

def get_domains_down_by_type(domain_type):
    return r_crawler.smembers(f'full_{domain_type}_down')

def get_domains_up_by_date(date, domain_type):
    return r_crawler.smembers(f'{domain_type}_up:{date}')

def get_domains_down_by_date(date, domain_type):
    return r_crawler.smembers(f'{domain_type}_down:{date}')

def get_domains_by_daterange(date_from, date_to, domain_type, up=True, down=False):
    date_domains = {}
    for date in Date.substract_date(date_from, date_to):
        domains = []
        if up:
            domains.extend(get_domains_up_by_date(date, domain_type))
        if down:
            domains.extend(get_domains_down_by_date(date, domain_type))
        if domains:
            date_domains[date] = list(domains)
    return date_domains

def get_domains_meta(domains):
    metas = []
    for domain in domains:
        dom = Domain(domain)
        metas.append(dom.get_meta())
    return metas

################################################################################
################################################################################

if __name__ == '__main__':
    dom = Domain('')
    dom.get_download_zip()
