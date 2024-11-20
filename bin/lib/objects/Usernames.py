#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import re

from flask import url_for
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, AbstractSubtypeObjects, get_all_id

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
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
        return {'style': style, 'icon': icon, 'color': '#4dffff', 'radius': 5}

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['subtype'] = self.subtype
        meta['tags'] = self.get_tags(r_list=True) # TODO NB Chats
        return meta

    def get_misp_object(self):
        obj_attrs = []
        if self.subtype == 'telegram':
            obj = MISPObject('telegram-account', standalone=True)
            obj_attrs.append(obj.add_attribute('username', value=self.id))

        elif self.subtype == 'twitter':
            obj = MISPObject('twitter-account', standalone=True)
            obj_attrs.append(obj.add_attribute('name', value=self.id))

        else:
            obj = MISPObject('user-account', standalone=True)
            obj_attrs.append(obj.add_attribute('username', value=self.id))

        first_seen = self.get_first_seen()
        last_seen = self.get_last_seen()
        if first_seen:
            obj.first_seen = first_seen
        if last_seen:
            obj.last_seen = last_seen
        if not first_seen or not last_seen:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={first_seen}, last={last_seen}')

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

# TODO FILTER NAME + Key + mail
def sanitize_username_name_to_search(name_to_search, subtype): # TODO FILTER NAME

    return name_to_search

def search_usernames_by_name(name_to_search, subtype, r_pos=False):
    usernames = {}
    # for subtype in subtypes:
    r_name = sanitize_username_name_to_search(name_to_search, subtype)
    if not name_to_search or isinstance(r_name, dict):
        # break
        return usernames
    r_name = re.compile(r_name)
    for user_name in get_all_usernames_by_subtype(subtype):
        res = re.search(r_name, user_name)
        if res:
            usernames[user_name] = {}
            if r_pos:
                usernames[user_name]['hl-start'] = res.start()
                usernames[user_name]['hl-end'] = res.end()
    return usernames


class Usernames(AbstractSubtypeObjects):
    """
        Usernames Objects
    """
    def __init__(self):
        super().__init__('username', Username)

    def get_name(self):
        return 'Usernames'

    def get_icon(self):
        return {'fas': 'far', 'icon': 'user'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_subtypes.objects_dashboard_username')
        else:
            url = f'{baseurl}/objects/usernames'
        return url

    def sanitize_id_to_search(self, subtypes, name_to_search):
        return name_to_search


# if __name__ == '__main__':
#     name_to_search = 'co'
#     subtypes = ['telegram']
#     u = Usernames()
#     r = u.search_by_id(name_to_search, subtypes, r_pos=True)
#     print(r)
