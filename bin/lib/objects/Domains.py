#!/usr/bin/env python3
# -*-coding:UTF-8 -*
import itertools
import json
import os
import re
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

from lib.ail_core import paginate_iterator
from lib.item_basic import get_item_children, get_item_date, get_item_url, get_item_domain, get_item_har
from lib.data_retention_engine import update_obj_date

from packages import Date

config_loader = ConfigLoader.ConfigLoader()
r_crawler = config_loader.get_db_conn("Kvrocks_Crawler")

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

    def get_content(self):
        return self.id

    def get_last_origin(self, obj=False):
        origin = {'item': r_crawler.hget(f'domain:meta:{self.id}', 'last_origin')}
        if obj and origin['item']:
            if origin['item'] != 'manual' and origin['item'] != 'auto':
                item_id = origin['item']
                origin['domain'] = get_item_domain(item_id)
                origin['url'] = get_item_url(item_id)
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

    # TODO ADD RANDOM OPTION
    def get_screenshot(self):
        last_item = self.get_last_item_root()
        if last_item:
            screenshot = self.get_obj_correlations('item', '', last_item, ['screenshot']).get('screenshot')
            if screenshot:
                return screenshot.pop()[1:]

    def get_languages(self):
        return r_crawler.smembers(f'domain:language:{self.id}')

    def get_meta_keys(self):
        return ['type', 'first_seen', 'last_check', 'last_origin', 'ports', 'status', 'tags', 'languages']

    # options: set of optional meta fields
    def get_meta(self, options=set()):
        meta = {'type': self.domain_type,  # TODO RENAME ME -> Fix template
                'id': self.id,
                'domain': self.id, # TODO Remove me -> Fix templates
                'first_seen': self.get_first_seen(),
                'last_check': self.get_last_check(),
                'tags': self.get_tags(r_list=True),
                'status': self.is_up()
                }
        if 'last_origin' in options:
            meta['last_origin'] = self.get_last_origin(obj=True)
        if 'languages' in options:
            meta['languages'] = self.get_languages()
        if 'screenshot' in options:
            meta['screenshot'] = self.get_screenshot()
        if 'tags_safe' in options:
            meta['is_tags_safe'] = self.is_tags_safe(meta['tags'])
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
        else:
            return []


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
        first_seen = self.get_first_seen()
        last_seen = self.get_last_check()
        if first_seen:
            obj.first_seen = first_seen
        if last_seen:
            obj.last_seen = last_seen
        if not first_seen or not last_seen:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={first_seen}, last={last_seen}')

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
                    _write_in_zip_buffer(zf, os.path.join(hars_dir, har), f'{basename}.json.gz')
                # Screenshot
                screenshot = self.get_obj_correlations('item', '', item_id, ['screenshot'])
                if screenshot and screenshot['screenshot']:
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

    def get_vanity(self, len_vanity=4):
        return get_domain_vanity(self.id, len_vanity=len_vanity)

    def update_vanity_cluster(self):
        if self.get_domain_type() == 'onion':
            update_vanity_cluster(self.id)

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
        if not root_item:
            root_item = int(epoch)
            status = False
        else:
            try:
                root_item = int(root_item)
                status = False
            except (ValueError, TypeError):
                status = True

        update_obj_date(date, 'domain', self.domain_type)
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

############################################################################
# In memory zipfile
def _write_in_zip_buffer(zf, path, filename):
    with open(path, "rb") as f:
        content = f.read()
        zf.writestr( filename, BytesIO(content).getvalue())

############################################################################

def get_all_domains_types():
    return ['onion', 'web']  # i2p

def sanitize_domains_types(types):
    domains_types = get_all_domains_types()
    if not types:
        return domains_types
    types_domains = []
    for type_d in types:
        if type_d in domains_types:
            types_domains.append(type_d)
    if not types_domains:
        return domains_types
    return types_domains


def get_all_domains_languages():
    return r_crawler.smembers('all_domains_languages')

# TODO sanitize type
# TODO sanitize languages
def get_domains_by_languages(languages, domain_types):
    if len(languages) == 1:
        if len(domain_types) == 1:
            return r_crawler.smembers(f'language:domains:{domain_types[0]}:{languages[0]}')
        else:
            l_keys = []
        for domain_type in domain_types:
            l_keys.append(f'language:domains:{domain_type}:{languages[0]}')
        return r_crawler.sunion(l_keys[0], *l_keys[1:])
    else:
        domains = []
        for domain_type in domain_types:
            l_keys = []
            for language in languages:
                l_keys.append(f'language:domains:{domain_type}:{language}')
            res = r_crawler.sinter(l_keys[0], *l_keys[1:])
            if res:
                domains.append(res)
        return list(itertools.chain.from_iterable(domains))

def api_get_domains_by_languages(domains_types, languages, meta=False, page=1):
    domains = sorted(get_domains_by_languages(languages, domains_types))
    domains = paginate_iterator(domains, nb_obj=28, page=page)
    if not meta:
        return domains
    else:
        metas = []
        for dom in domains['list_elem']:
            domain = Domain(dom)
            domain_meta = domain.get_meta(options={'languages', 'screenshot', 'tags_safe'})
            metas.append(domain_meta)
        domains['list_elem'] = metas
        return domains


def get_domains_up_by_type(domain_type):
    return r_crawler.smembers(f'full_{domain_type}_up')

def get_domains_down_by_type(domain_type):
    return r_crawler.smembers(f'full_{domain_type}_down')

def get_domains_up_by_date(date, domain_type):
    return r_crawler.smembers(f'{domain_type}_up:{date}')

def get_domains_down_by_date(date, domain_type):
    return r_crawler.smembers(f'{domain_type}_down:{date}')

def get_domains_by_daterange(date_from, date_to, domain_type, up=True, down=False):
    domains = []
    for date in Date.substract_date(date_from, date_to):
        if up:
            domains.extend(get_domains_up_by_date(date, domain_type))
        if down:
            domains.extend(get_domains_down_by_date(date, domain_type))
    return domains

def get_domains_dates_by_daterange(date_from, date_to, domain_types, up=True, down=False):
    if not domain_types:
        domain_types = get_all_domains_types()
    date_domains = {}
    for date in Date.substract_date(date_from, date_to):
        domains = []
        for domain_type in domain_types:
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

# TODO ADD TAGS FILTER
def get_domains_up_by_filers(domain_types, date_from=None, date_to=None, tags=[], nb_obj=28, page=1):
    if not domain_types:
        domain_types = ['onion', 'web']
    if not tags:
        domains = []
        if not date_from and not date_to:
            for domain_type in domain_types:
                domains[0:0] = get_domains_up_by_type(domain_type)
        else:
            for domain_type in domain_types:
                domains[0:0] = get_domains_by_daterange(date_from, date_to, domain_type)
        domains = sorted(domains)
        domains = paginate_iterator(domains, nb_obj=nb_obj, page=page)
        meta = []
        for dom in domains['list_elem']:
            domain = Domain(dom)
            meta.append(domain.get_meta(options={'languages', 'screenshot', 'tags_safe'}))
        domains['list_elem'] = meta
        domains['domain_types'] = domain_types
        if date_from:
            domains['date_from'] = date_from
        if date_to:
            domains['date_to'] = date_to
        return domains
    else:
        return None

def sanitize_domain_name_to_search(name_to_search, domain_type):
    if not name_to_search:
        return ""
    if domain_type == 'onion':
        r_name = r'[a-z0-9\.]+'
    else:
        r_name = r'[a-zA-Z0-9-_\.]+'
    # invalid domain name
    if not re.fullmatch(r_name, name_to_search):
        return ""
    return name_to_search.replace('.', '\.')

def search_domain_by_name(name_to_search, domain_types, r_pos=False):
    domains = {}
    for domain_type in domain_types:
        r_name = sanitize_domain_name_to_search(name_to_search, domain_type)
        if not r_name:
            break
        r_name = re.compile(r_name)
        for domain in get_domains_up_by_type(domain_type):
            res = re.search(r_name, domain)
            if res:
                domains[domain] = {}
                if r_pos:
                    domains[domain]['hl-start'] = res.start()
                    domains[domain]['hl-end'] = res.end()
    return domains

def api_search_domains_by_name(name_to_search, domain_types, meta=False, page=1):
    domain_types = sanitize_domains_types(domain_types)
    domains_dict = search_domain_by_name(name_to_search, domain_types, r_pos=True)
    domains = sorted(domains_dict.keys())
    domains = paginate_iterator(domains, nb_obj=28, page=page)
    if not meta:
        return domains
    else:
        metas = []
        for dom in domains['list_elem']:
            domain = Domain(dom)
            domain_meta = domain.get_meta(options={'languages', 'screenshot', 'tags_safe'})
            domain_meta = {**domains_dict[dom], **domain_meta}
            metas.append(domain_meta)
        domains['list_elem'] = metas
        domains['search'] = name_to_search
        return domains

################################################################################
################################################################################

#### Vanity Explorer ####

# TODO ADD ME IN OBJ CLASS
def get_domain_vanity(domain, len_vanity=4):
    return domain[:len_vanity]

def get_vanity_clusters(nb_min=4):
    return r_crawler.zrange('vanity:onion:4', nb_min, '+inf', byscore=True, withscores=True)

def get_vanity_domains(vanity, len_vanity=4, meta=False):
    if len_vanity == 4:
        domains = r_crawler.smembers(f'vanity:{int(len_vanity)}:{vanity}')
    else:
        domains = []
        for domain in r_crawler.smembers(f'vanity:4:{vanity[:4]}'):
            dom_vanity = get_domain_vanity(domain, len_vanity=len_vanity)
            if vanity == dom_vanity:
                domains.append(domain)
    if meta:
        metas = []
        for domain in domains:
            metas.append(Domain(domain).get_meta(options={'languages', 'screenshot', 'tags_safe'}))
        return metas
    else:
        return domains

def get_vanity_cluster(vanity, len_vanity=4, nb_min=4):
    if len_vanity == 4:
        return get_vanity_clusters(nb_min=nb_min)
    else:
        clusters = {}
        for domain in get_vanity_domains(vanity[:4], len_vanity=4):
            new_vanity = get_domain_vanity(domain, len_vanity=len_vanity)
            if new_vanity not in clusters:
                clusters[new_vanity] = 0
            clusters[new_vanity] += 1
        to_remove = []
        for new_vanity in clusters:
            if clusters[new_vanity] < nb_min:
                to_remove.append(new_vanity)
        for new_vanity in to_remove:
            del clusters[new_vanity]
        return clusters

def get_vanity_nb_domains(vanity, len_vanity=4):
    return r_crawler.scard(f'vanity:{int(len_vanity)}:{vanity}')

# TODO BUILD DICTIONARY
def update_vanity_cluster(domain):
    vanity = get_domain_vanity(domain, len_vanity=4)
    add = r_crawler.sadd(f'vanity:4:{vanity}', domain)
    if add == 1:
        r_crawler.zadd('vanity:onion:4', {vanity: 1}, incr=True)

def _rebuild_vanity_clusters():
    for vanity in r_crawler.zrange('vanity:onion:4', 0, -1):
        r_crawler.delete(f'vanity:4:{vanity}')
    r_crawler.delete('vanity:onion:4')
    for domain in get_domains_up_by_type('onion'):
        update_vanity_cluster(domain)

def cluster_onion_domain_vanity(len_vanity=4):
    domains = {}
    occurrences = {}
    for domain in get_domains_up_by_type('onion'):
        start = domain[:len_vanity]
        if start not in domains:
            domains[start] = []
            occurrences[start] = 0
        domains[start].append(domain)
        occurrences[start] += 1

    # print(json.dumps(domains))
    res = dict(sorted(occurrences.items(), key=lambda item: item[1], reverse=True))
    print(json.dumps(res))

class Domains:
    def __init__(self):
        self.type = 'message'
        self.obj_class = Domain

    def get_name(self):
        return 'Domains'

    def get_icon(self):
        return {'fas': 'fas', 'icon': 'spider'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('crawler_splash.crawlers_dashboard')
        else:
            url = f'{baseurl}/crawlers/dashboard'
        return url

    # def get_by_date(self, date):
    #     pass

    def get_nb_by_date(self, date):
        nb = 0
        for domain_type in get_all_domains_types():
            nb += r_crawler.scard(f'{domain_type}_up:{date}')
        return nb

if __name__ == '__main__':
    _rebuild_vanity_clusters()
