#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import argparse
import json
import os
import logging.config
import sys
import time
import traceback
from urllib.parse import urljoin

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

#### LOGS ####
logging.config.dictConfig(ail_logger.get_config(name='syncs'))
logger = logging.getLogger()


config_loader = ConfigLoader()
local_addr = config_loader.get_config_str('AIL_2_AIL', 'local_addr')
if not local_addr or local_addr == None:
    local_addr = None
else:
    local_addr = (local_addr, 0)
config_loader = None

####################################################################

class AIL2AILClient(object):
    """AIL2AILClient."""

    def __init__(self, client_id, ail_uuid, sync_mode):
        self.client_id
        self.ail_uuid = ail_uuid
        self.sync_mode = sync_mode

        self.uri = f"{ail_url}/{sync_mode}/{ail_uuid}"

####################################################################

# # TODO: ADD TIMEOUT => 30s
async def api_request(websocket, ail_uuid):
    res = await websocket.recv()
    # API OUTPUT
    sys.stdout.write(res)

# # TODO: ADD TIMEOUT
async def pull(websocket, ail_uuid):
    while True:
        obj = await websocket.recv()
        sys.stdout.write(obj)

async def push(websocket, ail_uuid):
    # ## DEBUG:
    # try:
    #     while True:
    #         await websocket.send('test')
    #         await asyncio.sleep(10)
    # except websockets.exceptions.ConnectionClosedError as err:
    #     raise err

    try:
        while True:
            # get elem to send
            Obj, queue_uuid = ail_2_ail.get_sync_queue_object_and_queue_uuid(ail_uuid)
            if Obj:
                obj_ail_stream = ail_2_ail.create_ail_stream(Obj)
                print(obj_ail_stream['meta'])
                obj_ail_stream = json.dumps(obj_ail_stream)

                # send objects
                await websocket.send(obj_ail_stream)
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(10)
                # check if connection open
                if not websocket.open:
                    # raise websocket internal exceptions
                    await websocket.send('')

    except websockets.exceptions.ConnectionClosedError as err:
        # resend object in queue on Connection Error
        ail_2_ail.resend_object_to_sync_queue(ail_uuid, queue_uuid, Obj, push=True)
        raise err

async def ail_to_ail_client(ail_uuid, sync_mode, api, ail_key=None, client_id=None):
    if not ail_2_ail.exists_ail_instance(ail_uuid):
        print('AIL server not found')
        return

    if not ail_key:
        ail_key = ail_2_ail.get_ail_instance_key(ail_uuid)

    # # TODO: raise exception
    ail_url = ail_2_ail.get_ail_instance_url(ail_uuid)
    local_ail_uuid = ail_2_ail.get_ail_uuid()

    if sync_mode == 'api':
        uri = f"{ail_url}/{sync_mode}/{api}/{local_ail_uuid}"
    else:
        uri = f"{ail_url}/{sync_mode}/{local_ail_uuid}"
    #print(uri)

    if client_id is None:
        client_id = ail_2_ail.create_sync_client_cache(ail_uuid, sync_mode)

    try:
        async with websockets.connect(
            uri,
            ssl=ssl_context,
            local_addr=local_addr,
            #open_timeout=10, websockers 10.0 /!\ python>=3.7
            extra_headers={"Authorization": f"{ail_key}"}
        ) as websocket:
            # success
            ail_2_ail.clear_save_ail_server_error(ail_uuid)

            if sync_mode == 'pull':
                await pull(websocket, ail_uuid)

            elif sync_mode == 'push':
                await push(websocket, ail_uuid)
                await websocket.close()

            elif sync_mode == 'api':
                await api_request(websocket, ail_uuid)
                await websocket.close()
    except websockets.exceptions.InvalidStatusCode as e:
        status_code = e.status_code
        error_message = ''
        # success
        if status_code == 1000:
            print('connection closed')
        elif status_code == 400:
            error_message = '400 BAD_REQUEST: Invalid path'
        elif status_code == 401:
            error_message = '401 UNAUTHORIZED: Invalid Key'
        elif status_code == 403:
            error_message = '403 FORBIDDEN: SYNC mode disabled'
        else:
            error_message = str(e)
        if error_message:
            sys.stderr.write(error_message)
            logger.warning(f'{ail_uuid}: {error_message}')
            ail_2_ail.save_ail_server_error(ail_uuid, error_message)
    except websockets.exceptions.ConnectionClosedError as e:
        error_message = ail_2_ail.get_websockets_close_message(e.code)
        sys.stderr.write(error_message)
        logger.info(f'{ail_uuid}: {error_message}')
        ail_2_ail.save_ail_server_error(ail_uuid, error_message)

    except websockets.exceptions.InvalidURI as e:
        error_message = f'Invalid AIL url: {e.uri}'
        sys.stderr.write(error_message)
        logger.warning(f'{ail_uuid}: {error_message}')
        ail_2_ail.save_ail_server_error(ail_uuid, error_message)
    except ConnectionError as e:
        error_message = str(e)
        sys.stderr.write(error_message)
        logger.info(f'{ail_uuid}: {error_message}')
        ail_2_ail.save_ail_server_error(ail_uuid, error_message)
    # OSError: Multiple exceptions
    except OSError as e: # # TODO: check if we need to check if is connection error
        error_message = str(e)
        sys.stderr.write(error_message)
        logger.info(f'{ail_uuid}: {error_message}')
        ail_2_ail.save_ail_server_error(ail_uuid, error_message)
    except websockets.exceptions.ConnectionClosedOK as e:
        print('connection closed')
    except Exception as err:
        trace = traceback.format_tb(err.__traceback__)
        trace = ''.join(trace)
        trace = str(trace)
        error_message = f'{trace}\n{str(err)}'
        sys.stderr.write(error_message)
        logger.critical(f'{ail_uuid}: {error_message}')
        ail_2_ail.save_ail_server_error(ail_uuid, error_message)

    ail_2_ail.delete_sync_client_cache(client_id)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Websocket SYNC Client')
    parser.add_argument('-u', '--uuid', help='AIL UUID', type=str, dest='ail_uuid', required=True, default=None)
    parser.add_argument('-i', '--client_id', help='Client ID', type=str, dest='client_id', default=None)
    parser.add_argument('-m', '--mode', help='SYNC Mode, pull, push or api', type=str, dest='sync_mode', default='pull')
    parser.add_argument('-a', '--api', help='API, ping or version', type=str, dest='api', default=None)
    #parser.add_argument('-k', '--key', type=str, default='', help='AIL Key')
    args = parser.parse_args()

    ail_uuid = args.ail_uuid
    sync_mode = args.sync_mode
    api = args.api
    client_id = args.client_id

    if ail_uuid is None or sync_mode not in ['api', 'pull', 'push']:
        parser.print_help()
        sys.exit(0)

    if api:
        if api not in ['ping', 'version']:
            parser.print_help()
            sys.exit(0)

    # SELF SIGNED CERTIFICATES
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    # SELF SIGNED CERTIFICATES

    asyncio.get_event_loop().run_until_complete(ail_to_ail_client(ail_uuid, sync_mode, api, client_id=client_id))
