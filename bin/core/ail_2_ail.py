#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import json
import secrets
import sys
import time
import uuid

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'core/'))
import screen

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
from Item import Item

config_loader = ConfigLoader.ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_serv_sync = config_loader.get_redis_conn("ARDB_DB")
config_loader = None

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')

def generate_sync_api_key():
    return secrets.token_urlsafe(42)

def get_ail_uuid():
    return r_serv_db.get('ail:uuid')

# # TODO: # TODO: # TODO: # TODO: # TODO: ADD SYNC MODE == PUSH
# # TODO: get connection status
# # TODO: get connection METADATA
#############################
#                           #
#### SYNC CLIENT MANAGER ####

def get_all_sync_clients(r_set=False):
    res = r_cache.smembers('ail_2_ail:all_sync_clients')
    if r_set:
        return set(res)
    else:
        return res

def get_sync_client_ail_uuid(client_id):
    return r_cache.hget(f'ail_2_ail:sync_client:{client_id}', 'ail_uuid')

def get_sync_client_queue_uuid(client_id):
    return r_cache.hget(f'ail_2_ail:sync_client:{client_id}', 'queue_uuid')

def delete_sync_client_cache(client_id):
    ail_uuid = get_sync_client_ail_uuid(client_id)
    queue_uuid = get_sync_client_queue_uuid(client_id)
    # map ail_uuid/queue_uuid
    r_cache.srem(f'ail_2_ail:ail_uuid:{ail_uuid}', client_id)
    r_cache.srem(f'ail_2_ail:queue_uuid:{queue_uuid}', client_id)

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
def send_command_to_manager(command, client_id=-1):
    dict_action = {'command': command, 'client_id': client_id}
    r_cache.sadd('ail_2_ail:client_manager:command', dict_action)

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
        for new_id in range(100000):
            if new_id not in self.clients:
                return str(new_id)

    def get_sync_client_ail_uuid(self, client_id):
        return self.clients[client_id]['ail_uuid']

    def get_sync_client_queue_uuid(self, client_id):
        return self.clients[client_id]['queue_uuid']

    # # TODO: check PUSH ACL
    def get_all_sync_clients_to_launch(self):
        return get_all_ail_instance()

    def relaunch_all_sync_clients(self):
        delete_all_sync_clients_cache()
        self.clients = {}
        for ail_uuid in self.get_all_sync_clients_to_launch():
             self.launch_sync_client(ail_uuid)

    def launch_sync_client(self, ail_uuid):
        dir_project = os.environ['AIL_HOME']
        client_id = self.get_new_sync_client_id()
        script_options = f'-a {ail_uuid} -m push -i {client_id}'
        screen.create_screen(AIL2AILClientManager.SCREEN_NAME)
        screen.launch_uniq_windows_script(AIL2AILClientManager.SCREEN_NAME,
                                            client_id, dir_project,
                                            AIL2AILClientManager.SCRIPT_DIR,
                                            AIL2AILClientManager.SCRIPT_NAME,
                                            script_options=script_options, kill_previous_windows=True)
        # save sync client status
        r_cache.hset(f'ail_2_ail:sync_client:{client_id}', 'ail_uuid', ail_uuid)
        r_cache.hset(f'ail_2_ail:sync_client:{client_id}', 'launch_time', int(time.time()))

        # create map ail_uuid/queue_uuid
        r_cache.sadd(f'ail_2_ail:ail_uuid:{ail_uuid}', client_id)

        self.clients[client_id] = {'ail_uuid': ail_uuid}

    # # TODO: FORCE KILL ????????????
    # # TODO: check if exists
    def kill_sync_client(self, client_id):
        if not kill_screen_window('AIL_2_AIL', client_id):
            # # TODO: log kill error
            pass

        delete_sync_client_cache(client_id)
        self.clients.pop(client_id)

    ## COMMANDS ##

    def get_manager_command(self):
        res = r_cache.spop('ail_2_ail:client_manager:command')
        if res:
            return json.dumps(res)
        else:
            return None

    def execute_manager_command(self, command_dict):
        command = command_dict.get('command')
        if command == 'launch':
            ail_uuid = int(command_dict.get('ail_uuid'))
            queue_uuid = int(command_dict.get('queue_uuid'))
            self.launch_sync_client(ail_uuid, queue_uuid)
        elif command == 'relaunch':
            self.relaunch_all_sync_clients()
        else:
            # only one sync client
            client_id = int(command_dict.get('client_id'))
            if client_id < 1:
                print('Invalid client id')
                return None
            if command == 'kill':
                self.kill_sync_client(client_id)
            elif command == 'relaunch':
                ail_uuid = self.get_sync_client_ail_uuid(client_id)
                queue_uuid = self.get_sync_client_queue_uuid(client_id)
                self.kill_sync_client(client_id)
                self.launch_sync_client(ail_uuid, queue_uuid)

########################################
########################################
########################################

# # TODO: ADD METADATA
def get_sync_client_status(client_id):
    dict_client = {'id': client_id}
    dict_client['ail_uuid'] = get_sync_client_ail_uuid(client_id)
    dict_client['queue_uuid'] = get_sync_client_queue_uuid(client_id)
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
    return r_serv_sync.sismember(f'ail:instance:key:all', key)

def get_ail_instance_key(ail_uuid):
    return r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'api_key')

def get_ail_instance_by_key(key):
    return r_serv_sync.get(f'ail:instance:key:{key}')

# def check_acl_sync_queue_ail(ail_uuid, queue_uuid, key):
#     return is_ail_instance_queue(ail_uuid, queue_uuid)

def update_ail_instance_key(ail_uuid, new_key):
    old_key = get_ail_instance_key(ail_uuid)
    r_serv_sync.srem(f'ail:instance:key:all', old_key)
    r_serv_sync.delete(f'ail:instance:key:{old_key}')

    r_serv_sync.sadd(f'ail:instance:key:all', new_key)
    r_serv_sync.delete(f'ail:instance:key:{new_key}', ail_uuid)
    r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'api_key', new_key)

#- AIL KEYS -#

def get_all_ail_instance():
    return r_serv_sync.smembers('ail:instance:all')

def get_ail_instance_all_sync_queue(ail_uuid):
    return r_serv_sync.smembers(f'ail:instance:sync_queue:{ail_uuid}')

def is_ail_instance_queue(ail_uuid, queue_uuid):
    return r_serv_sync.sismember(f'ail:instance:sync_queue:{ail_uuid}', queue_uuid)

def get_ail_instance_url(ail_uuid):
    return r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'url')

def get_ail_instance_description(ail_uuid):
    return r_serv_sync.hget(f'ail:instance:{ail_uuid}', 'description')

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

def change_pull_push_state(ail_uuid, pull=False, push=False):
    # sanityze pull/push
    if pull:
        pull = True
    else:
        pull = False
    if push:
        push = True
    else:
        push = False
    r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'push', push)
    r_serv_sync.hset(f'ail:instance:{ail_uuid}', 'pull', pull)


# # TODO: HIDE ADD GLOBAL FILTER (ON BOTH SIDE)
# # TODO: push/pull
def get_ail_instance_metadata(ail_uuid):
    dict_meta = {}
    dict_meta['uuid'] = ail_uuid
    dict_meta['url'] = get_ail_instance_url(ail_uuid)
    dict_meta['description'] = get_ail_instance_description(ail_uuid)

    # # TODO: HIDE
    dict_meta['api_key'] = get_ail_instance_key(ail_uuid)

    # # TODO:
    # - set UUID sync_queue

    return dict_meta

# # TODO: VALIDATE URL
#                  API KEY
def create_ail_instance(ail_uuid, url, api_key=None, description=None):
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

def get_last_updated_ail_instance():
    epoch = r_serv_sync.get(f'ail:instance:queue:last_updated')
    if not epoch:
        epoch = 0
    return float(epoch)

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

# # TODO: check if push or pull enabled ?
def is_queue_used_by_ail_instace(queue_uuid):
    return r_serv_sync.exists(f'ail2ail:sync_queue:ail_instance:{queue_uuid}')

# # TODO: add others filter
def get_sync_queue_filter(queue_uuid):
    return r_serv_sync.smembers(f'ail2ail:sync_queue:filter:tags:{queue_uuid}')

# # TODO: ADD FILTER
def get_sync_queue_metadata(queue_uuid):
    dict_meta = {}
    dict_meta['uuid'] = queue_uuid
    dict_meta['name'] = r_serv_sync.hget(f'ail2ail:sync_queue:{queue_uuid}', 'name')
    dict_meta['description'] = r_serv_sync.hget(f'ail2ail:sync_queue:{queue_uuid}', 'description')
    dict_meta['max_size'] = r_serv_sync.hget(f'ail2ail:sync_queue:{queue_uuid}', 'max_size')

    # # TODO: TO ADD:
    # - set uuid instance

    return dict_meta

#####################################################
def get_all_sync_queue_dict():
    dict_sync_queues = {}
    for queue_uuid in get_all_sync_queue():
        if is_queue_used_by_ail_instace(queue_uuid):
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


def register_ail_to_sync_queue(ail_uuid, queue_uuid):
    r_serv_sync.sadd(f'ail2ail:sync_queue:ail_instance:{queue_uuid}', ail_uuid)
    r_serv_sync.sadd(f'ail:instance:sync_queue:{ail_uuid}', queue_uuid)

def unregister_ail_to_sync_queue(ail_uuid, queue_uuid):
    r_serv_sync.srem(f'ail2ail:sync_queue:ail_instance:{queue_uuid}', ail_uuid)
    r_serv_sync.srem(f'ail:instance:sync_queue:{ail_uuid}', queue_uuid)

# # TODO: optionnal name ???
# # TODO: SANITYZE TAGS
def create_sync_queue(name, tags=[], description=None, max_size=100):
    queue_uuid = generate_uuid()
    r_serv_sync.sadd('ail2ail:sync_queue:all', queue_uuid)

    r_serv_sync.hset(f'ail2ail:sync_queue:{queue_uuid}', 'name', name)
    if description:
        r_serv_sync.hset(f'ail2ail:sync_queue:{queue_uuid}', 'description', description)
    r_serv_sync.hset(f'ail2ail:sync_queue:{queue_uuid}', 'max_size', max_size)

    for tag in tags:
        r_serv_sync.sadd(f'ail2ail:sync_queue:filter:tags:{queue_uuid}', tag)

    return queue_uuid

def delete_sync_queue(queue_uuid):
    for ail_uuid in get_sync_queue_all_ail_instance(queue_uuid):
        unregister_ail_to_sync_queue(ail_uuid, queue_uuid)
    r_serv_sync.delete(f'ail2ail:sync_queue:{queue_uuid}')
    r_serv_sync.srem('ail2ail:sync_queue:all', queue_uuid)
    return queue_uuid

#############################
#                           #
#### SYNC REDIS QUEUE #######

def get_sync_queue_object(ail_uuid, push=True):
    for queue_uuid in get_ail_instance_all_sync_queue(ail_uuid):
        obj_dict = get_sync_queue_object_by_queue_uuid(queue_uuid, ail_uuid, push=push)
        if obj_dict:
            return obj_dict
    return None

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

def add_object_to_sync_queue(queue_uuid, ail_uuid, obj_dict, push=True, pull=True):
    obj = json.dumps(obj_dict)

    # # TODO: # FIXME: USE CACHE ??????
    if push:
        r_serv_sync.lpush(f'sync:queue:push:{queue_uuid}:{ail_uuid}', obj)
        r_serv_sync.ltrim(f'sync:queue:push:{queue_uuid}:{ail_uuid}', 0, 200)

    if pull:
        r_serv_sync.lpush(f'sync:queue:pull:{queue_uuid}:{ail_uuid}', obj)
        r_serv_sync.ltrim(f'sync:queue:pull:{queue_uuid}:{ail_uuid}', 0, 200)

# # TODO: # REVIEW: USE CACHE ????? USE QUEUE FACTORY ?????
def get_sync_importer_ail_stream():
    return r_serv_sync.spop('sync:queue:importer')

def add_ail_stream_to_sync_importer(ail_stream):
    ail_stream = json.dumps(ail_stream)
    r_serv_sync.sadd('sync:queue:importer', ail_stream)

#############################
#                           #
#### AIL EXCHANGE FORMAT ####

def create_ail_stream(Object):
    ail_stream = {'format': 'ail',
                  'version': 1,
                  'type': Object.get_type()}

    # OBJECT META
    ail_stream['meta'] = {'ail_mime-type': 'text/plain'}
    ail_stream['meta']['ail:id'] = Object.get_id()
    ail_stream['meta']['ail:tags'] = Object.get_tags()
    # GLOBAL PAYLOAD
    ail_stream['meta']['ail:uuid'] = get_ail_uuid()

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
    res = change_pull_push_state(ail_uuid, push=True, pull=True)

    print(res)
