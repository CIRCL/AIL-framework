#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import json

import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects import Images
from lib.objects import Screenshots

config_loader = ConfigLoader()
# r_cache = config_loader.get_redis_conn("Redis_Cache")
OLLAMA_URL = config_loader.get_config_str('Images', 'ollama_url')
IS_OLLAMA_ENABLED = config_loader.get_config_boolean('Images', 'ollama_enabled')
config_loader = None

def is_ollama_enabled():
    return IS_OLLAMA_ENABLED


def get_image_obj(obj_gid):
    if obj_gid.startswith('image:'):
        return Images.Image(obj_gid.split(':')[2])
    elif obj_gid.startswith('screenshot:'):
        return Screenshots.Screenshot(obj_gid.split(':')[2])
    else:
        return None


def create_ollama_data(model, images):
    return json.dumps({'model': model,
                       'prompt': 'what is in this picture?',
                       'stream': False,
                       'images': images
                       })


# screenshot + image
def api_get_image_description(obj_gid):
    image = get_image_obj(obj_gid)
    if not image:
        return {"status": "error", "reason": "Unknown image"}, 404

    description = image.get_description()
    if description:
        return description, 200

    model = 'qwen2.5vl'
    b64 = image.get_base64()
    if not b64:
        return {"status": "error", "reason": "No Content"}, 404

    headers = {"Connection": "close", 'Content-Type': 'application/json', 'Accept': 'application/json'}
    res = requests.post(f'{OLLAMA_URL}/api/generate', data=create_ollama_data(model, [b64]), headers=headers)
    if res.status_code != 200:
        # TODO LOG
        # TODO return error
        print(res.status_code)
        print(res.text)
        return {"status": "error", "reason": "ollama requests error"}, 400
    else:
        r = res.json()
        if r:
            # r_cache.set(f'images:ollama:{obj_gid}', r['response'])
            # r_cache.expire(f'images:ollama:{obj_gid}', 300)
            image.set_description(r['response'])
            return r['response'], 200
    return None, 200
