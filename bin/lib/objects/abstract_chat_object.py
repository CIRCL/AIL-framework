# -*-coding:UTF-8 -*
"""
Base Class for AIL Objects
"""

##################################
# Import External packages
##################################
import os
import sys
from abc import ABC

from datetime import datetime
# from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects.abstract_subtype_object import AbstractSubtypeObject
from lib.ail_core import get_object_all_subtypes, zscan_iter ################
from lib.ConfigLoader import ConfigLoader
from lib.objects.Messages import Message
from lib.objects.UsersAccount import UserAccount
from lib.objects.Usernames import Username
from lib.data_retention_engine import update_obj_date

from packages import Date

# LOAD CONFIG
config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
config_loader = None

# # FIXME: SAVE SUBTYPE NAMES ?????

class AbstractChatObject(AbstractSubtypeObject, ABC):
    """
    Abstract Subtype Object
    """

    def __init__(self, obj_type, id, subtype):
        """ Abstract for all the AIL object

        :param obj_type: object type (item, ...)
        :param id: Object ID
        """
        super().__init__(obj_type, id, subtype)

    # get useraccount / username
    # get users ?
    # timeline name ????
    # info
    # created
    # last imported/updated

    # TODO get instance
    # TODO get protocol
    # TODO get network
    # TODO get address

    def get_chat(self):  # require ail object TODO ##
        if self.type != 'chat':
            parent = self.get_parent()
            if parent:
                obj_type, _ = parent.split(':', 1)
                if obj_type == 'chat':
                    return parent

    def get_subchannels(self):
        subchannels = []
        if self.type == 'chat':  # category ???
            for obj_global_id in self.get_childrens():
                obj_type, _ = obj_global_id.split(':', 1)
                if obj_type == 'chat-subchannel':
                    subchannels.append(obj_global_id)
        return subchannels

    def get_nb_subchannels(self):
        nb = 0
        if self.type == 'chat':
            for obj_global_id in self.get_childrens():
                obj_type, _ = obj_global_id.split(':', 1)
                if obj_type == 'chat-subchannel':
                    nb += 1
        return nb

    def get_threads(self):
        threads = []
        for obj_global_id in self.get_childrens():
            obj_type, _ = obj_global_id.split(':', 1)
            if obj_type == 'chat-thread':
                threads.append(obj_global_id)
        return threads

    def get_created_at(self):
        return self._get_field('created_at')

    def set_created_at(self, timestamp):
        self._set_field('created_at', timestamp)

    def get_name(self):
        name = self._get_field('name')
        if not name:
            name = ''
        return name

    def set_name(self, name):
        self._set_field('name', name)

    def get_img(self):
        return self._get_field('img')

    def set_img(self, icon):
        self._set_field('img', icon)

    def get_nb_messages(self):
        return r_object.zcard(f'messages:{self.type}:{self.subtype}:{self.id}')

    def _get_messages(self):  # TODO paginate
        return r_object.zrange(f'messages:{self.type}:{self.subtype}:{self.id}', 0, -1, withscores=True)

    def get_message_meta(self, message, parent=True, mess_datetime=None):  # TODO handle file message
        obj = Message(message[9:])
        mess_dict = obj.get_meta(options={'content', 'link', 'parent', 'user-account'})
        # print(mess_dict)
        if mess_dict.get('parent') and parent:
            mess_dict['reply_to'] = self.get_message_meta(mess_dict['parent'], parent=False)
        if mess_dict.get('user-account'):
            _, user_account_subtype, user_account_id = mess_dict['user-account'].split(':', 3)
            user_account = UserAccount(user_account_id, user_account_subtype)
            mess_dict['user-account'] = {}
            mess_dict['user-account']['type'] = user_account.get_type()
            mess_dict['user-account']['subtype'] = user_account.get_subtype(r_str=True)
            mess_dict['user-account']['id'] = user_account.get_id()
            username = user_account.get_username()
            if username:
                _, username_account_subtype, username_account_id = username.split(':', 3)
                username = Username(username_account_id, username_account_subtype).get_default_meta(link=False)
            mess_dict['user-account']['username'] = username  # TODO get username at the given timestamp ???
        else:
            mess_dict['user-account'] = {'id': 'UNKNOWN'}

        if not mess_datetime:
            obj_mess_id = message.get_timestamp()
            mess_datetime = datetime.fromtimestamp(obj_mess_id)
        mess_dict['date'] = mess_datetime.isoformat(' ')
        mess_dict['hour'] = mess_datetime.strftime('%H:%M:%S')
        return mess_dict

    def get_messages(self, start=0, page=1, nb=500, unread=False): # threads ????
        # TODO return message meta
        tags = {}
        messages = {}
        curr_date = None
        for message in self._get_messages():
            date = datetime.fromtimestamp(message[1])
            date_day = date.strftime('%Y/%m/%d')
            if date_day != curr_date:
                messages[date_day] = []
                curr_date = date_day
            mess_dict = self.get_message_meta(message[0], parent=True, mess_datetime=date)  # TODO use object
            messages[date_day].append(mess_dict)

            if mess_dict.get('tags'):
                for tag in mess_dict['tags']:
                    if tag not in tags:
                        tags[tag] = 0
                    tags[tag] += 1
        return messages, tags

    # TODO REWRITE ADD OR ADD MESSAGE ????
    # add
    # add message

    def get_obj_by_message_id(self, message_id):
        return r_object.hget(f'messages:ids:{self.type}:{self.subtype}:{self.id}', message_id)

    def add_message_cached_reply(self, reply_id, message_id):
        r_cache.sadd(f'messages:ids:{self.type}:{self.subtype}:{self.id}:{reply_id}', message_id)
        r_cache.expire(f'messages:ids:{self.type}:{self.subtype}:{self.id}:{reply_id}', 600)

    def _get_message_cached_reply(self, message_id):
        return r_cache.smembers(f'messages:ids:{self.type}:{self.subtype}:{self.id}:{message_id}')

    def get_cached_message_reply(self, message_id):
        objs_global_id = []
        for mess_id in self._get_message_cached_reply(message_id):
            obj_global_id = self.get_obj_by_message_id(mess_id) # TODO CATCH EXCEPTION
            if obj_global_id:
                objs_global_id.append(obj_global_id)
        return objs_global_id

    def add_message(self, obj_global_id, message_id, timestamp, reply_id=None):
        r_object.hset(f'messages:ids:{self.type}:{self.subtype}:{self.id}', message_id, obj_global_id)
        r_object.zadd(f'messages:{self.type}:{self.subtype}:{self.id}', {obj_global_id: float(timestamp)})

        # MESSAGE REPLY
        if reply_id:
            reply_obj = self.get_obj_by_message_id(reply_id)  # TODO CATCH EXCEPTION
            if reply_obj:
                self.add_obj_children(reply_obj, obj_global_id)
            else:
                self.add_message_cached_reply(reply_id, message_id)


    # get_messages_meta ????

# TODO move me to abstract subtype
class AbstractChatObjects(ABC):
    def __init__(self, type):
        self.type = type

    def add_subtype(self, subtype):
        r_object.sadd(f'all_{self.type}:subtypes', subtype)

    def get_subtypes(self):
        return r_object.smembers(f'all_{self.type}:subtypes')

    def get_nb_ids_by_subtype(self, subtype):
        return r_object.zcard(f'{self.type}_all:{subtype}')

    def get_ids_by_subtype(self, subtype):
        return r_object.zrange(f'{self.type}_all:{subtype}', 0, -1)

    def get_all_id_iterator_iter(self, subtype):
        return zscan_iter(r_object, f'{self.type}_all:{subtype}')

    def get_ids(self):
        pass

    def search(self):
        pass



