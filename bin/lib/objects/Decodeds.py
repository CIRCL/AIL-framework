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
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
HASH_DIR = config_loader.get_config_str('Directories', 'hash')
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


################################################################################
################################################################################
################################################################################

# # TODO: COMPLETE CLASS

class Decoded(AbstractObject):
    """
    AIL Decoded Object. (strings)
    """

    def __init__(self, id):
        super(Decoded, self).__init__('decoded', id)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    def get_sha1(self):
        return self.id.split('/')[0]

    def get_file_type(self):
        return r_serv_metadata.hget(f'metadata_hash:{self.get_sha1()}', 'estimated_type')

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', object_type="decoded", correlation_id=value)
        else:
            url = f'{baseurl}/correlation/show_correlation?object_type={self.type}&correlation_id={self.id}'
        return url

    def get_svg_icon(self):
        file_type = self.get_file_type()
        if file_type == 'application':
            icon = '\uf15b'
        elif file_type == 'audio':
            icon = '\uf1c7'
        elif file_type == 'image':
            icon = '\uf1c5'
        elif file_type == 'text':
            icon = '\uf15c'
        else:
            icon = '\uf249'
        return {'style': 'fas', 'icon': icon, 'color': '#88CCEE', 'radius':5}

    ############################################################################
    ############################################################################
    ############################################################################

    def exist_correlation(self):
        pass

    ############################################################################
    ############################################################################



#if __name__ == '__main__':
