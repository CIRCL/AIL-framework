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
import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from core import ail_2_ail
from modules.abstract_module import AbstractModule
from packages.Item import Item
from packages import Tag


class Sync_module(AbstractModule):
    """
    Sync_module module for AIL framework
    """

    def __init__(self):
        super(Sync_module, self).__init__()

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 10

        self.dict_sync_queues = ail_2_ail.get_all_sync_queue_dict()
        self.last_refresh = time.time()

        print(self.dict_sync_queues)

        # Send module state to logs
        self.redis_logger.info(f'Module {self.module_name} Launched')


    def compute(self, message):

        ### REFRESH DICT
        if self.last_refresh < ail_2_ail.get_last_updated_sync_config():
            self.last_refresh = time.time()
            self.dict_sync_queues = ail_2_ail.get_all_sync_queue_dict()
            print('sync queues refreshed')
            print(self.dict_sync_queues)

        #  Extract object from message
        # # TODO: USE JSON DICT ????
        mess_split = message.split(';')
        if len(mess_split) == 3:
            obj_type = mess_split[0]
            obj_subtype = mess_split[1]
            obj_id = mess_split[2]

            # OBJECT => Item
            if obj_type == 'item':
                obj = Item(obj_id)
                tags = obj.get_tags(r_set=True)

            # check filter + tags
            #print(message)
            for queue_uuid in self.dict_sync_queues:
                filter_tags = self.dict_sync_queues[queue_uuid]['filter']
                if filter_tags and tags:
                    #print(f'tags: {tags} filter: {filter_tags}')
                    if filter_tags.issubset(tags):
                        obj_dict = obj.get_default_meta()
                        # send to queue push and/or pull
                        for dict_ail in self.dict_sync_queues[queue_uuid]['ail_instances']:
                            print(f'ail_uuid: {dict_ail["ail_uuid"]} obj: {message}')
                            ail_2_ail.add_object_to_sync_queue(queue_uuid, dict_ail['ail_uuid'], obj_dict,
                                                            push=dict_ail['push'], pull=dict_ail['pull'])

        else:
            # Malformed message
            raise Exception(f'too many values to unpack (expected 3) given {len(mess_split)} with message {message}')


if __name__ == '__main__':

    module = Sync_module()
    module.run()
