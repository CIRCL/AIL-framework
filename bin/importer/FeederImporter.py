#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import os
import sys

import importlib
import json

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.abstract_importer import AbstractImporter
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader

#### CONFIG ####
config_loader = ConfigLoader()
r_db = config_loader.get_db_conn('Kvrocks_DB')
config_loader = None
# --- CONFIG --- #

#### FUNCTIONS ####

def add_json_feeder_to_queue(json_data):
    json_data = json.dumps(json_data)
    return r_db.rpush('importer:feeder', json_data)

def api_add_json_feeder_to_queue(json_data):
    if not json_data:
        return {'status': 'error', 'reason': 'Malformed JSON'}, 400
    # # TODO: add JSON verification
    res = add_json_feeder_to_queue(json_data)
    if not res:
        return {'status': 'error'}, 400
    return {'status': 'success'}, 200

# --- FUNCTIONS --- #

class FeederImporter(AbstractImporter):
    def __init__(self):
        super().__init__()
        self.feeders = {}
        self.reload_feeders()

    # TODO ADD TIMEOUT RELOAD
    def reload_feeders(self):
        feeder_dir = os.path.join(os.environ['AIL_BIN'], 'importer', 'feeders')
        feeders = [f[:-3] for f in os.listdir(feeder_dir) if os.path.isfile(os.path.join(feeder_dir, f))]
        self.feeders = {}
        for feeder in feeders:
            if feeder == 'abstract_chats_feeder':
                continue
            print(feeder)
            part = feeder.split('.')[-1]
            # import json importer class
            mod = importlib.import_module(f'importer.feeders.{part}')
            cls = getattr(mod, f'{feeder}Feeder')
            print(cls)
            self.feeders[feeder] = cls
            print()
        print(self.feeders)
        print()

    def get_feeder(self, json_data):
        class_name = None
        feeder_name = json_data.get('source')
        if feeder_name:
            if feeder_name.startswith('ail_feeder_'):
                feeder_name = feeder_name.replace('ail_feeder_', '', 1)
            class_name = feeder_name.replace('-', '_').title()

        if not class_name or class_name not in self.feeders:
            class_name = 'Default'
        cls = self.feeders[class_name]
        return cls(json_data)

    def importer(self, json_data):

        feeder = self.get_feeder(json_data)

        feeder_name = feeder.get_name()
        print(f'importing: {feeder_name} feeder')

        # Get Data object:
        data_obj = feeder.get_obj()

        # process meta
        if feeder.get_json_meta():
            objs = feeder.process_meta()
            if objs is None:
                objs = set()
        else:
            objs = set()

        if data_obj:
            objs.add(data_obj)

        objs_messages = []
        for obj in objs:
            # Text created
            if obj.type == 'item':
                if obj.exists():
                    objs_messages.append({'obj': obj, 'message': feeder_name})
                # object save on disk as file (Items)
                else:
                    gzip64_content = feeder.get_gzip64_content()
                    relay_message = f'{feeder_name} {gzip64_content}'
                    objs_messages.append({'obj': obj, 'message': relay_message})
            elif obj.type == 'image':
                date = feeder.get_date()
                objs_messages.append({'obj': obj, 'message': f'{feeder_name} {date}'})
            else:  # Messages save on DB
                if obj.exists() and obj.type != 'chat':
                    objs_messages.append({'obj': obj, 'message': feeder_name})
        return objs_messages

class FeederModuleImporter(AbstractModule):
    def __init__(self):
        super(FeederModuleImporter, self).__init__()
        self.pending_seconds = 5

        config = ConfigLoader()
        self.r_db = config.get_db_conn('Kvrocks_DB')
        self.importer = FeederImporter()

    def get_message(self):
        return self.r_db.lpop('importer:feeder')
        # TODO RELOAD LIST after delta

    def compute(self, message):
        # TODO HANDLE Invalid JSON
        json_data = json.loads(message)
        for obj_message in self.importer.importer(json_data):
            self.add_message_to_queue(obj=obj_message['obj'], message=obj_message['message'])


# Launch Importer
if __name__ == '__main__':
    module = FeederModuleImporter()
    # module.debug = True
    module.run()
