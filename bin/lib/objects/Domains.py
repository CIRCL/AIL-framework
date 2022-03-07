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

class Domain(AbstractObject):
    """
    AIL Decoded Object. (strings)
    """

    def __init__(self, id):
        super(Domain, self).__init__('domain', id)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    def get_domain_type(self):
        if str(self.id).endswith('.onion'):
            return 'onion'
        else:
            return 'regular'

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('crawler_splash.showDomain', domain=self.id)
        else:
            url = f'{baseurl}/crawlers/showDomain?domain={self.id}'
        return url

    def get_svg_icon(self):
        color = '#3DA760'
        if self.get_domain_type() == 'onion':
            style = 'fas'
            icon = '\uf06e'
        else:
            style = 'fab'
            icon = '\uf13b'
        return {'style': style, 'icon': icon, 'color':color, 'radius':5}

    ############################################################################
    ############################################################################
    ############################################################################

    def exist_correlation(self):
        pass

    ############################################################################
    ############################################################################



#if __name__ == '__main__':
