#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import json
import os
import logging.config
import sys
import uuid

import asyncio
import http
import ssl
import websockets

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_logger
from core import ail_2_ail
from lib.ConfigLoader import ConfigLoader


logging.config.dictConfig(ail_logger.get_config(name='syncs'))
logger = logging.getLogger()


config_loader = ConfigLoader()
host = config_loader.get_config_str('AIL_2_AIL', 'server_host')
port = config_loader.get_config_int('AIL_2_AIL', 'server_port')
config_loader = None

#############################

CONNECTED_CLIENTS = {}
# # TODO: Store in redis

#############################

# # # # # # #
#           #
#   UTILS   #
#           #
# # # # # # #

def is_valid_uuid_v4(UUID):
    if not UUID:
        return False
    UUID = UUID.replace('-', '')
    try:
        uuid_test = uuid.UUID(hex=UUID, version=4)
        return uuid_test.hex == UUID
    except:
        return False

def unpack_path(path):
    dict_path = {}
    path = path.split('/')
    if len(path) < 3:
        raise Exception('Invalid url path')
    if not len(path[-1]):
        path = path[:-1]

    dict_path['sync_mode'] = path[1]
    dict_path['ail_uuid'] = path[-1]
    dict_path['api'] = path[2:-1]

    return dict_path

# # # # # # #

# # TODO: ADD more commands
async def server_controller():
    while True:
        command_dict = ail_2_ail.get_server_controller_command()
        if command_dict:
            command = command_dict.get('command')
            if command == 'kill':
                ail_uuid = command_dict.get('ail_uuid')
                connected_clients = CONNECTED_CLIENTS[ail_uuid].copy()
                for c_websocket in connected_clients:
                    await c_websocket.close(code=1000)
                    logger.info(f'Server Command Connection closed: {ail_uuid}')
                    print(f'Server Command Connection closed: {ail_uuid}')

        await asyncio.sleep(10)

# # # # # # #

async def register(websocket):
    ail_uuid = websocket.ail_uuid
    remote_address = websocket.remote_address
    sync_mode = websocket.sync_mode
    logger.info(f'Client Connected: {ail_uuid} {remote_address}')
    print(f'Client Connected: {ail_uuid} {remote_address}')

    if not ail_uuid in CONNECTED_CLIENTS:
        CONNECTED_CLIENTS[ail_uuid] = set()
    CONNECTED_CLIENTS[ail_uuid].add(websocket)
    ail_2_ail.add_server_connected_client(ail_uuid, sync_mode)

    print('Register client')
    print(CONNECTED_CLIENTS)
    print()

async def unregister(websocket):
    ail_uuid = websocket.ail_uuid
    sync_mode = websocket.sync_mode
    CONNECTED_CLIENTS[ail_uuid].remove(websocket)
    connected_clients = CONNECTED_CLIENTS[ail_uuid].copy()
    for c_websocket in connected_clients:
        if c_websocket.sync_mode == sync_mode:
            sync_mode = None
            break
    if not CONNECTED_CLIENTS[ail_uuid]:
        is_connected = False
        CONNECTED_CLIENTS.pop(ail_uuid)
    else:
        is_connected = True
    ail_2_ail.remove_server_connected_client(ail_uuid, sync_mode=sync_mode, is_connected=is_connected)

    print('Unregister client')
    print(CONNECTED_CLIENTS)
    print()

# PULL: Send data to client
# # TODO: ADD TIMEOUT ???
async def pull(websocket, ail_uuid):
    try:
        for queue_uuid in ail_2_ail.get_ail_instance_all_sync_queue(ail_uuid):
            while True:
                # get elem to send
                Obj = ail_2_ail.get_sync_queue_object_by_queue_uuid(queue_uuid, ail_uuid, push=False)
                if Obj:
                    obj_ail_stream = ail_2_ail.create_ail_stream(Obj)
                    Obj = json.dumps(obj_ail_stream)
                    #print(Obj)

                    # send objects
                    await websocket.send(Obj)
                    await asyncio.sleep(0.1)
                # END PULL
                else:
                    break
    except websockets.exceptions.ConnectionClosedError as err:
        # resend object in queue on Connection Error
        ail_2_ail.resend_object_to_sync_queue(ail_uuid, queue_uuid, Obj, push=False)
        raise err

    # END PULL
    return None


# PUSH: receive data from client
# # TODO: optional queue_uuid
async def push(websocket, ail_uuid):
    #print(ail_uuid)
    while True:
        ail_stream = await websocket.recv()

        # # TODO: CHECK ail_stream
        ail_stream = json.loads(ail_stream)
        #print(ail_stream)

        # # TODO: Close connection on junk
        ail_2_ail.add_ail_stream_to_sync_importer(ail_stream)

# API: server API
# # TODO: ADD TIMEOUT ???
async def api(websocket, ail_uuid, api):
    api = api[0]
    if api == 'ping':
        message = {'message':'pong'}
        message = json.dumps(message)
        await websocket.send(message)
    elif api == 'version':
        sync_version = ail_2_ail.get_sync_server_version()
        message = {'version': sync_version}
        message = json.dumps(message)
        await websocket.send(message)

    # END API
    return

async def ail_to_ail_serv(websocket, path):

    # # TODO: save in class
    ail_uuid = websocket.ail_uuid
    remote_address = websocket.remote_address
    path = unpack_path(path)
    sync_mode = path['sync_mode']

    # # TODO: check if it works
    # # DEBUG:
    # print(websocket.ail_uuid)
    # print(websocket.remote_address)
    # print(f'sync mode: {sync_mode}')

    await register(websocket)
    try:
        if sync_mode == 'pull':
            await pull(websocket, websocket.ail_uuid)
            await websocket.close()
            logger.info(f'Connection closed: {ail_uuid} {remote_address}')
            print(f'Connection closed: {ail_uuid} {remote_address}')

        elif sync_mode == 'push':
            await push(websocket, websocket.ail_uuid)

        elif sync_mode == 'api':
            await api(websocket, websocket.ail_uuid, path['api'])
            await websocket.close()
            logger.info(f'Connection closed: {ail_uuid} {remote_address}')
            print(f'Connection closed: {ail_uuid} {remote_address}')

    finally:
        await unregister(websocket)


###########################################
# CHECK Authorization HEADER and URL PATH #

# # TODO: check AIL UUID (optional header)

class AIL_2_AIL_Protocol(websockets.WebSocketServerProtocol):
    """AIL_2_AIL_Protocol websockets server."""

    async def process_request(self, path, request_headers):

        # DEBUG:
        # print(self.remote_address)
        # print(request_headers)

        # API TOKEN
        api_key = request_headers.get('Authorization', '')
        if api_key is None:
            logger.warning(f'Missing token: {self.remote_address}')
            print(f'Missing token: {self.remote_address}')
            return http.HTTPStatus.UNAUTHORIZED, [], b"Missing token\n"

        if not ail_2_ail.is_allowed_ail_instance_key(api_key):
            logger.warning(f'Invalid token: {self.remote_address}')
            print(f'Invalid token: {self.remote_address}')
            return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid token\n"

        # PATH
        try:
            dict_path = unpack_path(path)
        except Exception as e:
            logger.warning(f'Invalid path: {self.remote_address}')
            print(f'Invalid path: {self.remote_address}')
            return http.HTTPStatus.BAD_REQUEST, [], b"Invalid path\n"


        ail_uuid = ail_2_ail.get_ail_instance_by_key(api_key)
        if ail_uuid != dict_path['ail_uuid']:
            logger.warning(f'Invalid token: {self.remote_address} {ail_uuid}')
            print(f'Invalid token: {self.remote_address} {ail_uuid}')
            return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid token\n"


        if not api_key != ail_2_ail.get_ail_instance_key(api_key):
            logger.warning(f'Invalid token: {self.remote_address} {ail_uuid}')
            print(f'Invalid token: {self.remote_address} {ail_uuid}')
            return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid token\n"

        self.ail_key = api_key
        self.ail_uuid = ail_uuid
        self.sync_mode = dict_path['sync_mode']

        if self.sync_mode == 'pull' or self.sync_mode == 'push':

            # QUEUE UUID
            # if dict_path['queue_uuid']:
            #
            #     if not is_valid_uuid_v4(dict_path['queue_uuid']):
            #         print('Invalid UUID')
            #         return http.HTTPStatus.BAD_REQUEST, [], b"Invalid UUID\n"
            #
            #     self.queue_uuid = dict_path['queue_uuid']
            # else:
            #     self.queue_uuid = None
            #
            # if not ail_2_ail.is_ail_instance_queue(ail_uuid, dict_path['queue_uuid']):
            #     print('UUID not found')
            #     return http.HTTPStatus.FORBIDDEN, [], b"UUID not found\n"

            # SYNC MODE
            if not ail_2_ail.is_ail_instance_sync_enabled(self.ail_uuid, sync_mode=self.sync_mode):
                sync_mode = self.sync_mode
                logger.warning(f'SYNC mode disabled: {self.remote_address} {ail_uuid} {sync_mode}')
                print(f'SYNC mode disabled: {self.remote_address} {ail_uuid} {sync_mode}')
                return http.HTTPStatus.FORBIDDEN, [], b"SYNC mode disabled\n"

        # # TODO: CHECK API
        elif self.sync_mode == 'api':
            pass

        else:
            print(f'Invalid path: {self.remote_address}')
            logger.info(f'Invalid path: {self.remote_address}')
            return http.HTTPStatus.BAD_REQUEST, [], b"Invalid path\n"

###########################################

# # TODO: clean shutdown / kill all connections
# # TODO: Filter object
# # TODO: IP/uuid to block

if __name__ == '__main__':

    print('Launching Server...')
    logger.info('Launching Server...')

    ail_2_ail.clear_server_connected_clients()

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_dir = os.environ['AIL_FLASK']
    ssl_context.load_cert_chain(certfile=os.path.join(cert_dir, 'server.crt'), keyfile=os.path.join(cert_dir, 'server.key'))

    start_server = websockets.serve(ail_to_ail_serv, host, port, ssl=ssl_context, create_protocol=AIL_2_AIL_Protocol, max_size=None)

    print(f'Server Launched:    wss://{host}:{port}')
    logger.info(f'Server Launched:    wss://{host}:{port}')

    loop = asyncio.get_event_loop()
    # server command
    loop.create_task(server_controller())
    # websockets server
    loop.run_until_complete(start_server)
    loop.run_forever()
