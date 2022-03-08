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

class Username(AbstractObject):
    """
    AIL Username Object. (strings)
    """

    def __init__(self, id, subtype):
        super(Username, self).__init__('username', id, subtype=subtype)

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

    ############################################################################
    ############################################################################
    ############################################################################

    def exist_correlation(self):
        pass

    ############################################################################
    ############################################################################



#if __name__ == '__main__':
