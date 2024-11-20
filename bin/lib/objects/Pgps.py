#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys

from flask import url_for
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, AbstractSubtypeObjects, get_all_id, get_all_id_iterator

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


################################################################################
################################################################################
################################################################################

class Pgp(AbstractSubtypeObject):
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

    # # TODO: 
    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['subtype'] = self.subtype
        meta['tags'] = self.get_tags(r_list=True)
        return meta

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, subtype=self.subtype, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&subtype={self.subtype}&id={self.id}'
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
        return {'style': 'fas', 'icon': icon, 'color': '#44AA99', 'radius': 5}

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('pgp-meta')
        first_seen = self.get_first_seen()
        last_seen = self.get_last_seen()
        if first_seen:
            obj.first_seen = first_seen
        if last_seen:
            obj.last_seen = last_seen
        if not first_seen or not last_seen:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={first_seen}, last={last_seen}')

        if self.subtype == 'key':
            obj_attrs.append(obj.add_attribute('key-id', value=self.id))
        elif self.subtype == 'name':
            obj_attrs.append(obj.add_attribute('user-id-name', value=self.id))
        else:  # mail
            obj_attrs.append(obj.add_attribute('user-id-email', value=self.id))

        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj


class Pgps(AbstractSubtypeObjects):
    """
        Usernames Objects
    """
    def __init__(self):
        super().__init__('pgp', Pgp)

    def get_name(self):
        return 'PGP Dumps'

    def get_icon(self):
        return {'fas': 'fas', 'icon': 'key'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_subtypes.objects_dashboard_pgp')
        else:
            url = f'{baseurl}/objects/pgps'
        return url

    def sanitize_id_to_search(self, subtypes, name_to_search):
        return name_to_search

    ############################################################################
    ############################################################################

def get_all_subtypes():
    return ['key', 'mail', 'name']

def get_all_pgps():
    pgps = {}
    for subtype in get_all_subtypes():
        pgps[subtype] = get_all_pgps_by_subtype(subtype)
    return pgps

def get_all_pgps_by_subtype(subtype):
    return get_all_id('pgp', subtype)

# TODO FILTER NAME + Key + mail
def sanitize_pgp_name_to_search(name_to_search, subtype): # TODO FILTER NAME + Key + mail
    if subtype == 'key':
        pass
    elif subtype == 'name':
        pass
    elif subtype == 'mail':
        pass
    return name_to_search

def search_pgps_by_name(name_to_search, subtype, r_pos=False):
    pgps = {}
    # for subtype in subtypes:
    r_name = sanitize_pgp_name_to_search(name_to_search, subtype)
    if not name_to_search or isinstance(r_name, dict):
        # break
        return pgps
    r_name = re.compile(r_name)
    for pgp_name in get_all_pgps_by_subtype(subtype):
        res = re.search(r_name, pgp_name)
        if res:
            pgps[pgp_name] = {}
            if r_pos:
                pgps[pgp_name]['hl-start'] = res.start()
                pgps[pgp_name]['hl-end'] = res.end()
    return pgps

def get_all_pgps_objects(filters={}):
    if 'subtypes' in filters:
        subtypes = filters['subtypes']
    else:
        subtypes = get_all_subtypes()
    for subtype in subtypes:
        for z_tuple in get_all_id_iterator('pgp', subtype):
            obj_id, _ = z_tuple
            yield Pgp(obj_id, subtype)


if __name__ == '__main__':
#     name_to_search = 'ex'
#     subtype = 'name'
#     print(search_pgps_by_name(name_to_search, subtype))
    gen = get_all_pgps_objects(filters={'subtypes': ['key']})
    for f in gen:
        print(f)

