#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The JSON Receiver Module
================

Recieve Json Items (example: Twitter feeder)

"""
import os
import importlib
import json
import redis
import sys
import time

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

# Import all receiver
#from all_json_receiver import *

#### CONFIG ####
config_loader = ConfigLoader.ConfigLoader()
server_cache = config_loader.get_redis_conn("Redis_Log_submit")
r_serv_db = config_loader.get_redis_conn("ARDB_DB")
config_loader = None

DEFAULT_FEEDER_NAME = 'Default_json'

#### ------ ####

def reload_json_importer_list():
    global importer_list
    importer_json_dir = os.path.join(os.environ['AIL_BIN'], 'import', 'ail_json_importer')
    importer_list = [f[:-3] for f in os.listdir(importer_json_dir) if os.path.isfile(os.path.join(importer_json_dir, f))]

# init importer list
importer_list = []
reload_json_importer_list()


#### FUNCTIONS ####
def get_json_importer_list():
    return importer_list

def add_json_to_json_queue(json_item):
    json_item = json.dumps(json_item)
    r_serv_db.sadd('importer:json:item', json_item)

def get_json_item_to_import():
    return r_serv_db.spop('importer:json:item')

def get_json_receiver_class(feeder_name_in):
    global importer_list

    # sanitize class name
    feeder_name = feeder_name_in[:1].upper() + feeder_name_in[1:]
    feeder_name = feeder_name.replace('-', '_')

    if feeder_name is None or feeder_name not in get_json_importer_list():
        reload_json_importer_list() # add refresh timing ?
        if feeder_name not in get_json_importer_list():
            print('Unknow feeder: {}'.format(feeder_name_in))
            feeder_name = 'Default_json'
    # avoid subpackages
    parts = feeder_name.split('.')
    module = 'ail_json_importer.{}'.format(parts[-1])
    # import json importer class
    try:
        mod = importlib.import_module(module)
    except:
        raise
    mod = importlib.import_module(module)
    class_name = getattr(mod, feeder_name)
    return class_name

def get_json_source(json_item):
    return json_item.get('source', DEFAULT_FEEDER_NAME)

def process_json(importer_obj, process):
    item_id = importer_obj.get_item_id()
    if 'meta' in importer_obj.get_json_file():
        importer_obj.process_json_meta(process)

    # send data to queue
    send_item_to_ail_queue(item_id, importer_obj.get_item_gzip64encoded_content(), importer_obj.get_feeder_name(), process)

def send_item_to_ail_queue(item_id, gzip64encoded_content, feeder_name, process):
    # Send item to queue
    # send paste to Global
    relay_message = "{0} {1}".format(item_id, gzip64encoded_content)
    process.populate_set_out(relay_message, 'Mixer')

    # increase nb of paste by feeder name
    server_cache.hincrby("mixer_cache:list_feeder", feeder_name, 1)

#### ---- ####


#### API ####
def api_import_json_item(data_json):
    if not data_json:
        return ({'status': 'error', 'reason': 'Malformed JSON'}, 400)

    # # TODO: add JSON verification
    res = add_json_to_json_queue(data_json)
    if not res:
        return ({'status': 'success'}, 200)
