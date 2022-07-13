# -*-coding:UTF-8 -*
"""
Base Class for AIL Objects
"""

##################################
# Import External packages
##################################
import os
import sys
from abc import abstractmethod

#from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects.abstract_object import AbstractObject
from lib.ConfigLoader import ConfigLoader

# LOAD CONFIG
config_loader = ConfigLoader()
r_metadata = config_loader.get_redis_conn("ARDB_Metadata")
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

    # # TODO: # FIXME:  REMOVE R_INT ????????????????????????????????????????????????????????????????????
    def get_first_seen(self, r_int=False):
        first_seen = r_metadata.hget(f'{self.type}_metadata_{self.subtype}:{self.id}', 'first_seen')
        if r_int:
            if first_seen:
                return int(first_seen)
            else:
                return 99999999
        else:
            return first_seen

    # # TODO: # FIXME:  REMOVE R_INT ????????????????????????????????????????????????????????????????????
    def get_last_seen(self, r_int=False):
        last_seen = r_metadata.hget(f'{self.type}_metadata_{self.subtype}:{self.id}', 'last_seen')
        if r_int:
            if last_seen:
                return int(last_seen)
            else:
                return 0
        else:
            return last_seen

    def get_nb_seen(self):
        return r_metadata.scard(f'set_{self.type}_{self.subtype}:{self.id}')

    # # TODO: CHECK RESULT
    def get_nb_seen_by_date(self, date_day):
        nb = r_metadata.hget(f'{self.type}:{self.subtype}:{date_day}', self.id)
        if nb is None:
            return 0
        else:
            return int(nb)

    def _get_meta(self):
        meta_dict = {}
        meta_dict['first_seen'] = self.get_first_seen()
        meta_dict['last_seen'] = self.get_last_seen()
        meta_dict['nb_seen'] = self.get_nb_seen()
        return meta_dict

    # def exists(self):
    #     res = r_metadata.zscore(f'{self.type}_all:{self.subtype}', self.id)
    #     if res is not None:
    #         return True
    #     else:
    #         return False

    def exists(self):
        return r_metadata.exists(f'{self.type}_metadata_{self.subtype}:{self.id}')

    def set_first_seen(self, first_seen):
        r_metadata.hset(f'{self.type}_metadata_{self.subtype}:{self.id}', 'first_seen', first_seen)

    def set_last_seen(self, last_seen):
        r_metadata.hset(f'{self.type}_metadata_{self.subtype}:{self.id}', 'last_seen', last_seen)

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

    def add(self, date, item_id):
        self.update_correlation_daterange()
        # daily
        r_metadata.hincrby(f'{self.type}:{self.subtype}:{date}', self.id, 1)
        # all type
        r_metadata.zincrby(f'{self.type}_all:{self.subtype}', self.id, 1)

        #######################################################################
        #######################################################################
        # REPLACE WITH CORRELATION ?????

        # global set
        r_serv_metadata.sadd(f'set_{self.type}_{self.subtype}:{self.id}', item_id)

        ## object_metadata
        # item
        r_serv_metadata.sadd(f'item_{self.type}_{self.subtype}:{item_id}', self.id)

        # new correlation
        #
        #       How to filter by correlation type ????
        #
        f'correlation:obj:{self.type}:{self.subtype}:{self.id}',                f'{obj_type}:{obj_subtype}:{obj_id}'
        f'correlation:obj:{self.type}:{self.subtype}:{obj_type}:{self.id}',     f'{obj_subtype}:{obj_id}'

        #
        #
        #
        #
        #
        #
        #
        #


        # # domain
        # if item_basic.is_crawled(item_id):
        #     domain = item_basic.get_item_domain(item_id)
        #     self.save_domain_correlation(domain, subtype, obj_id)

    def create(self, first_seen, last_seen):
        pass



    def _delete(self):
        pass


    ####################################
    #
    # _get_items
    # get_metadata
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
