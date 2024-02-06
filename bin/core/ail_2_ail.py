#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import json
import secrets
import re
import sys
import time
import uuid

import subprocess

from markupsafe import escape

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader
from lib.objects.Items import Item
# from lib import Tag
from core import screen

config_loader = ConfigLoader.ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
r_serv_sync = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

WEBSOCKETS_CLOSE_CODES = {
                            1000: 'Normal Closure',
                            1001: 'Going Away',
                            1002: 'Protocol Error',
                            1003: 'Unsupported Data',
                            1005: 'No Status Received',
                            1006: 'Abnormal Closure',
                            1007: 'Invalid frame payload data',
                            1008: 'Policy Violation',
                            1009: 'Message too big',
                            1010: 'Missing Extension',
                            1011: 'Internal Error',
                            1012: 'Service Restart',
                            1013: 'Try Again Later',
                            1014: 'Bad Gateway',
                            1015: 'TLS Handshake',
                        }

def get_websockets_close_message(code):
    if code in WEBSOCKETS_CLOSE_CODES:
        msg = f'{code} {WEBSOCKETS_CLOSE_CODES[code]}'
    else:
        msg = f'{code} Unknow websockets code'
    return msg

##-- LOGS --##

def is_valid_uuid_v4(UUID):
    if not UUID:
        return False
    UUID = UUID.replace('-', '')
    try:
        uuid_test = uuid.UUID(hex=UUID, version=4)
        return uuid_test.hex == UUID
    except:
        return False

def sanityze_uuid(UUID):
    sanityzed_uuid = uuid.UUID(hex=UUID, version=4)
    return str(sanityzed_uuid)

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')

def generate_sync_api_key():
    return secrets.token_urlsafe(42)

def get_ail_uuid():
    return r_serv_db.get('ail:uuid')

def get_sync_server_version():
    return '0.1'

def is_valid_websocket_url(websocket_url):
    regex_websocket_url = r'^(wss:\/\/)([0-9]{1,3}(?:\.[0-9]{1,3}){3}|(?=[^\/]{1,254}(?![^\/]))(?:(?=[a-zA-Z0-9-]{1,63}\.?)(?:xn--+)?[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\.?)+[a-zA-Z]{2,63}):([0-9]{1,5})$'
    if re.match(regex_websocket_url, websocket_url):
        return True
    return False

def is_valid_websocket_key(ail_key):
    regex_key = r'^[A-Za-z0-9-_]{56}$'
    if re.match(regex_key, ail_key):
        return True
    return False

#### HANDLE CONFIG UPDATE ####

def get_last_updated_sync_config():
    epoch = r_serv_sync.get(f'ail:instance:queue:last_updated_sync_config')
    if not epoch:
        epoch = 0
    return float(epoch)

def set_last_updated_sync_config():
    epoch = int(time.time())
    r_serv_sync.set(f'ail:instance:queue:last_updated_sync_config', epoch)
    return epoch

# # TODO: get connection status
# # TODO: get connection METADATA
# # TODO: client => reconnect on fails (with timeout)

# # TODO: API KEY change => trigger kill connection
#############################
#                           #
#### SYNC CLIENT MANAGER ####

#### ail servers connected clients ####
#
#   ail_uuid => WEBSOCKETS => ail_uuid
#   AIL: clients:
#               - 1 push
#               - 1 pull
#               - N api

def get_server_all_connected_clients():
    return r_cache.smembers('ail_2_ail:server:all_clients')

def add_server_connected_client(ail_uuid, sync_mode):
    r_cache.sadd('ail_2_ail:server:all_clients', ail_uuid)
    r_cache.hset(f'ail_2_ail:server:client:{ail_uuid}', sync_mode, True)

def remove_server_connected_client(ail_uuid, sync_mode=None, is_connected=False):
    if sync_mode:
        r_cache.hdel(f'ail_2_ail:server:client:{ail_uuid}', sync_mode)
    if not is_connected:
        r_cache.srem('ail_2_ail:server:all_clients', ail_uuid)

def is_server_client_sync_mode_connected(ail_uuid, sync_mode):
    res = r_cache.hexists(f'ail_2_ail:server:client:{ail_uuid}', sync_mode)
    return res == 1

def is_server_client_connected(ail_uuid):
    try:
        return r_cache.sismember('ail_2_ail:server:all_clients', ail_uuid)
    except:
        return False

def clear_server_connected_clients():
    for ail_uuid in get_server_all_connected_clients():
        r_cache.delete(f'ail_2_ail:server:client:{ail_uuid}')
    r_cache.delete('ail_2_ail:server:all_clients')

def get_server_controller_command():
    res = r_cache.spop('ail_2_ail:server_controller:command')
    if res:
        return json.loads(res)
    else:
        return None

# command: -kill
#          -killall or shutdown / restart ?
## TODO: ADD command
def send_command_to_server_controller(command, ail_uuid=None):
    dict_action = {'command': command, 'ail_uuid': ail_uuid}
    if ail_uuid:
        dict_action['ail_uuid'] = ail_uuid
    str_command = json.dumps(dict_action)
    r_cache.sadd('ail_2_ail:server_controller:command', str_command)

##-- --##
def get_new_sync_client_id():
    for new_id in range(120000, 100000, -1):
        new_id = str(new_id)
        if not r_cache.exists(f'ail_2_ail:sync_client:{new_id}'):
            return str(new_id)

def get_all_sync_clients(r_set=False):
    res = r_cache.smembers('ail_2_ail:all_sync_clients')
    if r_set:
        return set(res)
    else:
        return res

def get_sync_client_ail_uuid(client_id):
    return r_cache.hget(f'ail_2_ail:sync_client:{client_id}', 'ail_uuid')

def get_sync_client_sync_mode(client_id):
    return r_cache.hget(f'ail_2_ail:sync_client:{client_id}', 'sync_mode')

def set_sync_client_sync_mode(client_id, sync_mode):
    r_cache.hset(f'ail_2_ail:sync_client:{client_id}', 'sync_mode', sync_mode)

def create_sync_client_cache(ail_uuid, sync_mode, client_id=None):
    if client_id is None:
        client_id = get_new_sync_client_id()
    # save sync client status
    r_cache.hset(f'ail_2_ail:sync_client:{client_id}', 'ail_uuid', ail_uuid)
    r_cache.hset(f'ail_2_ail:sync_client:{client_id}', 'launch_time', int(time.time()))
    set_sync_client_sync_mode(client_id, sync_mode)

    r_cache.sadd('ail_2_ail:all_sync_clients', client_id)

    # create map ail_uuid/queue_uuid
    r_cache.sadd(f'ail_2_ail:ail_uuid:{ail_uuid}', client_id)
    return client_id

# current: only one push registred
def get_client_id_by_ail_uuid(ail_uuid, filter_push=True):
    res = r_cache.smembers(f'ail_2_ail:ail_uuid:{ail_uuid}')
    if not filter_push:
        return res
    else:
        clients_id = []
        for client_id in res:
            client_id = int(client_id)
            if client_id <= 100000:
                clients_id.append(client_id)
        return clients_id

def get_all_running_sync_servers():
    running_ail_servers= []
    for client_id in get_all_sync_clients():
        ail_uuid = get_sync_client_ail_uuid(client_id)
        running_ail_servers.append(ail_uuid)
    return running_ail_servers

def get_ail_instance_all_running_sync_mode(ail_uuid):
    clients_id = get_client_id_by_ail_uuid(ail_uuid, filter_push=False)
    running_sync_mode = {'api': False, 'pull': False, 'push': False}
    for client_id in clients_id:
        sync_mode = get_sync_client_sync_mode(client_id)
        running_sync_mode[sync_mode] = True
    return running_sync_mode

def delete_sync_client_cache(client_id):
    ail_uuid = get_sync_client_ail_uuid(client_id)
    # map ail_uuid
    r_cache.srem(f'ail_2_ail:ail_uuid:{ail_uuid}', client_id)

    r_cache.delete(f'ail_2_ail:sync_client:{client_id}')
    r_cache.srem('ail_2_ail:all_sync_clients', client_id)

def delete_all_sync_clients_cache():
    for client_id in get_all_sync_clients():
        delete_sync_client_cache(client_id)
    r_cache.delete('ail_2_ail:all_sync_clients')

# command: -launch
#          -kill
#          -relaunch
## TODO: check command
def send_command_to_manager(command, client_id=-1, ail_uuid=None):
    dict_action = {'command': command, 'client_id': client_id}
    if ail_uuid:
        dict_action['ail_uuid'] = ail_uuid
    str_command = json.dumps(dict_action)
    r_cache.sadd('ail_2_ail:client_manager:command', str_command)

def refresh_ail_instance_connection(ail_uuid):
    clients_id = get_client_id_by_ail_uuid(ail_uuid)
    if clients_id:
        client_id = clients_id[0]
    else:
        client_id = None
    launch_required = is_ail_instance_push_enabled(ail_uuid) and is_ail_instance_linked_to_sync_queue(ail_uuid)

    # relaunch
    if client_id and launch_required:
        send_command_to_manager('relaunch', client_id=client_id)
    # kill
    elif client_id:
        send_command_to_manager('kill', client_id=client_id)
    # launch
    elif launch_required:
        send_command_to_manager('launch', ail_uuid=ail_uuid)


class AIL2AILClientManager(object):
    """AIL2AILClientManager."""

    SCREEN_NAME = 'AIL_2_AIL'
    SCRIPT_NAME = 'ail_2_ail_client.py'
    SCRIPT_DIR = os.path.join(os.environ['AIL_BIN'], 'core')

    def __init__(self):
        # dict client_id: AIL2AILCLIENT or websocket
        self.clients = {}
        # launch all sync clients
        self.relaunch_all_sync_clients()

    def get_all_clients(self):
        return self.clients

    # return new client id
    def get_new_sync_client_id(self):
        for new_id in range(1, 100000):
            new_id = str(new_id)
            if new_id not in self.clients:
                return str(new_id)

    def get_sync_client_ail_uuid(self, client_id):
        return self.clients[client_id]['ail_uuid']

    # def get_sync_client_queue_uuid(self, client_id):
    #     return self.clients[client_id]['queue_uuid']

    def get_all_sync_clients_to_launch(self):
        ail_instances_to_launch = []
        for ail_uuid in get_all_ail_instance():
            if is_ail_instance_push_enabled(ail_uuid) and is_ail_instance_linked_to_sync_queue(ail_uuid):
                ail_instances_to_launch.append(ail_uuid)
        return ail_instances_to_launch

    def relaunch_all_sync_clients(self):
        delete_all_sync_clients_cache()
        self.clients = {}
        for ail_uuid in self.get_all_sync_clients_to_launch():
             self.launch_sync_client(ail_uuid)

    def launch_sync_client(self, ail_uuid):
        dir_project = os.environ['AIL_HOME']
        sync_mode = 'push'
        client_id = self.get_new_sync_client_id()
        script_options = f'-u {ail_uuid} -m push -i {client_id}'
        screen.create_screen(AIL2AILClientManager.SCREEN_NAME)
        screen.launch_uniq_windows_script(AIL2AILClientManager.SCREEN_NAME,
                                            client_id, dir_project,
                                            AIL2AILClientManager.SCRIPT_DIR,
                                            AIL2AILClientManager.SCRIPT_NAME,
                                            script_options=script_options, kill_previous_windows=True)
        # save sync client status
        create_sync_client_cache(ail_uuid, sync_mode, client_id=client_id)

        self.clients[client_id] = {'ail_uuid': ail_uuid}

    # # TODO: FORCE KILL ????????????
    # # TODO: check if exists
    def kill_sync_client(self, client_id):
        if not screen.kill_screen_window('AIL_2_AIL',client_id):
            # # TODO: log kill error
            pass

        delete_sync_client_cache(client_id)
        self.clients.pop(client_id)

    ## COMMANDS ##

    def get_manager_command(self):
        res = r_cache.spop('ail_2_ail:client_manager:command')
        if res:
            return json.loads(res)
        else:
            return None

    def execute_manager_command(self, command_dict):
        command = command_dict.get('command')
        if command == 'launch':
            ail_uuid = command_dict.get('ail_uuid')
            self.launch_sync_client(ail_uuid)
        elif command == 'relaunch_all':
            self.relaunch_all_sync_clients()
        else:
            # only one sync client
            client_id = int(command_dict.get('client_id'))
            if client_id < 1:
                print('Invalid client id')
                return None
            client_id = str(client_id)
            if command == 'kill':
                self.kill_sync_client(client_id)
            elif command == 'relaunch':
                ail_uuid = self.get_sync_client_ail_uuid(client_id)
                self.kill_sync_client(client_id)
                self.launch_sync_client(ail_uuid)

########################################
########################################
########################################

# # TODO: ADD METADATA
def get_sync_client_status(client_id):
    dict_client = {'id': client_id}
    dict_client['ail_uuid'] = get_sync_client_ail_uuid(client_id)
    return dict_client

def get_all_sync_client_status():
    sync_clients = []
    all_sync_clients = r_cache.smembers('ail_2_ail:all_sync_clients')
    for client_id in all_sync_clients:
        sync_clients.append(get_sync_client_status(client_id))
    return sync_clients

######################
#                    #
#### AIL INSTANCE ####

## AIL KEYS ##

def get_all_ail_instance_keys():
    return r_serv_sync.smembers(f'ail:instance:key:all')

def is_allowed_ail_instance_key(key):
    try:
        return r_serv_sync.sismember(f'ail:instance:key:all', key)
    except:
        return False

def get_ail_instance_key(ail_uuid):
    return r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'api_key')

def get_ail_instance_by_key(key):
    return r_serv_sync.get(f'ail:instance:key:{key}')

# def check_acl_sync_queue_ail(ail_uuid, queue_uuid, key):
#     return is_ail_instance_queue(ail_uuid, queue_uuid)

# def update_ail_instance_key(ail_uuid, new_key):
#     old_key = get_ail_instance_key(ail_uuid)
#     r_serv_sync.srem(f'ail:instance:key:all', old_key)
#     r_serv_sync.delete(f'ail:instance:key:{old_key}')
#
#     r_serv_sync.sadd(f'ail:instance:key:all', new_key)
#     r_serv_sync.delete(f'ail:instance:key:{new_key}', ail_uuid)
#     r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'api_key', new_key)

#- AIL KEYS -#

def get_all_ail_instance():
    return r_serv_sync.smembers('ail:instance:all')

def get_ail_instance_all_sync_queue(ail_uuid):
    return r_serv_sync.smembers(f'ail:instance:sync_queue:{ail_uuid}')

def is_ail_instance_queue(ail_uuid, queue_uuid):
    try:
        return r_serv_sync.sismember(f'ail:instance:sync_queue:{ail_uuid}', queue_uuid)
    except:
        return False

def exists_ail_instance(ail_uuid):
    return r_serv_sync.exists(f'ail:instance:{ail_uuid}')

def get_ail_instance_url(ail_uuid):
    return r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'url')

def get_ail_instance_description(ail_uuid):
    return r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'description')

def exists_ail_instance(ail_uuid):
    try:
        return r_serv_sync.sismember('ail:instance:all', ail_uuid)
    except:
        return False

def is_ail_instance_push_enabled(ail_uuid):
    res = r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'push')
    return res == 'True'

def is_ail_instance_pull_enabled(ail_uuid):
    res = r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'pull')
    return res == 'True'

def is_ail_instance_sync_enabled(ail_uuid, sync_mode=None):
    if sync_mode is None:
        return is_ail_instance_push_enabled(ail_uuid) or is_ail_instance_pull_enabled(ail_uuid)
    elif sync_mode == 'pull':
        return is_ail_instance_pull_enabled(ail_uuid)
    elif sync_mode == 'push':
        return is_ail_instance_push_enabled(ail_uuid)
    else:
        return False

def is_ail_instance_linked_to_sync_queue(ail_uuid):
    return r_serv_sync.exists(f'ail:instance:sync_queue:{ail_uuid}')

def change_pull_push_state(ail_uuid, pull=None, push=None):
    edited = False
    curr_pull = is_ail_instance_pull_enabled(ail_uuid)
    curr_push = is_ail_instance_push_enabled(ail_uuid)
    if pull is not None:
        # sanityze pull
        if pull:
            pull = True
        else:
            pull = False
        if curr_pull != pull:
            #print('pull hset')
            r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'pull', pull)
            edited = True
    if push is not None:
        # sanityze push
        if push:
            push = True
        else:
            push = False
        if curr_push != push:
            #print('push hset')
            r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'push', push)
            edited = True
    if edited:
        set_last_updated_sync_config()
        refresh_ail_instance_connection(ail_uuid)

def get_ail_server_version(ail_uuid):
    return r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'version')

def get_ail_server_ping(ail_uuid):
    res = r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'ping')
    return res == 'True'

def get_ail_server_error(ail_uuid):
    return r_cache.hget(f'ail_2_ail:all_servers:metadata:{ail_uuid}', 'error')

# # TODO: HIDE ADD GLOBAL FILTER (ON BOTH SIDE)
def get_ail_instance_metadata(ail_uuid, client_sync_mode=False, server_sync_mode=False, sync_queues=False):
    dict_meta = {}
    dict_meta['uuid'] = ail_uuid
    dict_meta['url'] = get_ail_instance_url(ail_uuid)
    dict_meta['description'] = get_ail_instance_description(ail_uuid)
    dict_meta['pull'] = is_ail_instance_pull_enabled(ail_uuid)
    dict_meta['push'] = is_ail_instance_push_enabled(ail_uuid)
    dict_meta['ping'] = get_ail_server_ping(ail_uuid)
    dict_meta['version'] = get_ail_server_version(ail_uuid)
    dict_meta['error'] = get_ail_server_error(ail_uuid)

    # # TODO: HIDE
    dict_meta['api_key'] = get_ail_instance_key(ail_uuid)

    if sync_queues:
        dict_meta['sync_queues'] = get_ail_instance_all_sync_queue(ail_uuid)

    if client_sync_mode:
        dict_meta['client_sync_mode'] = {}
        dict_meta['client_sync_mode']['pull'] = is_server_client_sync_mode_connected(ail_uuid, 'pull')
        dict_meta['client_sync_mode']['push'] = is_server_client_sync_mode_connected(ail_uuid, 'push')
        dict_meta['client_sync_mode']['api'] = is_server_client_sync_mode_connected(ail_uuid, 'api')

    if server_sync_mode:
        dict_meta['server_sync_mode'] = get_ail_instance_all_running_sync_mode(ail_uuid)

    return dict_meta

def get_all_ail_instances_metadata():
    l_servers = []
    for ail_uuid in get_all_ail_instance():
        l_servers.append(get_ail_instance_metadata(ail_uuid, sync_queues=True))
    return l_servers

def get_ail_instances_metadata(l_ail_servers, sync_queues=True, client_sync_mode=False, server_sync_mode=False):
    l_servers = []
    for ail_uuid in l_ail_servers:
        server_metadata = get_ail_instance_metadata(ail_uuid, sync_queues=sync_queues,
                                client_sync_mode=client_sync_mode, server_sync_mode=server_sync_mode)
        l_servers.append(server_metadata)
    return l_servers

def edit_ail_instance_key(ail_uuid, new_key):
    key = get_ail_instance_key(ail_uuid)
    if new_key and key != new_key:
        r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'api_key', new_key)
        r_serv_sync.srem('ail:instance:key:all', key)
        r_serv_sync.srem('ail:instance:key:all', new_key)
        r_serv_sync.delete(f'ail:instance:key:{key}')
        r_serv_sync.set(f'ail:instance:key:{new_key}', ail_uuid)
        refresh_ail_instance_connection(ail_uuid)

def edit_ail_instance_url(ail_uuid, new_url):
    url = get_ail_instance_url(ail_uuid)
    if new_url and new_url != url:
        r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'url', new_url)
        refresh_ail_instance_connection(ail_uuid)

def edit_ail_instance_pull_push(ail_uuid, new_pull, new_push):
    pull = is_ail_instance_pull_enabled(ail_uuid)
    push = is_ail_instance_push_enabled(ail_uuid)
    if new_pull == pull:
        new_pull = None
    if new_push == push:
        new_push = None
    change_pull_push_state(ail_uuid, pull=new_pull, push=new_push)

def edit_ail_instance_description(ail_uuid, new_description):
    description = get_ail_instance_description(ail_uuid)
    if new_description is not None and description != new_description:
        if not new_description:
            r_serv_sync.hdel(f'ail:instance:{ail_uuid}', 'description')
        else:
            r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'description', new_description)

# # TODO: VALIDATE URL
#                  API KEY
def create_ail_instance(ail_uuid, url, api_key=None, description=None, pull=True, push=True):
    r_serv_sync.sadd('ail:instance:all', ail_uuid)
    r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'url', url)
    ## API KEY ##
    if not api_key:
        api_key = generate_sync_api_key()
    r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'api_key', api_key)
    r_serv_sync.sadd('ail:instance:key:all', api_key)
    r_serv_sync.set(f'ail:instance:key:{api_key}', ail_uuid)
    #- API KEY -#
    if description:
        r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'description', description)
    change_pull_push_state(ail_uuid, pull=pull, push=push)
    set_last_updated_sync_config()
    refresh_ail_instance_connection(ail_uuid)
    return ail_uuid

def delete_ail_instance(ail_uuid):
    for queue_uuid in get_ail_instance_all_sync_queue(ail_uuid):
        unregister_ail_to_sync_queue(ail_uuid, queue_uuid)
    r_serv_sync.delete(f'ail:instance:sync_queue:{ail_uuid}')
    key = get_ail_instance_by_key(ail_uuid)
    r_serv_sync.delete(f'ail:instance:{ail_uuid}')
    r_serv_sync.srem('ail:instance:key:all', ail_uuid)
    r_serv_sync.delete(f'ail:instance:key:{key}', ail_uuid)
    r_serv_sync.srem('ail:instance:all', ail_uuid)
    set_last_updated_sync_config()
    refresh_ail_instance_connection(ail_uuid)
    clear_save_ail_server_error(ail_uuid)
    return ail_uuid

## WEBSOCKET API - ERRORS ##

def set_ail_server_version(ail_uuid, version):
    r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'version', version)

def set_ail_server_ping(ail_uuid, pong):
    r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'ping', bool(pong))

def save_ail_server_error(ail_uuid, error_message):
    r_cache.hset(f'ail_2_ail:all_servers:metadata:{ail_uuid}', 'error', error_message)

def clear_save_ail_server_error(ail_uuid):
    r_cache.hdel(f'ail_2_ail:all_servers:metadata:{ail_uuid}', 'error')

def _get_remote_ail_server_response(ail_uuid, api_request):
    websocket_client = os.path.join(os.environ['AIL_BIN'], 'core', 'ail_2_ail_client.py')
    l_command = ['python', websocket_client, '-u', ail_uuid, '-m', 'api', '-a', api_request]
    process = subprocess.Popen(l_command, stdout=subprocess.PIPE)
    while process.poll() is None:
        time.sleep(1)

    if process.returncode == 0:
        # Scrapy-Splash ERRORS
        if process.stderr:
            stderr = process.stderr.read().decode()
            if stderr:
                print(f'stderr: {stderr}')

        if process.stdout:
            output = process.stdout.read().decode()
            #print(output)
            if output:
                try:
                    message = json.loads(output)
                    return message
                except Exception as e:
                    print(e)
                    error = f'Error: {e}'
                    save_ail_server_error(ail_uuid, error)
                    return
    # ERROR
    else:
        if process.stderr:
            stderr = process.stderr.read().decode()
        else:
            stderr = ''
        if process.stdout:
            stdout = process.stdout.read().decode()
        else:
            stdout =''
        if stderr or stdout:
            error = f'-stderr-\n{stderr}\n-stdout-\n{stdout}'
            print(error)
            save_ail_server_error(ail_uuid, error)
            return

def get_remote_ail_server_version(ail_uuid):
    response = _get_remote_ail_server_response(ail_uuid, 'version')
    if response:
        version = response.get('version')
        if version:
            version = float(version)
            if version >= 0.1:
                set_ail_server_version(ail_uuid, version)
                return version

# # TODO: CATCH WEBSOCKETS RESPONSE CODE
def ping_remote_ail_server(ail_uuid):
    response = _get_remote_ail_server_response(ail_uuid, 'ping')
    if response:
        response = response.get('message', False)
        pong = response == 'pong'
    else:
        pong = False
    set_ail_server_ping(ail_uuid, pong)
    return pong

## API ##

def api_ping_remote_ail_server(json_dict):
    ail_uuid = json_dict.get('uuid').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404

    res = ping_remote_ail_server(ail_uuid)
    return res, 200

def api_get_remote_ail_server_version(json_dict):
    ail_uuid = json_dict.get('uuid').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404

    res = get_remote_ail_server_version(ail_uuid)
    return res, 200

def api_kill_server_connected_clients(json_dict):
    ail_uuid = json_dict.get('uuid').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404
    if not is_server_client_connected(ail_uuid):
        return {"status": "error", "reason": "Client not connected"}, 400

    res = send_command_to_server_controller('kill', ail_uuid=ail_uuid)
    return res, 200

def api_kill_sync_client(json_dict):
    ail_uuid = json_dict.get('uuid').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404

    clients_id = get_client_id_by_ail_uuid(ail_uuid)
    if not clients_id:
        return {"status": "error", "reason": "Client not connected"}, 400

    for client_id in clients_id:
        res = send_command_to_manager('kill', client_id=client_id, ail_uuid=ail_uuid)
    return res, 200

def api_launch_sync_client(json_dict):
    ail_uuid = json_dict.get('uuid').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404

    clients_id = get_client_id_by_ail_uuid(ail_uuid)
    if clients_id:
        return {"status": "error", "reason": "Client already connected"}, 400

    res = send_command_to_manager('launch', ail_uuid=ail_uuid)
    return res, 200

def api_relaunch_sync_client(json_dict):
    ail_uuid = json_dict.get('uuid').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404

    clients_id = get_client_id_by_ail_uuid(ail_uuid)
    if not clients_id:
        return {"status": "error", "reason": "Client not connected"}, 400
    for client_id in clients_id:
        res = send_command_to_manager('relaunch', client_id=client_id, ail_uuid=ail_uuid)
    return res, 200

def api_create_ail_instance(json_dict):
    ail_uuid = json_dict.get('uuid').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    if exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL uuid already exists"}, 400

    if json_dict.get('pull'):
        pull = True
    else:
        pull = False
    if json_dict.get('push'):
        push = True
    else:
        push = False
    description = json_dict.get('description')

    ail_url = json_dict.get('url').replace(' ', '')
    if not is_valid_websocket_url(ail_url):
        return {"status": "error", "reason": "Invalid websocket url"}, 400

    ail_key = json_dict.get('key')
    if ail_key:
        ail_key = ail_key.replace(' ', '')
        if not is_valid_websocket_key(ail_key):
            return {"status": "error", "reason": "Invalid websocket key"}, 400

    res = create_ail_instance(ail_uuid, ail_url, api_key=ail_key, description=description,
                                pull=pull, push=push)
    return res, 200

def api_edit_ail_instance(json_dict):
    ail_uuid = json_dict.get('uuid').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404

    pull = json_dict.get('pull')
    push = json_dict.get('push')
    if pull is not None:
        if pull:
            pull = True
        else:
            pull = False
    if push is not None:
        if push:
            push = True
        else:
            push = False
    edit_ail_instance_pull_push(ail_uuid, pull, push)

    description = json_dict.get('description')
    edit_ail_instance_description(ail_uuid, description)

    ail_url = json_dict.get('url')
    if ail_url:
        ail_url = ail_url.replace(' ', '')
        if not is_valid_websocket_url(ail_url):
            return {"status": "error", "reason": "Invalid websocket url"}, 400
        edit_ail_instance_url(ail_uuid, ail_url)

    ail_key = json_dict.get('key')
    if ail_key:
        ail_key = ail_key.replace(' ', '')
        if not is_valid_websocket_key(ail_key):
            return {"status": "error", "reason": "Invalid websocket key"}, 400
        edit_ail_instance_key(ail_uuid, ail_key)

    return ail_uuid, 200

def api_delete_ail_instance(json_dict):
    ail_uuid = json_dict.get('uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid AIL uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404

    res = delete_ail_instance(ail_uuid)
    return res, 200

####################
#                  #
#### SYNC QUEUE ####

class Sync_Queue(object): # # TODO: use for edit
    """Sync_Queue."""

    def __init__(self, uuid):
        self.uuid = uuid

def get_all_sync_queue():
    return r_serv_sync.smembers('ail2ail:sync_queue:all')

def get_sync_queue_all_ail_instance(queue_uuid):
    return r_serv_sync.smembers(f'ail2ail:sync_queue:ail_instance:{queue_uuid}')

def exists_sync_queue(queue_uuid):
    return r_serv_sync.exists(f'ail2ail:sync_queue:{queue_uuid}')

# # TODO: check if push or pull enabled ?
def is_queue_used_by_ail_instance(queue_uuid):
    return r_serv_sync.exists(f'ail2ail:sync_queue:ail_instance:{queue_uuid}')

# # TODO: add others filter
def get_sync_queue_filter(queue_uuid):
    return r_serv_sync.smembers(f'ail2ail:sync_queue:filter:tags:{queue_uuid}')

def get_sync_queue_name(queue_uuid):
    return r_serv_sync.hget(f'ail2ail:sync_queue:{queue_uuid}', 'name')

def get_sync_queue_description(queue_uuid):
    return r_serv_sync.hget(f'ail2ail:sync_queue:{queue_uuid}', 'description')

def get_sync_queue_max_size(queue_uuid):
    return r_serv_sync.hget(f'ail2ail:sync_queue:{queue_uuid}', 'max_size')

# # TODO: ADD FILTER
def get_sync_queue_metadata(queue_uuid):
    dict_meta = {}
    dict_meta['uuid'] = queue_uuid
    dict_meta['name'] = get_sync_queue_name(queue_uuid)
    dict_meta['description'] = get_sync_queue_description(queue_uuid)
    dict_meta['max_size'] = get_sync_queue_max_size(queue_uuid)
    dict_meta['tags'] = get_sync_queue_filter(queue_uuid)

    # # TODO: TO ADD:
    # - get uuid instance

    return dict_meta

def get_all_queues_metadata():
    l_queues = []
    for queue_uuid in get_all_sync_queue():
        l_queues.append(get_sync_queue_metadata(queue_uuid))
    return l_queues

def get_queues_metadata(l_queues_uuid):
    l_queues = []
    for queue_uuid in l_queues_uuid:
        l_queues.append(get_sync_queue_metadata(queue_uuid))
    return l_queues

#####################################################
def get_all_sync_queue_dict():
    dict_sync_queues = {}
    for queue_uuid in get_all_sync_queue():
        if is_queue_used_by_ail_instance(queue_uuid):
            dict_queue = {}
            dict_queue['filter'] = get_sync_queue_filter(queue_uuid)

            dict_queue['ail_instances'] = [] ############ USE DICT ?????????
            for ail_uuid in get_sync_queue_all_ail_instance(queue_uuid):
                dict_ail = {'ail_uuid': ail_uuid,
                            'pull': is_ail_instance_pull_enabled(ail_uuid),
                            'push': is_ail_instance_push_enabled(ail_uuid)}
                if dict_ail['pull'] or dict_ail['push']:
                    dict_queue['ail_instances'].append(dict_ail)
            if dict_queue['ail_instances']:
                dict_sync_queues[queue_uuid] = dict_queue
    return dict_sync_queues

def is_queue_registred_by_ail_instance(queue_uuid, ail_uuid):
    try:
        return r_serv_sync.sismember(f'ail:instance:sync_queue:{ail_uuid}', queue_uuid)
    except:
        return False

def register_ail_to_sync_queue(ail_uuid, queue_uuid):
    is_linked = is_ail_instance_linked_to_sync_queue(ail_uuid)
    r_serv_sync.sadd(f'ail2ail:sync_queue:ail_instance:{queue_uuid}', ail_uuid)
    r_serv_sync.sadd(f'ail:instance:sync_queue:{ail_uuid}', queue_uuid)
    set_last_updated_sync_config()
    if not is_linked:
        refresh_ail_instance_connection(ail_uuid)

# # # FIXME: TODO: delete sync queue ????????????????????????????????????????????????????
def unregister_ail_to_sync_queue(ail_uuid, queue_uuid):
    r_serv_sync.srem(f'ail2ail:sync_queue:ail_instance:{queue_uuid}', ail_uuid)
    r_serv_sync.srem(f'ail:instance:sync_queue:{ail_uuid}', queue_uuid)
    set_last_updated_sync_config()
    is_linked = is_ail_instance_linked_to_sync_queue(ail_uuid)
    if not is_linked:
        refresh_ail_instance_connection(ail_uuid)

def get_all_unregistred_queue_by_ail_instance(ail_uuid):
    return r_serv_sync.sdiff('ail2ail:sync_queue:all', f'ail:instance:sync_queue:{ail_uuid}')

def edit_sync_queue_name(queue_uuid, new_name):
    name = get_sync_queue_name(queue_uuid)
    if new_name and new_name != name:
        r_serv_sync.hset(f'ail2ail:sync_queue:{queue_uuid}', 'name', new_name)

def edit_sync_queue_description(queue_uuid, new_description):
    description = get_sync_queue_description(queue_uuid)
    if new_description is not None and new_description != description:
        r_serv_sync.hset(f'ail2ail:sync_queue:{queue_uuid}', 'description', new_description)

# # TODO: trigger update
def edit_sync_queue_max_size(queue_uuid, new_max_size):
    max_size = get_sync_queue_max_size(queue_uuid)
    if new_max_size > 0 and new_max_size != max_size:
        r_serv_sync.hset(f'ail2ail:sync_queue:{queue_uuid}', 'max_size', new_max_size)

def edit_sync_queue_filter_tags(queue_uuid, new_tags):
    tags = set(get_sync_queue_filter(queue_uuid))
    new_tags = set(new_tags)
    if new_tags and new_tags != tags:
        r_serv_sync.delete(f'ail2ail:sync_queue:filter:tags:{queue_uuid}')
        for tag in new_tags:
            r_serv_sync.sadd(f'ail2ail:sync_queue:filter:tags:{queue_uuid}', tag)
    set_last_updated_sync_config()

# # TODO: optionnal name ???
# # TODO: SANITYZE TAGS
# # TODO: SANITYZE queue_uuid
def create_sync_queue(name, tags=[], description=None, max_size=100, _queue_uuid=None):
    if _queue_uuid:
        queue_uuid = sanityze_uuid(_queue_uuid).replace('-', '')
    else:
        queue_uuid = generate_uuid()
    r_serv_sync.sadd('ail2ail:sync_queue:all', queue_uuid)

    r_serv_sync.hset(f'ail2ail:sync_queue:{queue_uuid}', 'name', name)
    if description:
        r_serv_sync.hset(f'ail2ail:sync_queue:{queue_uuid}', 'description', description)
    r_serv_sync.hset(f'ail2ail:sync_queue:{queue_uuid}', 'max_size', max_size)

    for tag in tags:
        r_serv_sync.sadd(f'ail2ail:sync_queue:filter:tags:{queue_uuid}', tag)

    set_last_updated_sync_config()
    return queue_uuid

def delete_sync_queue(queue_uuid):
    for ail_uuid in get_sync_queue_all_ail_instance(queue_uuid):
        unregister_ail_to_sync_queue(ail_uuid, queue_uuid)
    r_serv_sync.delete(f'ail2ail:sync_queue:{queue_uuid}')
    r_serv_sync.delete(f'ail2ail:sync_queue:filter:tags:{queue_uuid}')
    r_serv_sync.srem('ail2ail:sync_queue:all', queue_uuid)
    set_last_updated_sync_config()
    return queue_uuid

## API ##

# # TODO: sanityze queue_name
def api_create_sync_queue(json_dict):
    description = json_dict.get('description')
    description = escape(description)
    queue_name = json_dict.get('name')
    if queue_name: #################################################
        queue_name = escape(queue_name)

    tags = json_dict.get('tags')
    if not tags:
        return {"status": "error", "reason": "no tags provided"}, 400
    # FIXME: add custom tags
    # if not Tag.are_enabled_tags(tags):
    #     return {"status": "error", "reason": "Invalid/Disabled tags"}, 400

    max_size = json_dict.get('max_size')
    if not max_size:
        max_size = 100
    try:
        max_size = int(max_size)
    except ValueError:
        return {"status": "error", "reason": "Invalid queue size value"}, 400
    if not max_size > 0:
        return {"status": "error", "reason": "Invalid queue size value"}, 400

    queue_uuid = create_sync_queue(queue_name, tags=tags, description=description,
                                    max_size=max_size)
    return queue_uuid, 200

def api_edit_sync_queue(json_dict):
    queue_uuid = json_dict.get('uuid', '').replace(' ', '').replace('-', '')
    if not is_valid_uuid_v4(queue_uuid):
        return {"status": "error", "reason": "Invalid Queue uuid"}, 400
    if not exists_sync_queue(queue_uuid):
        return {"status": "error", "reason": "Queue Sync not found"}, 404

    description = json_dict.get('description')
    description = escape(description)
    if description is not None:
        edit_sync_queue_description(queue_uuid, description)

    queue_name = json_dict.get('name')
    if queue_name:
        queue_name = escape(queue_name)
        edit_sync_queue_name(queue_uuid, queue_name)

    tags = json_dict.get('tags')
    if tags:
        # FIXME: add custom tags
        # if not Tag.are_enabled_tags(tags):
        #     return {"status": "error", "reason": "Invalid/Disabled tags"}, 400
        edit_sync_queue_filter_tags(queue_uuid, tags)

    max_size = json_dict.get('max_size')
    if max_size:
        try:
            max_size = int(max_size)
        except ValueError:
            return {"status": "error", "reason": "Invalid queue size value"}, 400
        if not max_size > 0:
            return {"status": "error", "reason": "Invalid queue size value"}, 400
        edit_sync_queue_max_size(queue_uuid, max_size)

    return queue_uuid, 200

def api_delete_sync_queue(json_dict):
    queue_uuid = json_dict.get('uuid', '').replace(' ', '').replace('-', '')
    if not is_valid_uuid_v4(queue_uuid):
        return {"status": "error", "reason": "Invalid Queue uuid"}, 400
    if not exists_sync_queue(queue_uuid):
        return {"status": "error", "reason": "Queue Sync not found"}, 404

    res = delete_sync_queue(queue_uuid)
    return res, 200

def api_register_ail_to_sync_queue(json_dict):
    ail_uuid = json_dict.get('ail_uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid AIL uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    queue_uuid = json_dict.get('queue_uuid', '').replace(' ', '').replace('-', '')
    if not is_valid_uuid_v4(queue_uuid):
        return {"status": "error", "reason": "Invalid Queue uuid"}, 400

    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404
    if not exists_sync_queue(queue_uuid):
        return {"status": "error", "reason": "Queue Sync not found"}, 404
    if is_queue_registred_by_ail_instance(queue_uuid, ail_uuid):
        return {"status": "error", "reason": "Queue already registred"}, 400

    res = register_ail_to_sync_queue(ail_uuid, queue_uuid)
    return res, 200

def api_unregister_ail_to_sync_queue(json_dict):
    ail_uuid = json_dict.get('ail_uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(ail_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400
    ail_uuid = sanityze_uuid(ail_uuid)
    queue_uuid = json_dict.get('queue_uuid', '').replace(' ', '').replace('-', '')
    if not is_valid_uuid_v4(queue_uuid):
        return {"status": "error", "reason": "Invalid ail uuid"}, 400

    if not exists_ail_instance(ail_uuid):
        return {"status": "error", "reason": "AIL server not found"}, 404
    if not exists_sync_queue(queue_uuid):
        return {"status": "error", "reason": "Queue Sync not found"}, 404
    if not is_queue_registred_by_ail_instance(queue_uuid, ail_uuid):
        return {"status": "error", "reason": "Queue not registred"}, 400

    res = unregister_ail_to_sync_queue(ail_uuid, queue_uuid)
    return res, 200

#############################
#                           #
#### SYNC REDIS QUEUE #######

def get_sync_queue_object_and_queue_uuid(ail_uuid, push=True):
    for queue_uuid in get_ail_instance_all_sync_queue(ail_uuid):
        obj_dict = get_sync_queue_object_by_queue_uuid(queue_uuid, ail_uuid, push=push)
        if obj_dict:
            return obj_dict, queue_uuid
    return None, None

def get_sync_queue_object(ail_uuid, push=True):
    obj_dict, queue_uuid = get_sync_queue_object_and_queue_uuid(ail_uuid, push=push)[0]
    return obj_dict

def get_sync_queue_object_by_queue_uuid(queue_uuid, ail_uuid, push=True):
    if push:
        sync_mode = 'push'
    else:
        sync_mode = 'pull'
    obj_dict = r_serv_sync.lpop(f'sync:queue:{sync_mode}:{queue_uuid}:{ail_uuid}')
    if obj_dict:
        obj_dict = json.loads(obj_dict)
        # # REVIEW: # TODO: create by obj type
        return Item(obj_dict['id'])

def get_sync_queue_objects_by_queue_uuid(queue_uuid, ail_uuid, push=True):
    if push:
        sync_mode = 'push'
    else:
        sync_mode = 'pull'
    return r_serv_sync.lrange(f'sync:queue:{sync_mode}:{queue_uuid}:{ail_uuid}', 0, -1)

# # TODO: use queue max_size
def add_object_to_sync_queue(queue_uuid, ail_uuid, obj_dict, push=True, pull=True, json_obj=True):
    if json_obj:
        obj = json.dumps(obj_dict)
    else:
        obj = obj_dict

    # # TODO: # FIXME: USE CACHE ??????
    if push:
        r_serv_sync.lpush(f'sync:queue:push:{queue_uuid}:{ail_uuid}', obj)
        r_serv_sync.ltrim(f'sync:queue:push:{queue_uuid}:{ail_uuid}', 0, 200)

    if pull:
        r_serv_sync.lpush(f'sync:queue:pull:{queue_uuid}:{ail_uuid}', obj)
        r_serv_sync.ltrim(f'sync:queue:pull:{queue_uuid}:{ail_uuid}', 0, 200)

def resend_object_to_sync_queue(ail_uuid, queue_uuid, Obj, push=True):
    if queue_uuid is not None and Obj is not None:
        obj_dict = Obj.get_default_meta()
        if push:
            pull = False
        else:
            pull = True
        add_object_to_sync_queue(queue_uuid, ail_uuid, obj_dict, push=push, pull=pull)

# # TODO: # REVIEW: USE CACHE ????? USE QUEUE FACTORY ?????
def get_sync_importer_ail_stream():
    return r_serv_sync.spop('sync:queue:importer')

def add_ail_stream_to_sync_importer(ail_stream):
    ail_stream = json.dumps(ail_stream)
    r_serv_sync.sadd('sync:queue:importer', ail_stream)

#############################
#                           #
#### AIL EXCHANGE FORMAT ####

# TODO
def is_valid_ail_exchange_format_json(json_obj):
    try:
        ail_stream = json.dumps(json_obj)
    except ValueError:
        return False
    return is_valid_ail_exchange_format(ail_stream)

# TODO
def is_valid_ail_exchange_format(ail_stream):
    pass

def create_ail_stream(Object):
    ail_stream = {'format': 'ail',
                  'version': 1,
                  'type': Object.get_type()}

    # OBJECT META
    ail_stream['meta'] = {'ail:mime-type': 'text/plain'}
    ail_stream['meta']['compress'] = 'gzip'
    ail_stream['meta']['encoding'] = 'base64'
    ail_stream['meta']['ail:id'] = Object.get_id()
    ail_stream['meta']['tags'] = Object.get_tags()
    # GLOBAL META
    ail_stream['meta']['uuid_org'] = get_ail_uuid()

    # OBJECT PAYLOAD
    ail_stream['payload'] = Object.get_ail_2_ail_payload()

    return ail_stream

if __name__ == '__main__':

    ail_uuid = '03c51929-eeab-4d47-9dc0-c667f94c7d2d'
    url = "wss://localhost:4443"
    api_key = 'secret'
    #description = 'first test instance'
    queue_uuid = '79bcafc0a6d644deb2c75fb5a83d7caa'
    tags = ['infoleak:submission="manual"']
    name = 'submitted queue'
    description = 'first test queue, all submitted items'
    #queue_uuid = ''

    #res = create_ail_instance(ail_uuid, url, api_key=api_key, description=description)

    #res = create_sync_queue(name, tags=tags, description=description, max_size=100)
    #res = delete_sync_queue(queue_uuid)

    #res = register_ail_to_sync_queue(ail_uuid, queue_uuid)
    #res = change_pull_push_state(ail_uuid, push=True, pull=True)

    # print(get_ail_instance_all_sync_queue(ail_uuid))
    # print(get_all_sync_queue())
    # res = get_all_unregistred_queue_by_ail_instance(ail_uuid)

    ail_uuid = 'c3c2f3ef-ca53-4ff6-8317-51169b73f731'
    #ail_uuid = '2dfeff47-777d-4e70-8c30-07c059307e6a'

    # res = ping_remote_ail_server(ail_uuid)
    # print(res)
    #
    res = send_command_to_server_controller('kill', ail_uuid=ail_uuid)

    #res = _get_remote_ail_server_response(ail_uuid, 'pin')
    print(res)
