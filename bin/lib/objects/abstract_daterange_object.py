# -*-coding:UTF-8 -*
"""
Base Class for AIL Objects
"""

##################################
# Import External packages
##################################
import os
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

    def get_first_seen(self, r_int=False):
        first_seen = r_object.hget(f'meta:{self.type}:{self.id}', 'first_seen')
        if r_int:
            if first_seen:
                return int(first_seen)
            else:
                return 99999999
        else:
            return first_seen

    def get_last_seen(self, r_int=False):
        last_seen = r_object.hget(f'meta:{self.type}:{self.id}', 'last_seen')
        if r_int:
            if last_seen:
                return int(last_seen)
            else:
                return 0
        else:
            return last_seen

    def get_nb_seen(self):
        return self.get_nb_correlation('item')

    def get_nb_seen_by_date(self, date):
        nb = r_object.zscore(f'{self.type}:date:{date}', self.id)
        if nb is None:
            return 0
        else:
            return int(nb)

    def _get_meta(self, options=[]):
        meta_dict = {'first_seen': self.get_first_seen(),
                     'last_seen': self.get_last_seen(),
                     'nb_seen': self.get_nb_seen()}
        if 'sparkline' in options:
            meta_dict['sparkline'] = self.get_sparkline()
        return meta_dict

    def set_first_seen(self, first_seen):
        r_object.hset(f'meta:{self.type}:{self.id}', 'first_seen', first_seen)

    def set_last_seen(self, last_seen):
        r_object.hset(f'meta:{self.type}:{self.id}', 'last_seen', last_seen)

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

    def get_content(self):
        return self.id

    def _add_create(self):
        r_object.sadd(f'{self.type}:all', self.id)

    # TODO don't increase nb if same hash in item with different encoding
    # if hash already in item
    def _add(self, date, item_id):
        if not self.exists():
            self._add_create()
            self.set_first_seen(date)
            self.set_last_seen(date)
        else:
            self.update_daterange(date)
        update_obj_date(date, self.type)

        # NB Object seen by day
        if not self.is_correlated('item', '', item_id):  # if decoded not already in object
            r_object.zincrby(f'{self.type}:date:{date}', 1, self.id)

        # Correlations
        self.add_correlation('item', '', item_id)
        if is_crawled(item_id):  # Domain
            domain = get_item_domain(item_id)
            self.add_correlation('domain', '', domain)

    # TODO:ADD objects + Stats
    def _create(self, first_seen, last_seen):
        self.set_first_seen(first_seen)
        self.set_last_seen(last_seen)
        r_object.sadd(f'{self.type}:all', self.id)

    # TODO
    def _delete(self):
        pass
