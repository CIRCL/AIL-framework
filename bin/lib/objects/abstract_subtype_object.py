# -*-coding:UTF-8 -*
"""
Base Class for AIL Objects
"""

##################################
# Import External packages
##################################
import os
import sys

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

# # TODO: ADD CORRELATION ENGINE

# # FIXME: SAVE SUBTYPE NAMES ?????

class AbstractSubtypeObject(AbstractObject):
    """
    Abstract Subtype Object
    """

    def __init__(self, obj_type, id, subtype):
        """ Abstract for all the AIL object

        :param obj_type: object type (item, ...)
        :param id: Object ID
        """
        self.id = id
        self.type = obj_type
        self.subtype = subtype

    def exists(self):
        return r_object.exists(f'meta:{self.type}:{self.subtype}:{self.id}')

    def get_first_seen(self, r_int=False):
        first_seen = r_object.hget(f'meta:{self.type}:{self.subtype}:{self.id}', 'first_seen')
        if r_int:
            if first_seen:
                return int(first_seen)
            else:
                return 99999999
        else:
            return first_seen

    def get_last_seen(self, r_int=False):
        last_seen = r_object.hget(f'meta:{self.type}:{self.subtype}:{self.id}', 'last_seen')
        if r_int:
            if last_seen:
                return int(last_seen)
            else:
                return 0
        else:
            return last_seen

    def get_nb_seen(self):
        return int(r_object.zscore(f'{self.type}_all:{self.subtype}', self.id))

    # # TODO: CHECK RESULT
    def get_nb_seen_by_date(self, date_day):
        nb = r_object.hget(f'{self.type}:{self.subtype}:{date_day}', self.id)
        if nb is None:
            return 0
        else:
            return int(nb)

    def _get_meta(self):
        meta_dict = {'first_seen': self.get_first_seen(),
                     'last_seen': self.get_last_seen(),
                     'nb_seen': self.get_nb_seen()}
        return meta_dict

    def set_first_seen(self, first_seen):
        r_object.hset(f'meta:{self.type}:{self.subtype}:{self.id}', 'first_seen', first_seen)

    def set_last_seen(self, last_seen):
        r_object.hset(f'meta:{self.type}:{self.subtype}:{self.id}', 'last_seen', last_seen)

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
#
# HANDLE Others objects ????
#
# NEW field => first record(last record)
#                   by subtype ??????

#               => data Retention + efficient search
#
#

    def add(self, date, item_id):
        self.update_daterange(date)
        update_obj_date(date, self.type, self.subtype)
        # daily
        r_object.hincrby(f'{self.type}:{self.subtype}:{date}', self.id, 1)
        # all subtypes
        r_object.zincrby(f'{self.type}_all:{self.subtype}', 1, self.id)

        #######################################################################
        #######################################################################

        # Correlations
        self.add_correlation('item', '', item_id)
        # domain
        if is_crawled(item_id):
            domain = get_item_domain(item_id)
            self.add_correlation('domain', '', domain)


    # TODO:ADD objects + Stats
    def create(self, first_seen, last_seen):
        self.set_first_seen(first_seen)
        self.set_last_seen(last_seen)


    def _delete(self):
        pass

def get_all_id(obj_type, subtype):
    return r_object.zrange(f'{obj_type}_all:{subtype}', 0, -1)
