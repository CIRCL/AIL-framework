#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import argparse
import json
import os
import sys
import time
from urllib.parse import urljoin

import asyncio
import http
import ssl
import websockets

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from core import ail_2_ail

####################################################################

class AIL2AILClient(object):
    """AIL2AILClient."""

    def __init__(self, client_id, ail_uuid, sync_mode):
        self.client_id
        self.ail_uuid = ail_uuid
        self.sync_mode = sync_mode

        # # TODO:
        self.ail_url = "wss://localhost:4443"

        self.uri = f"{ail_url}/{sync_mode}/{ail_uuid}"

####################################################################

# # TODO: ADD TIMEOUT
async def pull(websocket, ail_uuid):
    while True:
        obj = await websocket.recv()
        print(obj)

async def push(websocket, ail_uuid):

    while True:
        # get elem to send
        Obj = ail_2_ail.get_sync_queue_object(ail_uuid)
        if Obj:
            obj_ail_stream = ail_2_ail.create_ail_stream(Obj)
            obj_ail_stream = json.dumps(obj_ail_stream)
            print(obj_ail_stream)

            # send objects
            await websocket.send(obj_ail_stream)
             # DEBUG:
            await asyncio.sleep(0.1)
        else:
            await asyncio.sleep(10)


async def ail_to_ail_client(ail_uuid, sync_mode, ail_key=None):
    if not ail_key:
        ail_key = ail_2_ail.get_ail_instance_key(ail_uuid)
    ail_url = "wss://localhost:4443"

    uri = f"{ail_url}/{sync_mode}/{ail_uuid}"
    print(uri)

    async with websockets.connect(
        uri,
        ssl=ssl_context,
        extra_headers={"Authorization": f"{ail_key}"}
    ) as websocket:

        if sync_mode == 'pull':
            await pull(websocket, ail_uuid)

        elif sync_mode == 'push':
            await push(websocket, ail_uuid)
            await websocket.close()

        elif sync_mode == 'api':
            await websocket.close()

##########################################################3
# # TODO:manual key
##########################################################
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Websocket SYNC Client')
    parser.add_argument('-a', '--ail', help='AIL UUID', type=str, dest='ail_uuid', required=True, default=None)
    parser.add_argument('-i', '--client_id', help='Client ID', type=str, dest='client_id', default=None)
    parser.add_argument('-m', '--mode', help='SYNC Mode, pull or push', type=str, dest='sync_mode', default='pull')
    #parser.add_argument('-k', '--key', type=str, default='', help='AIL Key')
    args = parser.parse_args()

    ail_uuid = args.ail_uuid
    sync_mode = args.sync_mode

    if ail_uuid is None or sync_mode not in ['pull', 'push']:
        parser.print_help()
        sys.exit(0)

    #ail_uuid = '03c51929-eeab-4d47-9dc0-c667f94c7d2d'
    #sync_mode = 'pull'

    # SELF SIGNED CERTIFICATES
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    # SELF SIGNED CERTIFICATES

    asyncio.get_event_loop().run_until_complete(ail_to_ail_client(ail_uuid, sync_mode))
