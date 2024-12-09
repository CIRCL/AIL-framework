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
import traceback

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from core import ail_2_ail
from lib.ail_queues import get_processed_end_obj, timeout_processed_objs, get_last_queue_timeout
from lib.exceptions import ModuleQueueError
from lib.objects import ail_objects
from modules.abstract_module import AbstractModule


class Sync_module(AbstractModule):
    """
    Sync_module module for AIL framework
    """

    def __init__(self, queue=False):  # FIXME MODIFY/ADD QUEUE
        super(Sync_module, self).__init__(queue=queue)

        # Waiting time in seconds between to message processed
        self.pending_seconds = 10

        self.dict_sync_queues = ail_2_ail.get_all_sync_queue_dict()
        self.last_refresh = time.time()
        self.last_refresh_queues = time.time()

        print(self.dict_sync_queues)

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} Launched')

    def compute(self, message):

        ### REFRESH DICT
        if self.last_refresh < ail_2_ail.get_last_updated_sync_config():
            self.last_refresh = time.time()
            self.dict_sync_queues = ail_2_ail.get_all_sync_queue_dict()
            print('sync queues refreshed')
            print(self.dict_sync_queues)

        obj = ail_objects.get_obj_from_global_id(message)

        tags = obj.get_tags()

        # check filter + tags
        # print(message)
        for queue_uuid in self.dict_sync_queues:
            filter_tags = self.dict_sync_queues[queue_uuid]['filter']
            if filter_tags and tags:
                # print('tags: {tags} filter: {filter_tags}')
                if filter_tags.issubset(tags):
                    obj_dict = obj.get_default_meta()
                    # send to queue push and/or pull
                    for dict_ail in self.dict_sync_queues[queue_uuid]['ail_instances']:
                        print(f'ail_uuid: {dict_ail["ail_uuid"]} obj: {obj.type}:{obj.get_subtype(r_str=True)}:{obj.id}')
                        ail_2_ail.add_object_to_sync_queue(queue_uuid, dict_ail['ail_uuid'], obj_dict,
                                                           push=dict_ail['push'], pull=dict_ail['pull'])

    def run(self):
        """
        Run Module endless process
        """

        # Endless loop processing messages from the input queue
        while self.proceed:

            # Timeout queues
            # timeout_processed_objs()
            if self.last_refresh_queues < time.time():
                timeout_processed_objs()
                self.last_refresh_queues = time.time() + 120
                # print('Timeout queues')

            # Get one message (paste) from the QueueIn (copy of Redis_Global publish)
            global_id = get_processed_end_obj()
            if global_id:
                try:
                    # Module processing with the message from the queue
                    self.compute(global_id)
                except Exception as err:
                    if self.debug:
                        self.queue.error()
                        raise err

                    # LOG ERROR
                    trace = traceback.format_tb(err.__traceback__)
                    trace = ''.join(trace)
                    self.logger.critical(f"Error in module {self.module_name}: {__name__} : {err}")
                    self.logger.critical(f"Module {self.module_name} input message: {global_id}")
                    self.logger.critical(trace)

                    if isinstance(err, ModuleQueueError):
                        self.queue.error()
                        raise err

            else:
                self.computeNone()
                # Wait before next process
                self.logger.debug(f"{self.module_name}, waiting for new message, Idling {self.pending_seconds}s")
                time.sleep(self.pending_seconds)


if __name__ == '__main__':

    module = Sync_module(queue=False)  # FIXME MODIFY/ADD QUEUE
    module.run()
