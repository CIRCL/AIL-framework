#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The SYNC Module
================================

This module .

"""

##################################
# Import External packages
##################################
import json
import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from core import ail_2_ail
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item

#### CONFIG ####
# config_loader = ConfigLoader()
#
# config_loader = None
#### ------ ####

class Sync_importer(AbstractModule):
    """
    Sync_importer module for AIL framework
    """

    def __init__(self):
        super(Sync_importer, self).__init__()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 10

        # self.dict_ail_sync_filters = ail_2_ail.get_all_sync_queue_dict()
        # self.last_refresh = time.time()

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} Launched')

    def run(self):
        while self.proceed:
            ### REFRESH DICT
            # if self.last_refresh < ail_2_ail.get_last_updated_ail_instance():
            #     self.dict_ail_sync_filters = ail_2_ail.get_all_sync_queue_dict()
            #     self.last_refresh = time.time()

            ail_stream = ail_2_ail.get_sync_importer_ail_stream()
            if ail_stream:
                ail_stream = json.loads(ail_stream)
                self.compute(ail_stream)

            else:
                self.computeNone()
                # Wait before next process
                self.logger.debug(f"{self.module_name}, waiting for new message, Idling {self.pending_seconds}s")
                time.sleep(self.pending_seconds)

    def compute(self, ail_stream):

        # # TODO: SANITYZE AIL STREAM
        # # TODO: CHECK FILTER

        # import Object
        b64_gzip_content = ail_stream['payload']['raw']

        # # TODO: create default id
        item_id = ail_stream['meta']['ail:id']
        item = Item(item_id)

        message = f'sync {b64_gzip_content}'
        print(item.id)
        self.add_message_to_queue(obj=item, message=message, queue='Importers')


if __name__ == '__main__':
    module = Sync_importer()
    module.run()
