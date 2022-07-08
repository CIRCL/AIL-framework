#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from flask import url_for
from io import BytesIO

sys.path.append(os.environ['AIL_BIN'])
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_object import AbstractObject

config_loader = ConfigLoader()
r_metadata = config_loader.get_redis_conn("ARDB_Metadata")
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
        return r_metadata.hget(f'metadata_hash:{self.get_sha1()}', 'estimated_type')

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

    '''
    Return the estimed type of a given decoded item.

    :param sha1_string: sha1_string
    '''
    def get_estimated_type(self):
        return r_metadata.hget(f'metadata_hash:{self.id}', 'estimated_type')

    def get_rel_path(self, mimetype=None):
        if not mimetype:
            mimetype = self.get_estimated_type()
        return os.path.join(HASH_DIR, mimetype, self.id[0:2], self.id)

    def get_filepath(self, mimetype=None):
        return os.path.join(os.environ['AIL_HOME'], self.get_rel_path(mimetype=mimetype))

    def get_file_content(self, mimetype=None):
        filepath = self.get_filepath(mimetype=mimetype)
        with open(filepath, 'rb') as f:
            file_content = BytesIO(f.read())
        return file_content

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('file')
        obj.first_seen = self.get_first_seen()
        obj.last_seen = self.get_last_seen()

        obj_attrs.append( obj.add_attribute('sha1', value=self.id) )
        obj_attrs.append( obj.add_attribute('mimetype', value=self.get_estimated_type()) )
        obj_attrs.append( obj.add_attribute('malware-sample', value=self.id, data=self.get_file_content()) )
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    ############################################################################
    ############################################################################
    ############################################################################

    def exist_correlation(self):
        pass

    def create(self, content, date):




        Decoded.save_decoded_file_content(sha1_string, decoded_file, item_date, mimetype=mimetype)
        ####correlation Decoded.save_item_relationship(sha1_string, item_id)
        Decoded.create_decoder_matadata(sha1_string, item_id, decoder_name)



    ############################################################################
    ############################################################################



#if __name__ == '__main__':
