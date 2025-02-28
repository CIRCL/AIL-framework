#!/usr/bin/python3

"""
Chats Viewer
===================


"""
import os
import sys
import time
import uuid

from datetime import datetime, timezone

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ail_core import generate_uuid
from lib.ConfigLoader import ConfigLoader
from lib.objects import Chats
from lib.objects import ChatSubChannels
from lib.objects import ChatThreads
from lib.objects import Messages
from lib.objects.BarCodes import Barcode
from lib.objects.QrCodes import Qrcode
from lib.objects.Ocrs import Ocr
from lib.objects import UsersAccount
from lib.objects import Usernames
from lib import Language
from lib import Tag
from packages import Date

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
r_crawler = config_loader.get_db_conn("Kvrocks_Crawler")
r_cache = config_loader.get_redis_conn("Redis_Cache")

r_obj = config_loader.get_db_conn("Kvrocks_DB")  # TEMP new DB ????

# # # # # # # #
#             #
#   COMMON    #
#             #
# # # # # # # #

# TODO ChatDefaultPlatform

# CHAT(type=chat, subtype=platform, id= chat_id)

# Channel(type=channel, subtype=platform, id=channel_id)

# Thread(type=thread, subtype=platform, id=thread_id)

# Message(type=message, subtype=platform, id=message_id)


# Protocol/Platform


# class ChatProtocols: # TODO Remove Me
#
#     def __init__(self):  # name ???? subtype, id ????
#         # discord, mattermost, ...
#         pass
#
#     def get_chat_protocols(self):
#         pass
#
#     def get_chat_protocol(self, protocol):
#         pass
#
#     ################################################################
#
#     def get_instances(self):
#         pass
#
#     def get_chats(self):
#         pass
#
#     def get_chats_by_instance(self, instance):
#         pass
#
#
# class ChatNetwork:  # uuid or protocol
#     def __init__(self, network='default'):
#         self.id = network
#
#     def get_addresses(self):
#         pass
#
#
# class ChatServerAddress: # uuid or protocol + network
#     def __init__(self, address='default'):
#         self.id = address

# map uuid -> type + field

# TODO option last protocol/ imported messages/chat -> unread mode ????

# # # # # # # # #
#               #
#   PROTOCOLS   #       IRC, discord, mattermost, ...
#               #
# # # # # # # # #       TODO icon => UI explorer by protocol + network + instance

def get_chat_protocols():
    return r_obj.smembers(f'chat:protocols')

def get_chat_protocols_meta():
    metas = []
    for protocol_id in get_chat_protocols():
        protocol = ChatProtocol(protocol_id)
        metas.append(protocol.get_meta(options={'icon'}))
    metas = sorted(metas, key=lambda d: d['id'])
    return metas

class ChatProtocol: # TODO first seen last seen ???? + nb by day ????
    def __init__(self, protocol):
        self.id = protocol

    def exists(self):
        return r_db.exists(f'chat:protocol:{self.id}')

    def get_networks(self):
        return r_db.smembers(f'chat:protocol:{self.id}')

    def get_nb_networks(self):
        return r_db.scard(f'chat:protocol:{self.id}')

    def get_icon(self):
        if self.id == 'discord':
            icon = {'style': 'fab', 'icon': 'fa-discord'}
        elif self.id == 'telegram':
            icon = {'style': 'fab', 'icon': 'fa-telegram'}
        else:
            icon = {}
        return icon

    def get_meta(self, options=set()):
        meta = {'id': self.id}
        if 'icon' in options:
            meta['icon'] = self.get_icon()
        return meta

    # def get_addresses(self):
    #     pass
    #
    # def get_instances_uuids(self):
    #     pass


# # # # # # # # # # # # # #
#                         #
#   ChatServiceInstance   #
#                         #
# # # # # # # # # # # # # #

# uuid -> protocol + network + server
class ChatServiceInstance:
    def __init__(self, instance_uuid):
        self.uuid = instance_uuid

    def exists(self):
        return r_obj.exists(f'chatSerIns:{self.uuid}')

    def get_protocol(self): # return objects ????
        return r_obj.hget(f'chatSerIns:{self.uuid}', 'protocol')

    def get_network(self): # return objects ????
        network = r_obj.hget(f'chatSerIns:{self.uuid}', 'network')
        if network:
            return network

    def get_address(self): # return objects ????
        address = r_obj.hget(f'chatSerIns:{self.uuid}', 'address')
        if address:
            return address

    def get_meta(self, options=set()):
        meta = {'uuid': self.uuid,
                'protocol': self.get_protocol(),
                'network': self.get_network(),
                'address': self.get_address()}
        if 'chats' in options:
            meta['chats'] = []
            for chat_id in self.get_chats():
                meta['chats'].append(Chats.Chat(chat_id, self.uuid).get_meta({'created_at', 'icon', 'nb_subchannels', 'nb_messages'}))
        if 'chats_with_messages':
            meta['chats'] = []
            for chat_id in self.get_chats_with_messages():
                meta['chats'].append(
                    Chats.Chat(chat_id, self.uuid).get_meta({'created_at', 'icon', 'nb_subchannels', 'nb_messages', 'username', 'str_username'}))
        return meta

    def get_nb_chats(self):
        return Chats.Chats().get_nb_ids_by_subtype(self.uuid)

    def get_chats(self):
        return Chats.Chats().get_ids_by_subtype(self.uuid)

    def get_chats_with_messages(self):
        return Chats.Chats().get_ids_with_messages_by_subtype(self.uuid)

def get_chat_service_instances():
    return r_obj.smembers(f'chatSerIns:all')

def get_chat_service_instances_by_protocol(protocol):
    instance_uuids = {}
    for network in r_obj.smembers(f'chat:protocol:networks:{protocol}'):
        inst_uuids = r_obj.hvals(f'map:chatSerIns:{protocol}:{network}')
        if not network:
            network = 'default'
        instance_uuids[network] = inst_uuids
    return instance_uuids

def get_chat_service_instance_uuid(protocol, network, address):
    if not network:
        network = ''
    if not address:
        address = ''
    return r_obj.hget(f'map:chatSerIns:{protocol}:{network}', address)

def get_chat_service_instance_uuid_meta_from_network_dict(instance_uuids):
    for network in instance_uuids:
        metas = []
        for instance_uuid in instance_uuids[network]:
            metas.append(ChatServiceInstance(instance_uuid).get_meta())
        instance_uuids[network] = metas
    return instance_uuids

def get_chat_service_instance(protocol, network, address):
    instance_uuid = get_chat_service_instance_uuid(protocol, network, address)
    if instance_uuid:
        return ChatServiceInstance(instance_uuid)

def create_chat_service_instance(protocol, network=None, address=None):
    instance_uuid = get_chat_service_instance_uuid(protocol, network, address)
    if instance_uuid:
        return instance_uuid
    else:
        if not network:
            network = ''
        if not address:
            address = ''
        instance_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f'{protocol}|{network}|{address}'))
        r_obj.sadd(f'chatSerIns:all', instance_uuid)

        # map instance - uuid
        r_obj.hset(f'map:chatSerIns:{protocol}:{network}', address, instance_uuid)

        r_obj.hset(f'chatSerIns:{instance_uuid}', 'protocol', protocol)
        if network:
            r_obj.hset(f'chatSerIns:{instance_uuid}', 'network', network)
        if address:
            r_obj.hset(f'chatSerIns:{instance_uuid}', 'address', address)

        # protocols
        r_obj.sadd(f'chat:protocols', protocol)  # TODO first seen / last seen

        # protocol -> network
        r_obj.sadd(f'chat:protocol:networks:{protocol}', network)

        return instance_uuid




    # INSTANCE ===> CHAT IDS





    # protocol -> instance_uuids => for protocol->networks -> protocol+network => HGETALL
    # protocol+network -> instance_uuids => HGETALL

    # protocol -> networks  ???default??? or ''

    # --------------------------------------------------------
    # protocol+network -> addresses => HKEYS
    # protocol+network+addresse => HGET


# Chat -> subtype=uuid, id = chat id


# instance_uuid -> chat id


# protocol - uniq ID
# protocol + network -> uuid ????
# protocol + network + address -> uuid

#######################################################################################

def get_obj_chat(chat_type, chat_subtype, chat_id):
    if chat_type == 'chat':
        return Chats.Chat(chat_id, chat_subtype)
    elif chat_type == 'chat-subchannel':
        return ChatSubChannels.ChatSubChannel(chat_id, chat_subtype)
    elif chat_type == 'chat-thread':
        return ChatThreads.ChatThread(chat_id, chat_subtype)

def get_obj_chat_from_global_id(chat_gid):
    chat_type, chat_subtype, chat_id = chat_gid.split(':', 2)
    return get_obj_chat(chat_type, chat_subtype, chat_id)

def get_obj_chat_meta(obj_chat, new_options=set()):
    options = {}
    if obj_chat.type == 'chat':
        options = {'created_at', 'icon', 'info', 'subchannels', 'threads', 'username'}
    elif obj_chat.type == 'chat-subchannel':
        options = {'chat', 'created_at', 'icon', 'nb_messages', 'threads'}
    elif obj_chat.type == 'chat-thread':
        options = {'chat', 'nb_messages'}
    for option in new_options:
        options.add(option)
    return obj_chat.get_meta(options=options)

def get_subchannels_meta_from_global_id(subchannels, translation_target=None):
    meta = []
    for sub in subchannels:
        _, instance_uuid, sub_id = sub.split(':', 2)
        subchannel = ChatSubChannels.ChatSubChannel(sub_id, instance_uuid)
        meta.append(subchannel.get_meta({'nb_messages', 'created_at', 'icon', 'translation'}, translation_target=translation_target))
    return meta

def get_chat_meta_from_global_id(chat_global_id):
    _, instance_uuid, chat_id = chat_global_id.split(':', 2)
    chat = Chats.Chat(chat_id, instance_uuid)
    return chat.get_meta()

def get_threads_metas(threads):
    metas = []
    for thread in threads:
        metas.append(ChatThreads.ChatThread(thread['id'], thread['subtype']).get_meta(options={'name', 'nb_messages'}))
    return metas

def get_username_meta_from_global_id(username_global_id):
    _, instance_uuid, username_id = username_global_id.split(':', 2)
    username = Usernames.Username(username_id, instance_uuid)
    return username.get_meta(options={'icon'})

###############################################################################
# TODO Pagination
def list_messages_to_dict(l_messages_id, translation_target=None):
    options = {'content', 'files', 'files-names', 'images', 'language', 'link', 'parent', 'parent_meta', 'reactions', 'thread', 'translation', 'user-account'}
    meta = {}
    curr_date = None
    for mess_id in l_messages_id:
        message = Messages.Message(mess_id[1:])
        timestamp = message.get_timestamp()
        date_day = message.get_date()
        date_day = f'{date_day[0:4]}/{date_day[4:6]}/{date_day[6:8]}'
        if date_day != curr_date:
            meta[date_day] = []
            curr_date = date_day
        meta_mess = message.get_meta(options=options, timestamp=timestamp, translation_target=translation_target)
        meta[date_day].append(meta_mess)

        # if mess_dict.get('tags'):
        #     for tag in mess_dict['tags']:
        #         if tag not in tags:
        #             tags[tag] = 0
        #         tags[tag] += 1
    # return messages, pagination, tags
    return meta

# TODO Filter
## Instance type
## Chats IDS
## SubChats IDS
## Threads IDS
## Daterange
def get_messages_iterator(filters={}):
    # Tags
    tags = filters.get('tags', [])
    if tags:
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')
        if not date_from:
            date_from = Tag.get_tags_min_first_seen(tags)
            if date_from == '99999999':
                return None
        if not date_to:
            date_to = Date.get_today_date_str()
        daterange = Date.get_daterange(date_from, date_to)
        for date in daterange:
            for message_id in Tag.get_objs_by_date('message', tags, date):
                yield Messages.Message(message_id)
    else:
        for instance_uuid in get_chat_service_instances():

            for chat_id in ChatServiceInstance(instance_uuid).get_chats():
                chat = Chats.Chat(chat_id, instance_uuid)

                # subchannels
                for subchannel_gid in chat.get_subchannels():
                    _, _, subchannel_id = subchannel_gid.split(':', 2)
                    subchannel = ChatSubChannels.ChatSubChannel(subchannel_id, instance_uuid)
                    messages, _ = subchannel._get_messages(nb=-1)
                    for mess in messages:
                        _, _, message_id = mess[0].split(':', )
                        yield Messages.Message(message_id)
                    # threads

                # threads
                for threads in chat.get_threads():
                    thread = ChatThreads.ChatThread(threads['id'], instance_uuid)
                    messages, _ = thread._get_messages(nb=-1)
                    for mess in messages:
                        message_id, _, message_id = mess[0].split(':', )
                        yield Messages.Message(message_id)

                # messages
                messages, _ = chat._get_messages(nb=-1)
                for mess in messages:
                    _, _, message_id = mess[0].split(':', )
                    yield Messages.Message(message_id)
                    # threads ???

def get_nb_messages_iterator(filters={}):
    nb_messages = 0
    for instance_uuid in get_chat_service_instances():
        for chat_id in ChatServiceInstance(instance_uuid).get_chats():
            chat = Chats.Chat(chat_id, instance_uuid)
            # subchannels
            for subchannel_gid in chat.get_subchannels():
                _, _, subchannel_id = subchannel_gid.split(':', 2)
                subchannel = ChatSubChannels.ChatSubChannel(subchannel_id, instance_uuid)
                nb_messages += subchannel.get_nb_messages()
            # threads
            for threads in chat.get_threads():
                thread = ChatThreads.ChatThread(threads['id'], instance_uuid)
                nb_messages += thread.get_nb_messages()
            # messages
            nb_messages += chat.get_nb_messages()
    return nb_messages


def get_ocrs_iterator(filters={}):
    for instance_uuid in get_chat_service_instances():
        for chat_id in ChatServiceInstance(instance_uuid).get_chats():
            chat = Chats.Chat(chat_id, instance_uuid)
            for ocr in chat.get_correlation('ocr').get('ocr', []):
                _, ocr_id = ocr.split(':', 1)
                yield Ocr(ocr_id)

def get_nb_ors_iterator(filters={}):
    nb = 0
    for instance_uuid in get_chat_service_instances():
        for chat_id in ChatServiceInstance(instance_uuid).get_chats():
            chat = Chats.Chat(chat_id, instance_uuid)
            nb += chat.get_nb_correlation('ocr')
    return nb


def get_chat_object_messages_meta(c_messages):
    temp_chats = {}
    for date in c_messages:
        for meta in c_messages[date]:
            if 'forwarded_from' in meta:
                if meta['forwarded_from'] not in temp_chats:
                    chat = get_obj_chat_from_global_id(meta['forwarded_from'])
                    temp_chats[meta['forwarded_from']] = chat.get_meta({'icon'})
                else:
                    meta['forwarded_from'] = temp_chats[meta['forwarded_from']]
            if meta['barcodes']:
                barcodes = []
                for q in meta['barcodes']:
                    obj = Barcode(q)
                    barcodes.append({'id': obj.id, 'content': obj.get_content(), 'tags': obj.get_tags()})
                meta['barcodes'] = barcodes
            if meta['qrcodes']:
                qrcodes = []
                for q in meta['qrcodes']:
                    qr = Qrcode(q)
                    qrcodes.append({'id': qr.id, 'content': qr.get_content(), 'tags': qr.get_tags()})
                meta['qrcodes'] = qrcodes
    return c_messages

def get_user_account_chats_meta(user_id, chats, subchannels):
    meta = []
    for chat_g_id in chats:
        c_subtype, c_id = chat_g_id.split(':', 1)
        chat = Chats.Chat(c_id, c_subtype)
        chat_meta = chat.get_meta(options={'icon', 'info', 'nb_participants', 'tags_safe', 'username'})
        if chat_meta['username']:
            chat_meta['username'] = get_username_meta_from_global_id(chat_meta['username'])
        chat_meta['nb_messages'] = len(chat.get_user_messages(user_id))
        chat_meta['subchannels'] = []
        for subchannel_gid in chat.get_subchannels():
            if subchannel_gid[16:] in subchannels:
                _, s_subtype, s_id = subchannel_gid.split(':', 2)
                subchannel = ChatSubChannels.ChatSubChannel(s_id, s_subtype)
                subchannel_meta = subchannel.get_meta(options={'created_at'})
                subchannel_meta['nb_messages'] = len(subchannel.get_user_messages(user_id))
                chat_meta['subchannels'].append(subchannel_meta)
        meta.append(chat_meta)
    return meta

def get_user_account_chat_message(user_id, subtype, chat_id):  # TODO subchannel + threads ...
    meta = {}
    chat = Chats.Chat(chat_id, subtype)
    chat_meta = chat.get_meta(options={'icon', 'info', 'nb_participants', 'tags_safe', 'username'})
    if chat_meta['username']:
        chat_meta['username'] = get_username_meta_from_global_id(chat_meta['username'])

    meta['messages'] = list_messages_to_dict(chat.get_user_messages(user_id), translation_target=None)
    return meta

def get_user_account_nb_all_week_messages(user_id, chats, subchannels):
    week = {}
    # Init
    for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
        week[day] = {}
        for i in range(24):
            week[day][i] = 0

    # chats
    for chat_g_id in chats:
        c_subtype, c_id = chat_g_id.split(':', 1)
        chat = Chats.Chat(c_id, c_subtype)
        for message in chat.get_user_messages(user_id):
            timestamp = message.split('/', 2)[1]
            timestamp = datetime.utcfromtimestamp(float(timestamp))
            date_name = timestamp.strftime('%a')
            week[date_name][timestamp.hour] += 1

    stats = []
    nb_day = 0
    for day in week:
        for hour in week[day]:
            stats.append({'date': day, 'day': nb_day, 'hour': hour, 'count': week[day][hour]})
        nb_day += 1
    return stats


def get_user_account_nb_year_messages(user_id, chats, year):
    nb_year = {}
    nb_max = 0
    start = int(datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
    end = int(datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp())

    for chat_g_id in chats:
        c_subtype, c_id = chat_g_id.split(':', 1)
        chat = Chats.Chat(c_id, c_subtype)
        for message in chat.get_user_messages(user_id):
            timestamp = int(message.split('/', 2)[1])
            if start <= timestamp <= end:
                timestamp = datetime.utcfromtimestamp(timestamp)
                date = timestamp.strftime('%Y-%m-%d')
                if date not in nb_year:
                    nb_year[date] = 0
                nb_year[date] += 1
                nb_max = max(nb_max, nb_year[date])

    return nb_max, nb_year


def get_user_account_usernames_timeline(subtype, user_id):
    user_account = UsersAccount.UserAccount(user_id, subtype)
    usernames = user_account.get_usernames_history()
    r_usernames = []
    if usernames:
        for row in usernames:
            if not row['obj']:
                continue
            row['obj'] = row['obj'].rsplit(':', 1)[1]
            if row['start'] > row['end']:
                t = row['start']
                row['start'] = row['end']
                row['end'] = t
            if row['start'] == row['end']:
                row['end'] = row['end'] + 1
            row['start'] = row['start'] * 1000
            row['end'] = row['end'] * 1000
            r_usernames.append(row)
    return r_usernames

def get_user_account_chats_chord(subtype, user_id):
    nb = {}
    user_account = UsersAccount.UserAccount(user_id, subtype)
    for chat_g_id in user_account.get_chats():
        c_subtype, c_id = chat_g_id.split(':', 1)
        chat = Chats.Chat(c_id, c_subtype)
        nb[f'chat:{chat_g_id}'] = len(chat.get_user_messages(user_id))

    user_account_gid = user_account.get_global_id() # # #
    chord = {'meta': {}, 'data': []}
    label = get_chat_user_account_label(user_account_gid)
    if label:
        chord['meta'][user_account_gid] = label
    else:
        chord['meta'][user_account_gid] = user_account_gid

    for chat_g_id in nb:
        label = get_chat_user_account_label(chat_g_id)
        if label:
            chord['meta'][chat_g_id] = label
        else:
            chord['meta'][chat_g_id] = chat_g_id
        chord['data'].append({'source': user_account_gid, 'target': chat_g_id, 'value': nb[chat_g_id]})
    return chord

def get_user_account_mentions_chord(subtype, user_id):
    chord = {'meta': {}, 'data': []}
    nb = {}
    user_account = UsersAccount.UserAccount(user_id, subtype)
    user_account_gid = user_account.get_global_id()
    label = get_chat_user_account_label(user_account_gid)
    if label:
        chord['meta'][user_account_gid] = label
    else:
        chord['meta'][user_account_gid] = user_account_gid

    for mess in user_account.get_messages():
        m = Messages.Message(mess[9:])
        for rel in m.get_obj_relationships(relationships={'mention'}, filter_types={'chat', 'user_account'}):
            if rel:
                if not rel['target'] in nb:
                    nb[rel['target']] = 0
                nb[rel['target']] += 1

    for g_id in nb:
        label = get_chat_user_account_label(g_id)
        if label:
            chord['meta'][g_id] = label
        else:
            chord['meta'][g_id] = g_id
        chord['data'].append({'source': user_account_gid, 'target': g_id, 'value': nb[g_id]})
    return chord


def _get_chat_card_meta_options():
    return {'created_at', 'icon', 'info', 'nb_participants', 'origin_link', 'subchannels', 'tags_safe', 'threads', 'translation', 'username'}

def _get_message_bloc_meta_options():
    return {'chat', 'content', 'files', 'files-names', 'icon', 'images', 'language', 'link', 'parent', 'parent_meta', 'reactions','thread', 'translation', 'user-account'}

def get_message_report(l_mess): # TODO Force language + translation
    translation_target = 'en'
    chats = {}
    messages = []
    mess_options = _get_message_bloc_meta_options()

    l_mess = sorted(l_mess, key=lambda x: x[2])

    for m in l_mess:
        message = Messages.Message(m[2])
        meta = message.get_meta(options=mess_options, translation_target=translation_target)
        if meta['chat'] not in chats:
            chat = Chats.Chat(meta['chat'], message.get_chat_instance())
            meta_chat = chat.get_meta(options=_get_chat_card_meta_options(), translation_target=translation_target)
            if meta_chat['username']:
                meta_chat['username'] = get_username_meta_from_global_id(meta_chat['username'])
            chats[chat.id] = meta_chat

            # stats
            chats[chat.id]['t_messages'] = 1
        else:
            chats[meta['chat']]['t_messages'] += 1

        messages.append(meta)

    return chats, messages

# # # # # # # # # # # # # #
#                         #
#   ChatMonitoringRequest #
#                         #
# # # # # # # # # # # # # #

def get_chats_monitoring_requests():
    return r_obj.smembers(f'chats:requests')

def get_chats_monitoring_requests_metas():
    requests = []
    for r in get_chats_monitoring_requests():
        cr = ChatsMonitoringRequest(r)
        requests.append(cr.get_meta())
    return requests

class ChatsMonitoringRequest:
    def __init__(self, r_uuid):
        self.uuid = r_uuid

    def _get_field(self, name):
        return r_obj.hget(f'chats:request:{self.uuid}', name)

    def _set_field(self, name, value):
        r_obj.hset(f'chats:request:{self.uuid}', name, value)

    def exists(self):
        r_obj.exists(f'chats:request:{self.uuid}')

    def get_meta(self):
        return {'uuid': self.uuid,
                'date':  self._get_field('date'),
                'creator': self._get_field('creator'),
                'chat_type': self._get_field('chat_type'),
                'invite': self._get_field('invite'),
                'username': self._get_field('username'),
                'description': self._get_field('description'),
        }

    def create(self, creator, chat_type, invite, username, description):
        self._set_field('chat_type', chat_type)
        self._set_field('creator', creator)
        self._set_field('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        if invite:
            self._set_field('invite', invite)
        if username:
            self._set_field('username', username)
        if description:
            self._set_field('description', description)
        r_obj.sadd(f'chats:requests', self.uuid)

def create_chat_monitoring_requests(creator, chat_type, invite, username, description):
    r_uuid = generate_uuid()
    chat_request = ChatsMonitoringRequest(r_uuid)
    chat_request.create(creator, chat_type, invite, username, description)
    return r_uuid


#### FIX ####

def fix_correlations_subchannel_message():
    for instance_uuid in get_chat_service_instances():
        for chat_id in ChatServiceInstance(instance_uuid).get_chats():
            chat = Chats.Chat(chat_id, instance_uuid)
            # subchannels
            for subchannel_gid in chat.get_subchannels():
                _, _, subchannel_id = subchannel_gid.split(':', 2)
                subchannel = ChatSubChannels.ChatSubChannel(subchannel_id, instance_uuid)
                messages, _ = subchannel._get_messages(nb=-1)
                for mess in messages:
                    _, _, message_id = mess[0].split(':', )
                    subchannel.add_correlation('message', '', message_id)

def fix_chats_with_messages():
    for instance_uuid in get_chat_service_instances():
        for chat_id in ChatServiceInstance(instance_uuid).get_chats():
            chat = Chats.Chat(chat_id, instance_uuid)

            messages = chat.get_nb_messages()
            if messages > 0:
                chat.add_chat_with_messages()
                continue

            for subchannel_gid in chat.get_subchannels():
                _, _, subchannel_id = subchannel_gid.split(':', 2)
                subchannel = ChatSubChannels.ChatSubChannel(subchannel_id, instance_uuid)
                if subchannel.get_nb_messages() > 0:
                    chat.add_chat_with_messages()
                    break

#### API ####

def get_chat_user_account_label(chat_gid):
    label = None
    obj_type, subtype, obj_id = chat_gid.split(':', 2)
    if obj_type == 'chat':
        obj = get_obj_chat(obj_type, subtype, obj_id)
        username = obj.get_username()
        if username:
            username = username.split(':', 2)[2]
        name = obj.get_name()
        if username and name:
            label = f'{username} - {name}'
        elif username:
            label = username
        elif name:
            label = name

    elif obj_type == 'user-account':
        obj = UsersAccount.UserAccount(obj_id, subtype)
        username = obj.get_username()
        if username:
            username = username.split(':', 2)[2]
        name = obj.get_name()
        if username and name:
            label = f'{username} - {name}'
        elif username:
            label = username
        elif name:
            label = name
    return label

def enrich_chat_relationships_labels(relationships):
    meta = {}
    for row in relationships:
        if row['source'] not in meta:
            label = get_chat_user_account_label(row['source'])
            if label:
                meta[row['source']] = label
            else:
                meta[row['source']] = row['source']

        if row['target'] not in meta:
            label = get_chat_user_account_label(row['target'])
            if label:
                meta[row['target']] = label
            else:
                meta[row['target']] = row['target']
    return meta

def api_get_chat_service_instance(chat_instance_uuid):
    chat_instance = ChatServiceInstance(chat_instance_uuid)
    if not chat_instance.exists():
        return {"status": "error", "reason": "Unknown uuid"}, 404
    # return chat_instance.get_meta({'chats'}), 200
    return chat_instance.get_meta({'chats_with_messages'}), 200

def api_get_chats_selector():
    selector = []
    for instance_uuid in get_chat_service_instances():
        for chat_id in ChatServiceInstance(instance_uuid).get_chats():
            chat = Chats.Chat(chat_id, instance_uuid)
            selector.append({'id': chat.get_global_id(), 'name': f'{chat.get_chat_instance()}: {chat.get_label()}'})
    return selector

def api_get_chat(chat_id, chat_instance_uuid, translation_target=None, nb=-1, page=-1, messages=True, message=None, heatmap=False):
    chat = Chats.Chat(chat_id, chat_instance_uuid)
    if not chat.exists():
        return {"status": "error", "reason": "Unknown chat"}, 404
    # print(chat.get_obj_language_stats())
    meta = chat.get_meta({'created_at', 'icon', 'info', 'nb_participants', 'subchannels', 'tags_safe', 'threads', 'translation', 'username'}, translation_target=translation_target)
    if meta['username']:
        meta['username'] = get_username_meta_from_global_id(meta['username'])
    if meta['subchannels']:
        meta['subchannels'] = get_subchannels_meta_from_global_id(meta['subchannels'], translation_target=translation_target)
    else:
        if translation_target not in Language.get_translation_languages():
            translation_target = None
        if messages:
            meta['messages'], meta['pagination'], meta['tags_messages'] = chat.get_messages(translation_target=translation_target, message=message, nb=nb, page=page)
            meta['messages'] = get_chat_object_messages_meta(meta['messages'])
    if heatmap:
        meta['years'] = chat.get_message_years()
    return meta, 200

def api_get_nb_message_by_week(chat_type, chat_instance_uuid, chat_id):
    chat = get_obj_chat(chat_type, chat_instance_uuid, chat_id)
    if not chat.exists():
        return {"status": "error", "reason": "Unknown chat"}, 404
    week = chat.get_nb_message_this_week()
    # week = chat.get_nb_message_by_week('20231109')
    return week, 200

def api_get_nb_week_messages(chat_type, chat_instance_uuid, chat_id):
    chat = get_obj_chat(chat_type, chat_instance_uuid, chat_id)
    if not chat.exists():
        return {"status": "error", "reason": "Unknown chat"}, 404
    week = chat.get_nb_week_messages()
    return week, 200

def api_get_nb_year_messages(chat_type, chat_instance_uuid, chat_id, year):
    chat = get_obj_chat(chat_type, chat_instance_uuid, chat_id)
    if not chat.exists():
        return {"status": "error", "reason": "Unknown chat"}, 404
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = datetime.now().year
    nb_max, nb = chat.get_nb_year_messages(year)
    nb = [[date, value] for date, value in nb.items()]
    return {'max': nb_max, 'nb': nb, 'year': year}, 200

def api_get_languages_stats(chat_type, chat_instance_uuid, chat_id):
    chat = get_obj_chat(chat_type, chat_instance_uuid, chat_id)
    if not chat.exists():
        return {"status": "error", "reason": "Unknown chat"}, 404
    stats = chat.get_obj_language_stats()
    langs = []
    for stat in stats:
        langs.append({'name': Language.get_language_from_iso(stat[0]), 'value': int(stat[1])})
    return langs


def api_get_chat_participants(chat_type, chat_subtype, chat_id):
    if chat_type not in ['chat', 'chat-subchannel', 'chat-thread']:
        return {"status": "error", "reason": "Unknown chat type"}, 400
    chat_obj = get_obj_chat(chat_type, chat_subtype, chat_id)
    if not chat_obj.exists():
        return {"status": "error", "reason": "Unknown chat"}, 404
    else:
        meta = get_obj_chat_meta(chat_obj, new_options={'participants'})
        chat_participants = []
        for participant in meta['participants']:
            user_account = UsersAccount.UserAccount(participant['id'], participant['subtype'])
            user_account_meta = user_account.get_meta({'icon', 'info', 'username'})
            user_account_meta['nb_messages'] = user_account.get_nb_messages_by_chat_obj(chat_obj)
            chat_participants.append(user_account_meta)
        meta['participants'] = chat_participants
        return meta, 200

def api_get_subchannel(chat_id, chat_instance_uuid, translation_target=None, message=None, nb=-1, page=-1):
    subchannel = ChatSubChannels.ChatSubChannel(chat_id, chat_instance_uuid)
    if not subchannel.exists():
        return {"status": "error", "reason": "Unknown subchannel"}, 404
    # print(subchannel.get_obj_language_stats())
    meta = subchannel.get_meta({'chat', 'created_at', 'icon', 'nb_messages', 'nb_participants', 'threads', 'translation'}, translation_target=translation_target)
    if meta['chat']:
        meta['chat'] = get_chat_meta_from_global_id(meta['chat'])
    if meta.get('threads'):
        meta['threads'] = get_threads_metas(meta['threads'])
    if meta.get('username'):
        meta['username'] = get_username_meta_from_global_id(meta['username'])
    meta['messages'], meta['pagination'], meta['tags_messages'] = subchannel.get_messages(translation_target=translation_target, message=message, nb=nb, page=page)
    meta['messages'] = get_chat_object_messages_meta(meta['messages'])
    return meta, 200

def api_get_thread(thread_id, thread_instance_uuid, translation_target=None, message=None, nb=-1, page=-1):
    thread = ChatThreads.ChatThread(thread_id, thread_instance_uuid)
    if not thread.exists():
        return {"status": "error", "reason": "Unknown thread"}, 404
    # print(thread.get_obj_language_stats())
    meta = thread.get_meta({'chat', 'nb_messages', 'nb_participants'})
    # if meta['chat']:
    #     meta['chat'] = get_chat_meta_from_global_id(meta['chat'])
    meta['messages'], meta['pagination'], meta['tags_messages'] = thread.get_messages(translation_target=translation_target, message=message, nb=nb, page=page)
    meta['messages'] = get_chat_object_messages_meta(meta['messages'])
    return meta, 200

def api_get_message(message_id, translation_target=None):
    message = Messages.Message(message_id)
    if not message.exists():
        return {"status": "error", "reason": "Unknown uuid"}, 404
    meta = message.get_meta({'barcodes', 'chat', 'container', 'content', 'files', 'files-names', 'forwarded_from', 'icon', 'images', 'language', 'link', 'parent', 'parent_meta', 'qrcodes', 'reactions', 'thread', 'translation', 'user-account'}, translation_target=translation_target)
    if 'forwarded_from' in meta:
        chat = get_obj_chat_from_global_id(meta['forwarded_from'])
        meta['forwarded_from'] = chat.get_meta({'icon'})
    barcodes = []
    for q in meta['barcodes']:
        obj = Barcode(q)
        barcodes.append({'id': obj.id, 'content': obj.get_content(), 'tags': obj.get_tags()})
    meta['barcodes'] = barcodes
    qrcodes = []
    for q in meta['qrcodes']:
        qr = Qrcode(q)
        qrcodes.append({'id': qr.id, 'content': qr.get_content(), 'tags': qr.get_tags()})
    meta['qrcodes'] = qrcodes
    return meta, 200

def api_message_detect_language(message_id):
    message = Messages.Message(message_id)
    if not message.exists():
        return {"status": "error", "reason": "Unknown uuid"}, 404
    lang = message.detect_language()
    return {"language": lang}, 200

def api_manually_translate_message(message_id, source, translation_target, translation):
    message = Messages.Message(message_id)
    if not message.exists():
        return {"status": "error", "reason": "Unknown uuid"}, 404
    if translation:
        if len(translation) > 200000: # TODO REVIEW LIMIT
            return {"status": "error", "reason": "Max Size reached"}, 400
    all_languages = Language.get_translation_languages()
    if source not in all_languages:
        return {"status": "error", "reason": "Unknown source Language"}, 400
    message_language = message.get_language()
    if message_language != source:
        message.edit_language(message_language, source)
    if translation:
        if translation_target not in all_languages:
            return {"status": "error", "reason": "Unknown target Language"}, 400
        message.set_translation(translation_target, translation)
    # TODO SANITYZE translation
    return None, 200

def api_get_user_account(user_id, instance_uuid, translation_target=None):
    user_account = UsersAccount.UserAccount(user_id, instance_uuid)
    if not user_account.exists():
        return {"status": "error", "reason": "Unknown user-account"}, 404
    meta = user_account.get_meta({'chats', 'icon', 'info', 'subchannels', 'threads', 'translation', 'username', 'usernames', 'username_meta', 'years'}, translation_target=translation_target)
    if meta['chats']:
        meta['chats'] = get_user_account_chats_meta(user_id, meta['chats'], meta['subchannels'])
    return meta, 200

def api_get_user_account_chat_messages(user_id, instance_uuid, chat_id, translation_target=None):
    user_account = UsersAccount.UserAccount(user_id, instance_uuid)
    if not user_account.exists():
        return {"status": "error", "reason": "Unknown user-account"}, 404
    meta = get_user_account_chat_message(user_id, instance_uuid, chat_id)
    meta['user-account'] = user_account.get_meta({'icon', 'info', 'translation', 'username', 'username_meta'}, translation_target=translation_target)
    resp = api_get_chat(chat_id, instance_uuid, translation_target=translation_target, messages=False)
    if resp[1] != 200:
        return resp
    meta['chat'] = resp[0]
    return meta, 200

def api_get_user_account_nb_all_week_messages(user_id, instance_uuid):
    user_account = UsersAccount.UserAccount(user_id, instance_uuid)
    if not user_account.exists():
        return {"status": "error", "reason": "Unknown user-account"}, 404
    week = get_user_account_nb_all_week_messages(user_account.id, user_account.get_chats(), user_account.get_chat_subchannels())
    return week, 200

def api_get_user_account_nb_year_messages(user_id, instance_uuid, year):
    user_account = UsersAccount.UserAccount(user_id, instance_uuid)
    if not user_account.exists():
        return {"status": "error", "reason": "Unknown user-account"}, 404
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = datetime.now().year
    nb_max, nb = get_user_account_nb_year_messages(user_account.id, user_account.get_chats(), year)
    nb = [[date, value] for date, value in nb.items()]
    return {'max': nb_max, 'nb': nb, 'year': year}, 200

def api_chat_messages(subtype, chat_id):
    chat = Chats.Chat(chat_id, subtype)
    if not chat.exists():
        return {"status": "error", "reason": "Unknown chat"}, 404
    meta = chat.get_meta({'created_at', 'info', 'nb_participants', 'subchannels', 'threads', 'username'})  # 'icon' 'translation'
    if meta['username']:
        meta['username'] = get_username_meta_from_global_id(meta['username'])
    if meta['subchannels']:
        meta['subchannels'] = get_subchannels_meta_from_global_id(meta['subchannels'])
    else:
        options = {'content', 'files', 'files-names', 'images', 'link', 'parent', 'parent_meta', 'reactions', 'thread', 'user-account'}
        meta['messages'], _, _ = chat.get_messages(nb=-1, options=options)
    return meta, 200

def api_subchannel_messages(subtype, subchannel_id):
    subchannel = ChatSubChannels.ChatSubChannel(subchannel_id, subtype)
    if not subchannel.exists():
        return {"status": "error", "reason": "Unknown subchannel"}, 404
    meta = subchannel.get_meta(
        {'chat', 'created_at', 'nb_messages', 'nb_participants', 'threads'})
    if meta['chat']:
        meta['chat'] = get_chat_meta_from_global_id(meta['chat'])
    if meta.get('threads'):
        meta['threads'] = get_threads_metas(meta['threads'])
    if meta.get('username'):
        meta['username'] = get_username_meta_from_global_id(meta['username'])
    options = {'content', 'files', 'files-names', 'images', 'link', 'parent', 'parent_meta', 'reactions', 'thread', 'user-account'}
    meta['messages'], _, _ = subchannel.get_messages(nb=-1, options=options)
    return meta, 200

def api_thread_messages(subtype, thread_id):
    thread = ChatThreads.ChatThread(thread_id, subtype)
    if not thread.exists():
        return {"status": "error", "reason": "Unknown thread"}, 404
    meta = thread.get_meta({'chat', 'nb_messages', 'nb_participants'})
    options = {'content', 'files', 'files-names', 'images', 'link', 'parent', 'parent_meta', 'reactions', 'thread', 'user-account'}
    meta['messages'], _, _ = thread.get_messages(nb=-1, options=options)
    return meta, 200

# # # # # # # # # # LATER
#                 #
#   ChatCategory  #
#                 #
# # # # # # # # # #


if __name__ == '__main__':
    get_messages_iterator(filters={'tags': ['infoleak:automatic-detection="cve"']})
    # r = get_chat_service_instances()
    # print(r)
    # r = ChatServiceInstance(r.pop())
    # print(r.get_meta({'chats'}))
    # r = get_chat_protocols()
    # print(r)
