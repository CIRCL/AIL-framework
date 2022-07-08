#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

from flask import url_for
from pymisp import MISPObject

# sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

from abstract_subtype_object import AbstractSubtypeObject

config_loader = ConfigLoader.ConfigLoader()

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
            url = url_for('correlation.show_correlation', object_type=self.type, type_id=self.subtype, correlation_id=self.id)
        else:
            url = f'{baseurl}/correlation/show_correlation?object_type={self.type}&type_id={self.subtype}&correlation_id={self.id}'
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
    ############################################################################

    def exist_correlation(self):
        pass

    ############################################################################
    ############################################################################



if __name__ == '__main__':

    obj = Username('ninechantw', 'telegram')
    print(obj.get_misp_object().to_json())
