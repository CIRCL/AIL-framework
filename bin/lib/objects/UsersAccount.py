#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
# import re

from flask import url_for
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, AbstractSubtypeObjects, get_all_id
from lib.timeline_engine import Timeline
from lib.objects import Usernames


config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


################################################################################
################################################################################
################################################################################

class UserAccount(AbstractSubtypeObject):
    """
    AIL User Object. (strings)
    """

    def __init__(self, id, subtype):
        super(UserAccount, self).__init__('user-account', id, subtype)

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
            url = url_for('chats_explorer.objects_user_account', type=self.type, subtype=self.subtype, id=self.id)
        else:
            url = f'{baseurl}/objects/user-account?&subtype={self.subtype}&id={self.id}'
        return url

    def get_svg_icon(self): # TODO change icon/color
        return {'style': 'fas', 'icon': '\uf2bd', 'color': '#4dffff', 'radius': 5}

    def get_first_name(self):
        return self._get_field('firstname')

    def get_last_name(self):
        return self._get_field('lastname')

    def get_name(self):
        first_name = self.get_first_name()
        last_name = self.get_last_name()
        if first_name and last_name:
            return f'{first_name} {last_name}'
        elif first_name:
            return first_name
        elif last_name:
            return last_name

    def get_years(self):
        year_start = int(self.get_first_seen()[0:4])
        year_end = int(self.get_last_seen()[0:4])
        return list(range(year_start, year_end + 1))

    def get_phone(self):
        return self._get_field('phone')

    def set_first_name(self, firstname):
        return self._set_field('firstname', firstname)

    def set_last_name(self, lastname):
        return self._set_field('lastname', lastname)

    def set_phone(self, phone):
        return self._set_field('phone', phone)

    def get_icon(self):
        icon = self._get_field('icon')
        if icon:
            return icon.rsplit(':', 1)[1]

    def set_icon(self, icon):
        self._set_field('icon', icon)

    def get_info(self):
        return self._get_field('info')

    def set_info(self, info):
        return self._set_field('info', info)

    # def get_created_at(self, date=False):
    #     created_at = self._get_field('created_at')
    #     if date and created_at:
    #         created_at = datetime.fromtimestamp(float(created_at))
    #         created_at = created_at.isoformat(' ')
    #     return created_at

    # TODO MESSAGES:
    # 1) ALL MESSAGES + NB
    # 2) ALL MESSAGES TIMESTAMP
    # 3) ALL MESSAGES TIMESTAMP By: - chats
    #                               - subchannel
    #                               - thread

    def get_chats(self):
        chats = self.get_correlation('chat')['chat']
        return chats

    def get_chat_subchannels(self):
        chats = self.get_correlation('chat-subchannel')['chat-subchannel']
        return chats

    def get_chat_threads(self):
        chats = self.get_correlation('chat-thread')['chat-thread']
        return chats

    def _get_timeline_username(self):
        return Timeline(self.get_global_id(), 'username')

    def get_username(self):
        return self._get_timeline_username().get_last_obj_id()

    def get_usernames(self):
        usernames = []
        names = self._get_timeline_username().get_objs_ids()
        for name in names:
            _, subtype, obj_id = name.split(':', 2)
            usernames.append({'type': 'username', 'subtype': subtype, 'id': obj_id})
        return usernames

    def get_usernames_history(self):
        return self._get_timeline_username().get_objs()

    def update_username_timeline(self, username_global_id, timestamp):
        self._get_timeline_username().add_timestamp(timestamp, username_global_id)

    def get_messages(self):
        messages = []
        correl = self.get_correlation('message')
        if 'message' in correl:
            for mess_id in correl['message']:
                messages.append(f'message:{mess_id}')
        return messages

    def get_messages_by_chat_obj(self, chat_obj):
        messages = []
        for mess in self.get_correlation_iter_obj(chat_obj, 'message'):
            messages.append(f'message:{mess}')
        return messages

    def get_nb_messages_by_chat_obj(self, chat_obj):
        messages = self.get_correlation_iter_obj(chat_obj, 'message')
        if messages:
            return len(messages)
        else:
            return 0

    def get_meta(self, options=set(), translation_target=None): # TODO Username timeline
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['subtype'] = self.subtype
        meta['tags'] = self.get_tags(r_list=True)  # TODO add in options ????
        if 'username' in options:
            meta['username'] = self.get_username()
            if meta['username']:
                _, username_account_subtype, username_account_id = meta['username'].split(':', 2)
                if 'username_meta' in options:
                    meta['username'] = Usernames.Username(username_account_id, username_account_subtype).get_meta(options={'icon'})
                else:
                    meta['username'] = {'type': 'username', 'subtype': username_account_subtype, 'id': username_account_id}
        if 'usernames' in options:
            meta['usernames'] = self.get_usernames()
        if 'icon' in options:
            meta['icon'] = self.get_icon()
            meta['svg_icon'] = meta['icon']
        if 'info' in options:
            meta['info'] = self.get_info()
            if 'translation' in options and translation_target:
                meta['translation_info'] = self.translate(meta['info'], field='info', target=translation_target)
        # if 'created_at':
        #     meta['created_at'] = self.get_created_at(date=True)
        if 'chats' in options:
            meta['chats'] = self.get_chats()
        if 'subchannels' in options:
            meta['subchannels'] = self.get_chat_subchannels()
        if 'threads' in options:
            meta['threads'] = self.get_chat_threads()
        if 'years' in options:
            meta['years'] = self.get_years()
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


def get_all_subtypes():
    return ail_core.get_object_all_subtypes('user-account')

def get_all():
    users = {}
    for subtype in get_all_subtypes():
        users[subtype] = get_all_by_subtype(subtype)
    return users

def get_all_by_subtype(subtype):
    return get_all_id('user-account', subtype)


class UserAccounts(AbstractSubtypeObjects):
    """
        Usernames Objects
    """
    def __init__(self):
        super().__init__('user-account', UserAccount)

    def get_name(self):
        return 'User-Accounts'

    def get_icon(self):
        return {'fas': 'fas', 'icon': 'user-circle'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_subtypes.objects_dashboard_user_account')
        else:
            url = f'{baseurl}/objects/user-accounts'
        return url

    def sanitize_id_to_search(self, subtypes, name_to_search):
        return name_to_search


# if __name__ == '__main__':
#     from lib.objects import Chats
#     chat = Chats.Chat('', '00098785-7e70-5d12-a120-c5cdc1252b2b')
#     account = UserAccount('', '00098785-7e70-5d12-a120-c5cdc1252b2b')
#     print(account.get_messages_by_chat_obj(chat))
