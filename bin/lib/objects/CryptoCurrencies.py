#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

# sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

from abstract_object import AbstractObject

config_loader = ConfigLoader.ConfigLoader()

config_loader = None


################################################################################
################################################################################
################################################################################

class CryptoCurrency(AbstractObject):
    """
    AIL CryptoCurrency Object. (strings)
    """

    def __init__(self, id, subtype):
        super(CryptoCurrency, self).__init__('cryptocurrency', id, subtype=subtype)

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
        if self.subtype == 'bitcoin':
            style = 'fab'
            icon = '\uf15a'
        elif self.subtype == 'monero':
            style = 'fab'
            icon = '\uf3d0'
        elif self.subtype == 'ethereum':
            style = 'fab'
            icon = '\uf42e'
        else:
            style = 'fas'
            icon = '\uf51e'
        return {'style': style, 'icon': icon, 'color': '#DDCC77', 'radius':5}

    ############################################################################
    ############################################################################
    ############################################################################

    def exist_correlation(self):
        pass

    ############################################################################
    ############################################################################



#if __name__ == '__main__':
