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
from lib import search_engine

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
                       'prompt': f'From this list of images descriptions, Can you please describe this domain and check if it\'s related to child exploitation?\n\n{descriptions}',
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
            # index
            if search_engine.is_meilisearch_enabled():
                if image.type == 'image':
                    search_engine.index_image_description(image)
                else:
                    search_engine.index_screenshot_description(image)

            return r['response'], 200
    return None, 200

def get_domain_description(domain_id, reprocess=True):
    model = get_default_image_description_model()

    domain = Domains.Domain(domain_id)
    if not domain.exists():
        return {"status": "error", "reason": f"Domain {domain_id} does not exist"}, 404

    if not reprocess:
        description = domain.get_description(model)
        if description:
            return description, 200

    descriptions = []
    for image_id in domain.get_crawled_images_by_epoch():
        description = api_get_image_description(f'screenshot::{image_id}')
        print(description)
        if description[1] == 200 and description[0]:
            descriptions.append(description[0])

    if not descriptions:
        return None, 200

    descriptions = '\n\nImage Description:'.join(descriptions)
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
            # index
            if search_engine.is_meilisearch_enabled():
                search_engine.index_domain_description(domain_id)

            print(r['response'])
            return r['response'], 200
    return None, 200

def _create_domains_up_description():
    nb_domains = Domains.get_nb_domains_up_by_type('onion') + Domains.get_nb_domains_up_by_type('web')
    done = 0
    for domain in Domains.get_domain_up_iterator():
        get_domain_description(domain.get_id(), reprocess=False)
        done += 1
        progress = int(done * 100 / nb_domains)
        print(f'{done}/{nb_domains}        {progress}%')

def _create_image_description():
    total = Images.Images().get_nb()
    done = 0
    for image in Images.get_all_images_objects():
        api_get_image_description(image.get_global_id())
        done += 1
        progress = int(done * 100 / total)
        print(f'{done}/{total}        {progress}%')


if __name__ == '__main__':
    # _create_domains_up_description()
    _create_image_description()
