#!/usr/bin/python3

"""
Chats Viewer
===================


"""
import os
import sys
import time
import uuid


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects import Chats
from lib.objects import ChatSubChannels
from lib.objects import ChatThreads
from lib.objects import Messages
from lib.objects import UsersAccount
from lib.objects import Usernames
from lib import Language

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
        return meta

    def get_nb_chats(self):
        return Chats.Chats().get_nb_ids_by_subtype(self.uuid)

    def get_chats(self):
        return Chats.Chats().get_ids_by_subtype(self.uuid)

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
    return username.get_meta()

#### API ####

def api_get_chat_service_instance(chat_instance_uuid):
    chat_instance = ChatServiceInstance(chat_instance_uuid)
    if not chat_instance.exists():
        return {"status": "error", "reason": "Unknown uuid"}, 404
    return chat_instance.get_meta({'chats'}), 200

def api_get_chat(chat_id, chat_instance_uuid, translation_target=None, nb=-1, page=-1):
    chat = Chats.Chat(chat_id, chat_instance_uuid)
    if not chat.exists():
        return {"status": "error", "reason": "Unknown chat"}, 404
    meta = chat.get_meta({'created_at', 'icon', 'info', 'nb_participants', 'subchannels', 'threads', 'translation', 'username'}, translation_target=translation_target)
    if meta['username']:
        meta['username'] = get_username_meta_from_global_id(meta['username'])
    if meta['subchannels']:
        meta['subchannels'] = get_subchannels_meta_from_global_id(meta['subchannels'], translation_target=translation_target)
    else:
        if translation_target not in Language.get_translation_languages():
            translation_target = None
        meta['messages'], meta['pagination'], meta['tags_messages'] = chat.get_messages(translation_target=translation_target, nb=nb, page=page)
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
            chat_participants.append(user_account.get_meta({'icon', 'info', 'username'}))
        meta['participants'] = chat_participants
        return meta, 200

def api_get_subchannel(chat_id, chat_instance_uuid, translation_target=None, nb=-1, page=-1):
    subchannel = ChatSubChannels.ChatSubChannel(chat_id, chat_instance_uuid)
    if not subchannel.exists():
        return {"status": "error", "reason": "Unknown subchannel"}, 404
    meta = subchannel.get_meta({'chat', 'created_at', 'icon', 'nb_messages', 'nb_participants', 'threads', 'translation'}, translation_target=translation_target)
    if meta['chat']:
        meta['chat'] = get_chat_meta_from_global_id(meta['chat'])
    if meta.get('threads'):
        meta['threads'] = get_threads_metas(meta['threads'])
    if meta.get('username'):
        meta['username'] = get_username_meta_from_global_id(meta['username'])
    meta['messages'], meta['pagination'], meta['tags_messages'] = subchannel.get_messages(translation_target=translation_target, nb=nb, page=page)
    return meta, 200

def api_get_thread(thread_id, thread_instance_uuid, translation_target=None, nb=-1, page=-1):
    thread = ChatThreads.ChatThread(thread_id, thread_instance_uuid)
    if not thread.exists():
        return {"status": "error", "reason": "Unknown thread"}, 404
    meta = thread.get_meta({'chat', 'nb_messages', 'nb_participants'})
    # if meta['chat']:
    #     meta['chat'] = get_chat_meta_from_global_id(meta['chat'])
    meta['messages'], meta['pagination'], meta['tags_messages'] = thread.get_messages(translation_target=translation_target, nb=nb, page=page)
    return meta, 200

def api_get_message(message_id, translation_target=None):
    message = Messages.Message(message_id)
    if not message.exists():
        return {"status": "error", "reason": "Unknown uuid"}, 404
    meta = message.get_meta({'chat', 'content', 'files-names', 'icon', 'images', 'language', 'link', 'parent', 'parent_meta', 'reactions', 'thread', 'translation', 'user-account'}, translation_target=translation_target)
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
        print(source)
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
    meta = user_account.get_meta({'chats', 'icon', 'info', 'subchannels', 'threads', 'translation', 'username', 'username_meta'}, translation_target=translation_target)
    return meta, 200

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
        options = {'content', 'files-names', 'images', 'link', 'parent', 'parent_meta', 'reactions', 'thread', 'user-account'}
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
    options = {'content', 'files-names', 'images', 'link', 'parent', 'parent_meta', 'reactions', 'thread', 'user-account'}
    meta['messages'], _, _ = subchannel.get_messages(nb=-1, options=options)
    return meta, 200

def api_thread_messages(subtype, thread_id):
    thread = ChatThreads.ChatThread(thread_id, subtype)
    if not thread.exists():
        return {"status": "error", "reason": "Unknown thread"}, 404
    meta = thread.get_meta({'chat', 'nb_messages', 'nb_participants'})
    options = {'content', 'files-names', 'images', 'link', 'parent', 'parent_meta', 'reactions', 'thread', 'user-account'}
    meta['messages'], _, _ = thread.get_messages(nb=-1, options=options)
    return meta, 200

# # # # # # # # # # LATER
#                 #
#   ChatCategory  #
#                 #
# # # # # # # # # #


if __name__ == '__main__':
    r = get_chat_service_instances()
    print(r)
    r = ChatServiceInstance(r.pop())
    print(r.get_meta({'chats'}))
    # r = get_chat_protocols()
    # print(r)