#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

# sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

from abstract_object import AbstractObject
from flask import url_for

config_loader = ConfigLoader.ConfigLoader()

config_loader = None


################################################################################
################################################################################
################################################################################

class Pgp(AbstractObject):
    """
    AIL Pgp Object. (strings)
    """

    def __init__(self, id, subtype):
        super(Pgp, self).__init__('pgp', id, subtype=subtype)

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
        if self.subtype == 'key':
            icon = '\uf084'
        elif self.subtype == 'name':
            icon = '\uf507'
        elif self.subtype == 'mail':
            icon = '\uf1fa'
        else:
            icon = 'times'
        return {'style': 'fas', 'icon': icon, 'color': '#44AA99', 'radius':5}

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('pgp-meta')
        obj.first_seen = self.get_first_seen()
        obj.last_seen = self.get_last_seen()

        if self.subtype=='key':
            obj_attrs.append( obj.add_attribute('key-id', value=self.id) )
        elif self.subtype=='name':
            obj_attrs.append( obj.add_attribute('user-id-name', value=self.id) )
        else: # mail
            obj_attrs.append( obj.add_attribute('user-id-email', value=self.id) )

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



#if __name__ == '__main__':
