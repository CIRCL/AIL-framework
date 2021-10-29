#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import json
import os
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
from core import ail_2_ail


obj_test = {
    "format": "ail",
    "version": 1,
    "type": "item",
    "meta": {
       "ail:uuid": "03c51929-eeab-4d47-9dc0-c667f94c7d2c",
       "ail:uuid_org": "28bc3db3-16da-461c-b20b-b944f4058708",
    },
    "payload": {
        "raw" : "MjhiYzNkYjMtMTZkYS00NjFjLWIyMGItYjk0NGY0MDU4NzA4Cg==",
        "compress": "gzip",
        "encoding": "base64"
    }
}

#############################

CONNECTED_CLIENT = set()
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
    dict_path['sync_mode'] = path[1]
    dict_path['ail_uuid'] = path[2]
    return dict_path

# # # # # # #


# async def send_object():
#     if CONNECTED_CLIENT:
#         message = 'new json object {"id": "test01"}'
#         await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
    CONNECTED_CLIENT.add(websocket)
    print(CONNECTED_CLIENT)

async def unregister(websocket):
    CONNECTED_CLIENT.remove(websocket)

# PULL: Send data to client
# # TODO: ADD TIMEOUT ???
async def pull(websocket, ail_uuid):

    for queue_uuid in ail_2_ail.get_ail_instance_all_sync_queue(ail_uuid):
        while True:
            # get elem to send
            Obj = ail_2_ail.get_sync_queue_object_by_queue_uuid(queue_uuid, ail_uuid, push=False)
            if Obj:
                obj_ail_stream = ail_2_ail.create_ail_stream(Obj)
                Obj = json.dumps(obj_ail_stream)
                print(Obj)

                # send objects
                await websocket.send(Obj)
            # END PULL
            else:
                break

    # END PULL
    return None


# PUSH: receive data from client
# # TODO: optional queue_uuid
async def push(websocket, ail_uuid):
    print(ail_uuid)
    while True:
        ail_stream = await websocket.recv()

        # # TODO: CHECK ail_stream
        ail_stream = json.loads(ail_stream)
        print(ail_stream)

        ail_2_ail.add_ail_stream_to_sync_importer(ail_stream)

async def ail_to_ail_serv(websocket, path):


    # # TODO: check if it works
    # # DEBUG:
    print(websocket.ail_key)
    print(websocket.ail_uuid)

    print(websocket.remote_address)
    path = unpack_path(path)
    sync_mode = path['sync_mode']
    print(f'sync mode: {sync_mode}')

    await register(websocket)
    try:
        if sync_mode == 'pull':
            await pull(websocket, websocket.ail_uuid)
            await websocket.close()
            print('closed')

        elif sync_mode == 'push':
            await push(websocket, websocket.ail_uuid)

        elif sync_mode == 'api':
            await websocket.close()

    finally:
        await unregister(websocket)


###########################################
# CHECK Authorization HEADER and URL PATH #

# # TODO: check AIL UUID (optional header)

class AIL_2_AIL_Protocol(websockets.WebSocketServerProtocol):
    """AIL_2_AIL_Protocol websockets server."""

    async def process_request(self, path, request_headers):

        print(self.remote_address)
        print(request_headers)
        # API TOKEN
        api_key = request_headers.get('Authorization', '')
        print(api_key)
        if api_key is None:
            print('Missing token')
            return http.HTTPStatus.UNAUTHORIZED, [], b"Missing token\n"

        if not ail_2_ail.is_allowed_ail_instance_key(api_key):
            print('Invalid token')
            return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid token\n"

        # PATH
        try:
            dict_path = unpack_path(path)
        except Exception as e:
            print('Invalid path')
            return http.HTTPStatus.BAD_REQUEST, [], b"Invalid path\n"


        ail_uuid = ail_2_ail.get_ail_instance_by_key(api_key)
        if ail_uuid != dict_path['ail_uuid']:
            print('Invalid token')
            return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid token\n"


        if not api_key != ail_2_ail.get_ail_instance_key(api_key):
            print('Invalid token')
            return http.HTTPStatus.UNAUTHORIZED, [], b"Invalid token\n"

        self.ail_key = api_key
        self.ail_uuid = ail_uuid

        if dict_path['sync_mode'] == 'pull' or dict_path['sync_mode'] == 'push':

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
            if not ail_2_ail.is_ail_instance_sync_enabled(self.ail_uuid, sync_mode=dict_path['sync_mode']):
                print('SYNC mode disabled')
                return http.HTTPStatus.FORBIDDEN, [], b"SYNC mode disabled\n"

        # # TODO: CHECK API
        elif dict_path[sync_mode] == 'api':
            pass

        else:
            print('Invalid path')
            return http.HTTPStatus.BAD_REQUEST, [], b"Invalid path\n"


###########################################

# # TODO: logging
# # TODO: clean shutdown / kill all connections
# # TODO: API
# # TODO: Filter object
# # TODO: process_request check
# # TODO: IP/uuid to block

if __name__ == '__main__':

    host = 'localhost'
    port = 4443

    print('Launching Server...')

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_dir = os.environ['AIL_FLASK']
    ssl_context.load_cert_chain(certfile=os.path.join(cert_dir, 'server.crt'), keyfile=os.path.join(cert_dir, 'server.key'))

    start_server = websockets.serve(ail_to_ail_serv, "localhost", 4443, ssl=ssl_context, create_protocol=AIL_2_AIL_Protocol)

    print(f'Server Launched:    wss://{host}:{port}')

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
