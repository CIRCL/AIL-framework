#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from datetime import datetime

from flask import url_for
# from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, get_all_id
from lib.data_retention_engine import update_obj_date
from lib.objects import ail_objects
from lib import item_basic

from lib.correlations_engine import get_correlation_by_correl_type

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
r_cache = config_loader.get_redis_conn("Redis_Cache")
config_loader = None


################################################################################
################################################################################
################################################################################

class Chat(AbstractSubtypeObject):  # TODO # ID == username ?????
    """
    AIL Chat Object. (strings)
    """

    def __init__(self, id, subtype):
        super(Chat, self).__init__('chat', id, subtype)

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

    def get_svg_icon(self):  # TODO
        # if self.subtype == 'telegram':
        #     style = 'fab'
        #     icon = '\uf2c6'
        # elif self.subtype == 'discord':
        #     style = 'fab'
        #     icon = '\uf099'
        # else:
        #     style = 'fas'
        #     icon = '\uf007'
        style = 'fas'
        icon = '\uf086'
        return {'style': style, 'icon': icon, 'color': '#4dffff', 'radius': 5}

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['subtype'] = self.subtype
        meta['tags'] = self.get_tags(r_list=True)
        return meta

    def get_misp_object(self):
        # obj_attrs = []
        # if self.subtype == 'telegram':
        #     obj = MISPObject('telegram-account', standalone=True)
        #     obj_attrs.append(obj.add_attribute('username', value=self.id))
        #
        # elif self.subtype == 'twitter':
        #     obj = MISPObject('twitter-account', standalone=True)
        #     obj_attrs.append(obj.add_attribute('name', value=self.id))
        #
        # else:
        #     obj = MISPObject('user-account', standalone=True)
        #     obj_attrs.append(obj.add_attribute('username', value=self.id))
        #
        # first_seen = self.get_first_seen()
        # last_seen = self.get_last_seen()
        # if first_seen:
        #     obj.first_seen = first_seen
        # if last_seen:
        #     obj.last_seen = last_seen
        # if not first_seen or not last_seen:
        #     self.logger.warning(
        #         f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={first_seen}, last={last_seen}')
        #
        # for obj_attr in obj_attrs:
        #     for tag in self.get_tags():
        #         obj_attr.add_tag(tag)
        # return obj
        return

    ############################################################################
    ############################################################################

    # others optional metas, ... -> # TODO ALL meta in hset

    def get_name(self):  # get username ????
        pass

    # users that send at least a message else participants/spectator
    # correlation created by messages
    def get_users(self):
        users = set()
        accounts = self.get_correlation('user-account').get('user-account', [])
        for account in accounts:
            users.add(account[1:])
        return users


    # def get_last_message_id(self):
    #
    #     return r_object.hget(f'meta:{self.type}:{self.subtype}:{self.id}', 'last:message:id')

    def get_obj_message_id(self, obj_id):
        if obj_id.endswith('.gz'):
            obj_id = obj_id[:-3]
        return int(obj_id.split('_')[-1])

    def _get_message_timestamp(self, obj_global_id):
        return r_object.zscore(f'messages:{self.type}:{self.subtype}:{self.id}', obj_global_id)

    def _get_messages(self):
        return r_object.zrange(f'messages:{self.type}:{self.subtype}:{self.id}', 0, -1, withscores=True)

    def get_message_meta(self, obj_global_id, parent=True, mess_datetime=None):
        obj = ail_objects.get_obj_from_global_id(obj_global_id)
        mess_dict = obj.get_meta(options={'content', 'link', 'parent'})
        if mess_dict.get('parent') and parent:
            mess_dict['reply_to'] = self.get_message_meta(mess_dict['parent'], parent=False)
        mess_dict['username'] = {}
        user = obj.get_correlation('username').get('username')
        if user:
            subtype, user = user.pop().split(':', 1)
            mess_dict['username']['type'] = 'telegram'
            mess_dict['username']['subtype'] = subtype
            mess_dict['username']['id'] = user
        else:
            mess_dict['username']['id'] = 'UNKNOWN'

        if not mess_datetime:
            obj_mess_id = self._get_message_timestamp(obj_global_id)
            mess_datetime = datetime.fromtimestamp(obj_mess_id)
        mess_dict['date'] = mess_datetime.isoformat(' ')
        mess_dict['hour'] = mess_datetime.strftime('%H:%M:%S')
        return mess_dict


    def get_messages(self, start=0, page=1, nb=500):  # TODO limit nb returned, # TODO add replies
        start = 0
        stop = -1
        # r_object.delete(f'messages:{self.type}:{self.subtype}:{self.id}')

        # TODO chat without username ???? -> chat ID ????

        messages = {}
        curr_date = None
        for message in self._get_messages():
            date = datetime.fromtimestamp(message[1])
            date_day = date.strftime('%Y/%m/%d')
            if date_day != curr_date:
                messages[date_day] = []
                curr_date = date_day
            mess_dict = self.get_message_meta(message[0], parent=True, mess_datetime=date)
            messages[date_day].append(mess_dict)
        return messages

        # Zset with ID ???  id -> item id ??? multiple id == media + text
        #                   id -> media id
        # How do we handle reply/thread ??? -> separate with new chats name/id ZSET ???
        # Handle media ???

        # list of message id -> obj_id
        # list of obj_id ->
        # abuse parent children ???

    # def add(self, timestamp, obj_id, mess_id=0, username=None, user_id=None):
    #     date = # TODO get date from object
    #     self.update_daterange(date)
    #     update_obj_date(date, self.type, self.subtype)
    #
    #
    #     # daily
    #     r_object.hincrby(f'{self.type}:{self.subtype}:{date}', self.id, 1)
    #     # all subtypes
    #     r_object.zincrby(f'{self.type}_all:{self.subtype}', 1, self.id)
    #
    #     #######################################################################
    #     #######################################################################
    #
    #     # Correlations
    #     self.add_correlation('item', '', item_id)
    #     # domain
    #     if is_crawled(item_id):
    #         domain = get_item_domain(item_id)
    #         self.add_correlation('domain', '', domain)

    # TODO kvrocks exception if key don't exists
    def get_obj_by_message_id(self, mess_id):
        return r_object.hget(f'messages:ids:{self.type}:{self.subtype}:{self.id}', mess_id)

    # importer -> use cache for previous reply SET to_add_id: previously_imported : expire SET key -> 30 mn
    def add_message(self, obj_global_id, timestamp, mess_id, reply_id=None):
        r_object.hset(f'messages:ids:{self.type}:{self.subtype}:{self.id}', mess_id, obj_global_id)
        r_object.zadd(f'messages:{self.type}:{self.subtype}:{self.id}', {obj_global_id: timestamp})

        if reply_id:
            reply_obj = self.get_obj_by_message_id(reply_id)
            if reply_obj:
                self.add_obj_children(reply_obj, obj_global_id)
            else:
                self.add_message_cached_reply(reply_id, mess_id)

        # ADD cached replies
        for reply_obj in self.get_cached_message_reply(mess_id):
            self.add_obj_children(obj_global_id, reply_obj)

    def _get_message_cached_reply(self, message_id):
        return r_cache.smembers(f'messages:ids:{self.type}:{self.subtype}:{self.id}:{message_id}')

    def get_cached_message_reply(self, message_id):
        objs_global_id = []
        for mess_id in self._get_message_cached_reply(message_id):
            obj_global_id = self.get_obj_by_message_id(mess_id)
            if obj_global_id:
                objs_global_id.append(obj_global_id)
        return objs_global_id

    def add_message_cached_reply(self, reply_to_id, message_id):
        r_cache.sadd(f'messages:ids:{self.type}:{self.subtype}:{self.id}:{reply_to_id}', message_id)
        r_cache.expire(f'messages:ids:{self.type}:{self.subtype}:{self.id}:{reply_to_id}', 600)

    # TODO nb replies = nb son ???? what if it create a onion item ??? -> need source filtering


# TODO factorize
def get_all_subtypes():
    return ail_core.get_object_all_subtypes('chat')

def get_all():
    objs = {}
    for subtype in get_all_subtypes():
        objs[subtype] = get_all_by_subtype(subtype)
    return objs

def get_all_by_subtype(subtype):
    return get_all_id('chat', subtype)

# # TODO FILTER NAME + Key + mail
# def sanitize_username_name_to_search(name_to_search, subtype): # TODO FILTER NAME
#
#     return name_to_search
#
# def search_usernames_by_name(name_to_search, subtype, r_pos=False):
#     usernames = {}
#     # for subtype in subtypes:
#     r_name = sanitize_username_name_to_search(name_to_search, subtype)
#     if not name_to_search or isinstance(r_name, dict):
#         # break
#         return usernames
#     r_name = re.compile(r_name)
#     for user_name in get_all_usernames_by_subtype(subtype):
#         res = re.search(r_name, user_name)
#         if res:
#             usernames[user_name] = {}
#             if r_pos:
#                 usernames[user_name]['hl-start'] = res.start()
#                 usernames[user_name]['hl-end'] = res.end()
#     return usernames


if __name__ == '__main__':
    chat = Chat('test', 'telegram')
    r = chat.get_messages()
    print(r)
