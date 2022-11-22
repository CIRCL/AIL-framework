#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

from flask import url_for
from pymisp import MISPObject

# sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, get_all_id

config_loader = ConfigLoader()

config_loader = None


################################################################################
################################################################################
################################################################################

class Username(AbstractSubtypeObject):
    """
    AIL Username Object. (strings)
    """

    def __init__(self, id, subtype):
        super(Username, self).__init__('username', id, subtype)

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
            url = url_for('correlation.show_correlation', type=self.type, subtype=self.subtype, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&subtype={self.subtype}&id={self.id}'
        return url

    def get_svg_icon(self):
        if self.subtype == 'telegram':
            style = 'fab'
            icon = '\uf2c6'
        elif self.subtype == 'twitter':
            style = 'fab'
            icon = '\uf099'
        else:
            style = 'fas'
            icon = '\uf007'
        return {'style': style, 'icon': icon, 'color': '#4dffff', 'radius':5}

    def get_meta(self, options=set()):
        meta = self._get_meta()
        meta['id'] = self.id
        meta['subtype'] = self.subtype
        meta['tags'] = self.get_tags(r_list=True)
        return meta

    def get_misp_object(self):
        obj_attrs = []
        if self.subtype == 'telegram':
            obj = MISPObject('telegram-account', standalone=True)
            obj_attrs.append( obj.add_attribute('username', value=self.id) )

        elif self.subtype == 'twitter':
            obj = MISPObject('twitter-account', standalone=True)
            obj_attrs.append( obj.add_attribute('name', value=self.id) )

        else:
            obj = MISPObject('user-account', standalone=True)
            obj_attrs.append( obj.add_attribute('username', value=self.id) )

        obj.first_seen = self.get_first_seen()
        obj.last_seen = self.get_last_seen()
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    ############################################################################
    ############################################################################

def get_all_subtypes():
    #return ail_core.get_object_all_subtypes(self.type)
    return ['telegram', 'twitter', 'jabber']

def get_all_usernames():
    users = {}
    for subtype in get_all_subtypes():
        users[subtype] = get_all_usernames_by_subtype(subtype)
    return users

def get_all_usernames_by_subtype(subtype):
    return get_all_id('username', subtype)



if __name__ == '__main__':

    obj = Username('ninechantw', 'telegram')
    print(obj.get_misp_object().to_json())
