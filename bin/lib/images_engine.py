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
from lib.ail_core import get_default_image_description_model
from lib.objects import Domains
from lib.objects import Images
from lib.objects import Screenshots

config_loader = ConfigLoader()
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

def create_ollama_domain_data(model, descriptions):
    return json.dumps({'model': model,
                       'prompt': f'From this list of images descritions, Can you please describe this domain and check if it\'s related to child exploitaton?\n\n{descriptions}',
                       'stream': False
                       })

def create_ollama_image_data(model, images):
    return json.dumps({'model': model,
                       'prompt': 'what is in this picture?',
                       'stream': False,
                       'images': images
                       })

# screenshot + image
def api_get_image_description(obj_gid):
    model = get_default_image_description_model()

    image = get_image_obj(obj_gid)
    if not image:
        return {"status": "error", "reason": "Unknown image"}, 404

    description = image.get_description(model)
    if description:
        return description, 200

    b64 = image.get_base64()
    if not b64:
        return {"status": "error", "reason": "No Content"}, 404

    headers = {"Connection": "close", 'Content-Type': 'application/json', 'Accept': 'application/json'}
    try:
        res = requests.post(f'{OLLAMA_URL}/api/generate', data=create_ollama_image_data(model, [b64]), headers=headers)
    except Exception as e:
        return {"status": "error", "reason": f"ollama requests error: {e}"}, 400
    if res.status_code != 200:
        # TODO LOG
        return {"status": "error", "reason": f" llama requests error: {res.status_code}, {res.text}"}, 400
    else:
        r = res.json()
        if r:
            image.add_description_model(model, r['response'])
            return r['response'], 200
    return None, 200

def get_domain_description(domain_id):
    model = get_default_image_description_model()

    domain = Domains.Domain(domain_id)
    descriptions = []
    for image_id in domain.get_crawled_images_by_epoch():
        description = api_get_image_description(f'screenshot::{image_id}')
        print(description)
        if description[1] == 200 and description[0]:
            descriptions.append(description[0])

    if not descriptions:
        return None, 200

    descriptions = '\n\nImage Description:'.join(descriptions)
    print(descriptions)
    headers = {"Connection": "close", 'Content-Type': 'application/json', 'Accept': 'application/json'}
    try:
        res = requests.post(f'{OLLAMA_URL}/api/generate', data=create_ollama_domain_data(model, descriptions), headers=headers)
    except Exception as e:
        return {"status": "error", "reason": f"ollama requests error: {e}"}, 400
    if res.status_code != 200:
        # TODO LOG
        return {"status": "error", "reason": f" llama requests error: {res.status_code}, {res.text}"}, 400
    else:
        r = res.json()
        if r:
            domain.add_description_model(model, r['response'])
            return r['response'], 200
    return None, 200


# if __name__ == '__main__':
#     print(get_domain_description(''))
