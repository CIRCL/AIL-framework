# -*-coding:UTF-8 -*
"""
Base Class for AIL Objects
"""

##################################
# Import External packages
##################################
import os
import sys
from abc import ABC, abstractmethod

#from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from packages import Tag
from lib import Duplicate
from lib.correlations_engine import get_correlations, add_obj_correlation, delete_obj_correlation, exists_obj_correlation, is_obj_correlated
from lib.Investigations import is_object_investigated, get_obj_investigations, delete_obj_investigations
from lib.Tracker import is_obj_tracked, get_obj_all_trackers, delete_obj_trackers

# # TODO: ADD CORRELATION ENGINE

class AbstractObject(ABC):
    """
    Abstract Object
    """

    # first seen last/seen ??
    # # TODO: - tags
    #         - handle + refactor coorelations
    #         - creates others objects

    def __init__(self, obj_type, id, subtype=None):
        """ Abstract for all the AIL object

        :param obj_type: object type (item, ...)
        :param id: Object ID
        """
        self.id = id
        self.type = obj_type
        self.subtype = subtype

    def get_id(self):
        return self.id

    def get_type(self):
        return self.type

    def get_subtype(self, r_str=False):
        if not self.subtype:
            if r_str:
                return ''
        return self.subtype

    def get_default_meta(self, tags=False):
        dict_meta = {'id': self.get_id(),
                     'type': self.get_type(),
                     'subtype': self.get_subtype()}
        if tags:
            dict_meta['tags'] = self.get_tags()
        return dict_meta

    ## Tags ##
    def get_tags(self, r_set=False):
        tags = Tag.get_obj_tag(self.id)
        if r_set:
            tags = set(tags)
        return tags

    def get_duplicates(self):
        return Duplicate.get_duplicates(self.type, self.get_subtype(r_str=True), self.id)

    ## ADD TAGS ????
    #def add_tags(self):

    #- Tags -#

    ## Investigations ##
    # # TODO: unregister =====

    def is_investigated(self):
        if not self.subtype:
            is_investigated = is_object_investigated(self.id, self.type)
        else:
            is_investigated = is_object_investigated(self.id, self.type, self.subtype)
        return is_investigated

    def get_investigations(self):
        if not self.subtype:
            investigations = get_obj_investigations(self.id, self.type)
        else:
            investigations = get_obj_investigations(self.id, self.type, self.subtype)
        return investigations

    def delete_investigations(self):
        if not self.subtype:
            unregistred = delete_obj_investigations(self.id, self.type)
        else:
            unregistred = delete_obj_investigations(self.id, self.type, self.subtype)
        return unregistred

    #- Investigations -#

    ## Trackers ##

    def is_tracked(self):
        return is_obj_tracked(self.type, self.subtype, self.id)

    def get_trackers(self):
        return get_obj_all_trackers(self.type, self.subtype, self.id)

    def delete_trackers(self):
        return delete_obj_trackers(self.type, self.subtype, self.id)

    #- Investigations -#

    def _delete(self):
        # DELETE TAGS
        Tag.delete_obj_all_tags(self.id, self.type)
        # remove from tracker
        self.delete_trackers()
        # remove from investigations
        self.delete_investigations()

        # # TODO: remove from correlation

    @abstractmethod
    def delete(self):
        """
        Delete Object: used for the Data Retention
        """
        pass

    # @abstractmethod
    # def get_meta(self):
    #     """
    #     get Object metadata
    #     """
    #     pass

    @abstractmethod
    def get_link(self, flask_context=False):
        pass

    @abstractmethod
    def get_svg_icon(self):
        """
        Get object svg icon
        """
        pass

    @abstractmethod
    def get_misp_object(self):
        pass

    def get_correlations(self):
        """
        Get object correlations
        """
        return get_correlations(self.type, self.subtype, self.id)

    def add_correlation(self, type2, subtype2, id2):
        """
        Add object correlation
        """
        add_obj_correlation(self.type, self.subtype, self.id, type2, subtype2, id2)

    def exists_correlation(self, type2):
        """
        Check if an object is correlated
        """
        return exists_obj_correlation(self.type, self.subtype, self.id, type2)

    def is_correlated(self, type2, subtype2, id2):
        """
        Check if an object is correlated by another object
        """
        return is_obj_correlated(self.type, self.subtype, self.id, type2, subtype2, id2)

    def delete_correlation(self, type2, subtype2, id2):
        """
        Get object correlations
        """
        delete_obj_correlation(self.type, self.subtype, self.id, type2, subtype2, id2)


    # # TODO: get favicon
    # # TODO: get url
    # # TODO: get metadata
