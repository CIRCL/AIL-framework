#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import os
import sys

# import importlib
import json

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.abstract_importer import AbstractImporter
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from importer.feeders.abstract_crawler_feeder import AbstractCrawlerFeeder

#### CONFIG ####
config_loader = ConfigLoader()
r_db = config_loader.get_db_conn('Kvrocks_DB')
config_loader = None
# --- CONFIG --- #

#### FUNCTIONS ####

# --- FUNCTIONS --- #

class LacusCaptureFeeder(AbstractCrawlerFeeder):

    def __init__(self, logger, json_data):
        super().__init__('lacus_capture', logger, json_data)

class LacusCaptureImporter(AbstractImporter):  # can be renamed
    def __init__(self, logger):
        super().__init__()
        self.logger = logger

    def importer(self, json_data):
        feeder = LacusCaptureFeeder(self.logger, json_data)
        # feeder_name = feeder.get_name()
        # print(f'importing: {feeder_name} feeder')

        # process capture
        objs = feeder.process_capture()
        # process meta field
        if feeder.get_meta():
            new_objs = feeder.process_meta()
            if new_objs:
                objs[0:0] = new_objs
        # messages to queue
        return self.build_queue_messages(objs, feeder)


class LacusCaptureModuleImporter(AbstractModule):
    def __init__(self):
        super(LacusCaptureModuleImporter, self).__init__()
        self.pending_seconds = 5

        config = ConfigLoader()
        self.r_db = config.get_db_conn('Kvrocks_DB')
        self.importer = LacusCaptureImporter(self.logger)

        self.tmp_dir = os.path.join(os.environ['AIL_HOME'], 'temp')

    def get_message(self):
        return self.r_db.spop('importer:lacus:capture')

    def compute(self, capture_uuid):
        # TODO HANDLE Invalid Lacus JSON
        # delete temp file
        print(capture_uuid)
        filename = os.path.join(self.tmp_dir, f'capture_{capture_uuid}.json')
        with open(filename, 'r') as capture_file:
            crawled_capture = json.loads(capture_file.read())
            # print(crawled_capture.keys())
        j_data = {'meta': {}, 'data': crawled_capture}
        for obj_message in self.importer.importer(j_data):
            print(obj_message)
            self.add_message_to_queue(obj=obj_message['obj'], message=obj_message['message'])
        os.remove(filename)


# Launch Importer
if __name__ == '__main__':
    module = LacusCaptureModuleImporter()
    # module.debug = True
    # module.compute('test')
    module.run()
