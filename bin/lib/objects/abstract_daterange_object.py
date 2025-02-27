# -*-coding:UTF-8 -*
"""
Base Class for AIL Objects
"""

##################################
# Import External packages
##################################
import os
import re
import sys
from abc import abstractmethod, ABC

# from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects.abstract_object import AbstractObject
from lib.ConfigLoader import ConfigLoader
from lib.item_basic import is_crawled, get_item_domain
from lib.data_retention_engine import update_obj_date

from packages import Date

# LOAD CONFIG
config_loader = ConfigLoader()
r_object = config_loader.get_db_conn("Kvrocks_Objects")
config_loader = None

class AbstractDaterangeObject(AbstractObject, ABC):
    """
    Abstract Subtype Object
    """

    def __init__(self, obj_type, id):
        """ Abstract for all the AIL object

        :param obj_type: object type (item, ...)
        :param id: Object ID
        """
        super().__init__(obj_type, id)

    def exists(self):
        return r_object.exists(f'meta:{self.type}:{self.id}')

    def _get_field(self, field): # TODO remove me (NEW in abstract)
        return r_object.hget(f'meta:{self.type}:{self.id}', field)

    def _set_field(self, field, value): # TODO remove me (NEW in abstract)
        return r_object.hset(f'meta:{self.type}:{self.id}', field, value)

    def get_first_seen(self, r_int=False):
        first_seen = self._get_field('first_seen')
        if r_int:
            if first_seen:
                return int(first_seen)
            else:
                return 99999999
        else:
            return first_seen

    def get_last_seen(self, r_int=False):
        last_seen = self._get_field('last_seen')
        if r_int:
            if last_seen:
                return int(last_seen)
            else:
                return 0
        else:
            return last_seen

    def get_nb_seen(self): # TODO REPLACE ME -> correlation image chats
        return self.get_nb_correlation('item') + self.get_nb_correlation('message')

    def get_nb_seen_by_date(self, date):
        nb = r_object.zscore(f'{self.type}:date:{date}', self.id)
        if nb is None:
            return 0
        else:
            return int(nb)

    def _get_meta(self, options=[]):
        meta_dict = self.get_default_meta(options=options)
        meta_dict['first_seen'] = self.get_first_seen()
        meta_dict['last_seen'] = self.get_last_seen()
        meta_dict['nb_seen'] = self.get_nb_seen()
        if 'sparkline' in options:
            meta_dict['sparkline'] = self.get_sparkline()
        if 'last_full_date' in options:
            meta_dict['last_full_date'] = meta_dict['last_seen']
        return meta_dict

    def set_first_seen(self, first_seen):
        self._set_field('first_seen', first_seen)

    def set_last_seen(self, last_seen):
        self._set_field('last_seen', last_seen)

    def update_daterange(self, date):
        date = int(date)
        # obj don't exit
        if not self.exists():
            self.set_first_seen(date)
            self.set_last_seen(date)
        else:
            first_seen = self.get_first_seen(r_int=True)
            last_seen = self.get_last_seen(r_int=True)
            if date < first_seen:
                self.set_first_seen(date)
            if date > last_seen:
                self.set_last_seen(date)

    def get_sparkline(self):
        sparkline = []
        for date in Date.get_previous_date_list(6):
            sparkline.append(self.get_nb_seen_by_date(date))
        return sparkline

    def get_content(self, r_type='str'):
        if r_type == 'str':
            return self.id
        elif r_type == 'bytes':
            return self.id.encode()

    def _add_create(self):
        r_object.sadd(f'{self.type}:all', self.id)

    def _copy_from(self, obj_type, obj_id):
        first_seen = r_object.hget(f'meta:{obj_type}:{obj_id}', 'first_seen')
        last_seen = r_object.hget(f'meta:{obj_type}:{obj_id}', 'last_seen')
        if first_seen and last_seen:
            for date in Date.get_daterange(first_seen, last_seen):
                nb = r_object.zscore(f'{obj_type}:date:{date}', obj_id)
                if nb:
                    r_object.zincrby(f'{self.type}:date:{date}', nb, self.id)
            update_obj_date(first_seen, self.type)
            update_obj_date(last_seen, self.type)
            self._add_create()
            self.set_first_seen(first_seen)
            self.set_last_seen(last_seen)

    def _add(self, date, obj): # TODO OBJ=None
        if not self.exists():
            self._add_create()
            self.set_first_seen(date)
            self.set_last_seen(date)
        else:
            self.update_daterange(date)
        update_obj_date(date, self.type)

        r_object.zincrby(f'{self.type}:date:{date}', 1, self.id)

        if obj:
            # Correlations
            self.add_correlation(obj.type, obj.get_subtype(r_str=True), obj.get_id())

            if obj.type == 'item':
                item_id = obj.get_id()
                # domain
                if is_crawled(item_id):
                    domain = get_item_domain(item_id)
                    self.add_correlation('domain', '', domain)
            elif obj.type == 'message':
                chat_subtype = obj.get_chat_instance()
                chat_id = obj.get_chat_id()
                self.add_correlation('chat', chat_subtype, chat_id)

    def add(self, date, obj):
        self._add(date, obj)

    # TODO:ADD objects + Stats
    def _create(self, first_seen=None, last_seen=None):
        if first_seen:
            self.set_first_seen(first_seen)
        if last_seen:
            self.set_last_seen(last_seen)
        r_object.sadd(f'{self.type}:all', self.id)

    # TODO
    def _delete(self):
        pass


class AbstractDaterangeObjects(ABC):
    """
    Abstract Daterange Objects
    """

    def __init__(self, obj_type, obj_class):
        """ Abstract for Daterange Objects

        :param obj_type: object type (item, ...)
        :param obj_class: object python class (Item, ...)
        """
        self.type = obj_type
        self.obj_class = obj_class

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_icon(self):
        pass

    @abstractmethod
    def get_link(self, flask_context=False):
        pass

    ################################################
    ################################################

    def get_ids(self):
        return r_object.smembers(f'{self.type}:all')

    def get_iterator(self):
        for obj_id in self.get_ids():
            yield self.obj_class(obj_id)

    ################################################
    ################################################

    # def get_ids_iterator(self):
    #     return r_object.sscan_iter(r_object, f'{self.type}:all')

    def get_by_date(self, date):
        return r_object.zrange(f'{self.type}:date:{date}', 0, -1)

    def get_nb_by_date(self, date):
        return r_object.zcard(f'{self.type}:date:{date}')

    def get_by_daterange(self, date_from, date_to):
        obj_ids = set()
        for date in Date.substract_date(date_from, date_to):
            obj_ids = obj_ids | set(self.get_by_date(date))
        return obj_ids

    def get_metas(self, obj_ids, options=set()):
        dict_obj = {}
        for obj_id in obj_ids:
            obj = self.obj_class(obj_id)
            dict_obj[obj_id] = obj.get_meta(options=options)
        return dict_obj

    @abstractmethod
    def sanitize_id_to_search(self, id_to_search):
        return id_to_search

    def search_by_id(self, name_to_search, r_pos=False, case_sensitive=True):
        objs = {}
        if case_sensitive:
            flags = 0
        else:
            flags = re.IGNORECASE
        # for subtype in subtypes:
        r_name = self.sanitize_id_to_search(name_to_search)
        if not name_to_search or isinstance(r_name, dict):
            return objs
        r_name = re.compile(r_name, flags=flags)
        for obj_id in self.get_ids():   # TODO REPLACE ME WITH AN ITERATOR
            res = re.search(r_name, obj_id)
            if res:
                objs[obj_id] = {}
                if r_pos:
                    objs[obj_id]['hl-start'] = res.start()
                    objs[obj_id]['hl-end'] = res.end()
        return objs

    def sanitize_content_to_search(self, content_to_search):
        return content_to_search

    def get_contents_ids(self):
        titles = {}
        for obj_id in self.get_ids():
            obj = self.obj_class(obj_id)
            content = obj.get_content()
            if content not in titles:
                titles[content] = []
            for domain in obj.get_correlation('domain').get('domain', []):
                titles[content].append(domain[1:])
        return titles

    def search_by_content(self, content_to_search, r_pos=False, case_sensitive=True):
        objs = {}
        if case_sensitive:
            flags = 0
        else:
            flags = re.IGNORECASE
        # for subtype in subtypes:
        r_search = self.sanitize_content_to_search(content_to_search)
        if not r_search or isinstance(r_search, dict):
            return objs
        r_search = re.compile(r_search, flags=flags)
        for obj_id in self.get_ids():  # TODO REPLACE ME WITH AN ITERATOR
            obj = self.obj_class(obj_id)
            content = obj.get_content()
            res = re.search(r_search, content)
            if res:
                objs[obj_id] = {}
                if r_pos:  # TODO ADD CONTENT ????
                    objs[obj_id]['hl-start'] = res.start()
                    objs[obj_id]['hl-end'] = res.end()
                    objs[obj_id]['content'] = content
        return objs

    def api_get_chart_nb_by_daterange(self, date_from, date_to):
        date_type = []
        for date in Date.substract_date(date_from, date_to):
            d = {'date': f'{date[0:4]}-{date[4:6]}-{date[6:8]}',
                 self.type: self.get_nb_by_date(date)}
            date_type.append(d)
        return date_type

    def api_get_meta_by_daterange(self, date_from, date_to):
        date = Date.sanitise_date_range(date_from, date_to)
        return self.get_metas(self.get_by_daterange(date['date_from'], date['date_to']), options={'sparkline', 'uuid'})
