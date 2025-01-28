# -*-coding:UTF-8 -*
"""
Base Class for AIL Objects
"""

##################################
# Import External packages
##################################
import os
import sys
import time
from abc import ABC

from datetime import datetime, timezone
# from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, AbstractSubtypeObjects
from lib.ail_core import unpack_correl_objs_id, zscan_iter ################
from lib.ConfigLoader import ConfigLoader
from lib.objects import Messages
from packages import Date

# from lib.data_retention_engine import update_obj_date


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
        for child in self.get_childrens():
            obj_type, obj_subtype, obj_id = child.split(':', 2)
            if obj_type == 'chat-thread':
                threads.append({'type': obj_type, 'subtype': obj_subtype, 'id': obj_id})
        return threads

    def get_created_at(self, date=False):
        created_at = self._get_field('created_at')
        if date and created_at:
            created_at = datetime.utcfromtimestamp(float(created_at))
            created_at = created_at.isoformat(' ')
        return created_at

    def set_created_at(self, timestamp):
        self._set_field('created_at', timestamp)

    def get_name(self):
        name = self._get_field('name')
        if not name:
            name = ''
        return name

    def set_name(self, name):
        self._set_field('name', name)

    def get_icon(self):
        icon = self._get_field('icon')
        if icon:
            return icon.rsplit(':', 1)[1]

    def set_icon(self, icon):
        self._set_field('icon', icon)

    def get_info(self):
        return self._get_field('info')

    def set_info(self, info):
        self._set_field('info', info)

    def get_nb_messages(self):
        return r_object.zcard(f'messages:{self.type}:{self.subtype}:{self.id}')

    def get_message_page(self, message, nb):
        rank = r_object.zrank(f'messages:{self.type}:{self.subtype}:{self.id}', f'message::{message}')
        if not rank:
            return -1
        return int(rank/ nb) + 1

    def _get_messages(self, nb=-1, page=-1):
        if nb < 1:
            messages = r_object.zrange(f'messages:{self.type}:{self.subtype}:{self.id}', 0, -1, withscores=True)
            nb_pages = 0
            page = 1
            total = len(messages)
            nb_first = 1
            nb_last = total
        else:
            total = r_object.zcard(f'messages:{self.type}:{self.subtype}:{self.id}')
            nb_pages = total / nb
            if not nb_pages.is_integer():
                nb_pages = int(nb_pages) + 1
            else:
                nb_pages = int(nb_pages)
            if page > nb_pages or page < 1:
                page = nb_pages

            if page > 1:
                start = (page - 1) * nb
            else:
                start = 0
            messages = r_object.zrange(f'messages:{self.type}:{self.subtype}:{self.id}', start, start+nb-1, withscores=True)
            # if messages:
            #     messages = reversed(messages)
            nb_first = start+1
            nb_last = start+nb
        if nb_last > total:
            nb_last = total
        return messages, {'nb': nb, 'page': page, 'nb_pages': nb_pages, 'total': total, 'nb_first': nb_first, 'nb_last': nb_last}

    def get_timestamp_first_message(self):
        first = r_object.zrange(f'messages:{self.type}:{self.subtype}:{self.id}', 0, 0, withscores=True)
        if first:
            return int(first[0][1])

    def get_timestamp_last_message(self):
        last = r_object.zrevrange(f'messages:{self.type}:{self.subtype}:{self.id}', 0, 0, withscores=True)
        if last:
            return int(last[0][1])

    def get_first_message(self):
        return r_object.zrange(f'messages:{self.type}:{self.subtype}:{self.id}', 0, 0)

    def get_last_message(self):
        return r_object.zrevrange(f'messages:{self.type}:{self.subtype}:{self.id}', 0, 0)

    def get_nb_message_by_hours(self, date_day, nb_day):
        hours = []
        # start=0, end=23
        timestamp = time.mktime(datetime.strptime(date_day, "%Y%m%d").utctimetuple())
        for i in range(24):
            timestamp_end = timestamp + 3600
            nb_messages = r_object.zcount(f'messages:{self.type}:{self.subtype}:{self.id}', timestamp, timestamp_end)
            timestamp = timestamp_end
            hours.append({'date': f'{date_day[0:4]}-{date_day[4:6]}-{date_day[6:8]}', 'day': nb_day, 'hour': i, 'count': nb_messages})
        return hours

    def get_nb_message_by_week(self, date_day):
        date_day = Date.get_date_week_by_date(date_day)
        week_messages = []
        i = 0
        for date in Date.daterange_add_days(date_day, 6):
            week_messages = week_messages + self.get_nb_message_by_hours(date, i)
            i += 1
        return week_messages

    def get_nb_message_this_week(self):
        week_date = Date.get_current_week_day()
        return self.get_nb_message_by_week(week_date)

    def get_nb_week_messages(self):
        week = {}
        # Init
        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            week[day] = {}
            for i in range(24):
                week[day][i] = 0

        # chat
        for mess_t in r_object.zrange(f'messages:{self.type}:{self.subtype}:{self.id}', 0, -1, withscores=True):
            timestamp = datetime.utcfromtimestamp(float(mess_t[1]))
            date_name = timestamp.strftime('%a')
            week[date_name][timestamp.hour] += 1

        subchannels = self.get_subchannels()
        for gid in subchannels:
            for mess_t in r_object.zrange(f'messages:{gid}', 0, -1, withscores=True):
                timestamp = datetime.utcfromtimestamp(float(mess_t[1]))
                date_name = timestamp.strftime('%a')
                week[date_name][timestamp.hour] += 1
        stats = []
        nb_day = 0
        for day in week:
            for hour in week[day]:
                stats.append({'date': day, 'day': nb_day, 'hour': hour, 'count': week[day][hour]})
            nb_day += 1
        return stats

    def get_message_years(self):
        timestamp = self.get_timestamp_first_message()
        if not timestamp:
            year_start = int(self.get_first_seen()[0:4])
            year_end = int(self.get_last_seen()[0:4])
            return list(range(year_start, year_end + 1))
        else:
            timestamp = datetime.utcfromtimestamp(float(timestamp))
            year_start = int(timestamp.strftime('%Y'))
            timestamp = datetime.utcfromtimestamp(float(self.get_timestamp_last_message()))
            year_end = int(timestamp.strftime('%Y'))
            return list(range(year_start, year_end + 1))

    def get_nb_year_messages(self, year):
        nb_year = {}
        nb_max = 0
        start = int(datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        end = int(datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp())

        for mess_t in r_object.zrangebyscore(f'messages:{self.type}:{self.subtype}:{self.id}', start, end, withscores=True):
            timestamp = datetime.utcfromtimestamp(float(mess_t[1]))
            date = timestamp.strftime('%Y-%m-%d')
            if date not in nb_year:
                nb_year[date] = 0
            nb_year[date] += 1
            nb_max = max(nb_max, nb_year[date])

        subchannels = self.get_subchannels()
        for gid in subchannels:
            for mess_t in r_object.zrangebyscore(f'messages:{gid}', start, end, withscores=True):
                timestamp = datetime.utcfromtimestamp(float(mess_t[1]))
                date = timestamp.strftime('%Y-%m-%d')
                if date not in nb_year:
                    nb_year[date] = 0
                nb_year[date] += 1
                nb_max = max(nb_max, nb_year[date])

        return nb_max, nb_year

    def get_message_meta(self, message, timestamp=None, translation_target='', options=None):  # TODO handle file message
        message = Messages.Message(message[9:])
        if not options:
            options = {'barcodes', 'content', 'files', 'files-names', 'forwarded_from', 'images', 'language', 'link', 'parent', 'parent_meta', 'qrcodes', 'reactions', 'thread', 'translation', 'user-account'}
        meta = message.get_meta(options=options, timestamp=timestamp, translation_target=translation_target)
        return meta

    def get_messages(self, start=0, page=-1, nb=500, message=None, unread=False, options=None, translation_target='en'):  # threads ???? # TODO ADD last/first message timestamp + return page
        # TODO return message meta
        tags = {}
        messages = {}
        curr_date = None
        try:
            nb = int(nb)
        except TypeError:
            nb = 500
        if message:
            page = self.get_message_page(message, nb)
        else:
            if not page:
                page = -1
            try:
                page = int(page)
            except TypeError:
                page = 1
        mess, pagination = self._get_messages(nb=nb, page=page)
        for message in mess:
            timestamp = message[1]
            date_day = datetime.utcfromtimestamp(timestamp).strftime('%Y/%m/%d')
            if date_day != curr_date:
                messages[date_day] = []
                curr_date = date_day
            mess_dict = self.get_message_meta(message[0], timestamp=timestamp, translation_target=translation_target, options=options)
            messages[date_day].append(mess_dict)

            if mess_dict.get('tags'):
                for tag in mess_dict['tags']:
                    if tag not in tags:
                        tags[tag] = 0
                    tags[tag] += 1
        return messages, pagination, tags

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
            obj_global_id = self.get_obj_by_message_id(mess_id)  # TODO CATCH EXCEPTION
            if obj_global_id:
                objs_global_id.append(obj_global_id)
        return objs_global_id

    def add_chat_with_messages(self):
        r_object.sadd(f'{self.type}_w_mess:{self.subtype}', self.id)

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
        # CACHED REPLIES
        for mess_id in self.get_cached_message_reply(message_id):
            self.add_obj_children(obj_global_id, mess_id)

    # def get_deleted_messages(self, message_id):

    def get_participants(self):
        return unpack_correl_objs_id('user-account', self.get_correlation('user-account')['user-account'], r_type='dict')

    def get_nb_participants(self):
        return self.get_nb_correlation('user-account')

    def get_user_messages(self, user_id):
        return self.get_correlation_iter('user-account', self.subtype, user_id, 'message')

# TODO move me to abstract subtype
class AbstractChatObjects(AbstractSubtypeObjects, ABC):

    def __init__(self, obj_type, obj_class):
        super().__init__(obj_type, obj_class)

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
