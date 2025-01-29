#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from flask import url_for
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects

config_loader = ConfigLoader()
r_object = config_loader.get_db_conn("Kvrocks_Objects")
config_loader = None


class FileName(AbstractDaterangeObject):
    """
    AIL FileName Object. (strings)
    """

    # ID = SHA256
    def __init__(self, name):
        super().__init__('file-name', name)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'far', 'icon': '\uf15b', 'color': '#36F5D5', 'radius': 5}

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('file')

        # obj_attrs.append(obj.add_attribute('sha256', value=self.id))
        # obj_attrs.append(obj.add_attribute('attachment', value=self.id, data=self.get_file_content()))
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['tags'] = self.get_tags(r_list=True)
        if 'tags_safe' in options:
            meta['tags_safe'] = self.is_tags_safe(meta['tags'])
        return meta

    def create(self): # create ALL SET ??????
        pass

    def add_reference(self, date, src_ail_object, file_obj=None):
        self.add(date, src_ail_object)
        if file_obj:
            self.add_correlation(file_obj.type, file_obj.get_subtype(r_str=True), file_obj.get_id())

# TODO USE ZSET FOR ALL OBJS IDS ??????

class FilesNames(AbstractDaterangeObjects):
    """
        CookieName Objects
    """
    def __init__(self):
        super().__init__('file-name', FileName)

    def get_name(self):
        return 'File-Names'

    def get_icon(self):
        return {'fa': 'far', 'icon': 'file'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_file_name.objects_files_names')
        else:
            url = f'{baseurl}/objects/file-names'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search

    # TODO sanitize file name
    def create(self, name, date, src_ail_object, file_obj=None, limit=500, force=False):
        if 0 < len(name) <= limit or force or limit < 0:
            file_name = self.obj_class(name)
            # if not file_name.exists():
            #     file_name.create()
            file_name.add_reference(date, src_ail_object, file_obj=file_obj)
            return file_name

# if __name__ == '__main__':
#     name_to_search = '29ba'
#     print(search_screenshots_by_name(name_to_search))
