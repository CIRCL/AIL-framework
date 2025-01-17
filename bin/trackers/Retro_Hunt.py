#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Retro_Hunt trackers module
===================

"""

##################################
# Import External packages
##################################
import os
import sys
import time
import yara

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ail_core import get_objects_retro_hunted
from lib.ConfigLoader import ConfigLoader
from lib.objects import ail_objects
from lib import Tracker

class Retro_Hunt_Module(AbstractModule):

    """
    Retro_Hunt module for AIL framework
    """
    def __init__(self):
        super(Retro_Hunt_Module, self).__init__()
        config_loader = ConfigLoader()
        self.pending_seconds = 5

        # reset on each loop
        self.retro_hunt = None
        self.nb_objs = 0
        self.nb_done = 0
        self.progress = 0
        self.obj = None
        self.tags = []

        self.logger.info(f"Module: {self.module_name} Launched")

    # # TODO:   # start_time
    #           # end_time
    def compute(self, task_uuid):
        print(f'starting Retro hunt task {task_uuid}')
        self.progress = 0
        # First launch
        # restart
        self.retro_hunt = Tracker.RetroHunt(task_uuid)

        rule = self.retro_hunt.get_rule(r_compile=True)
        timeout = self.retro_hunt.get_timeout()
        self.tags = self.retro_hunt.get_tags()

        self.logger.debug(f'{self.module_name}, Retro Hunt rule {task_uuid} timeout {timeout}')

        # Filters
        filters = self.retro_hunt.get_filters()
        if not filters:
            filters = {}
            for obj_type in get_objects_retro_hunted():
                filters[obj_type] = {}

        self.nb_objs = ail_objects.card_objs_iterators(filters)

        # Resume
        last_obj = self.retro_hunt.get_last_analyzed()
        if last_obj:
            last_obj_type, last_obj_subtype, last_obj_id = last_obj.split(':', 2)
            if last_obj_subtype is None:
                last_obj_subtype = ''
        else:
            last_obj_type = None
            last_obj_subtype = None
            last_obj_id = None

        self.nb_done = 0
        self.update_progress()

        if last_obj_type:
            filters['start'] = {'type': last_obj_type, 'subtype': last_obj_subtype, 'id': last_obj_id}

        for obj_type in filters:
            for obj in ail_objects.obj_iterator(obj_type, filters):
                self.obj = obj
                content = obj.get_content(r_type='bytes')
                if not content:
                    continue

                rule.match(data=content, callback=self.yara_rules_match,
                           which_callbacks=yara.CALLBACK_MATCHES, timeout=timeout)

                self.nb_done += 1
                if self.nb_done % 10 == 0:
                    self.retro_hunt.set_last_analyzed(obj.get_type(), obj.get_subtype(r_str=True), obj.get_id())
                self.retro_hunt.set_last_analyzed_cache(obj.get_type(), obj.get_subtype(r_str=True), obj.get_id())

                # update progress
                self.update_progress()

                # PAUSE
                if self.retro_hunt.to_pause():
                    self.retro_hunt.set_last_analyzed(obj.get_type(), obj.get_subtype(r_str=True), obj.get_id())
                    self.retro_hunt.pause()
                    return None

        # Completed
        self.retro_hunt.complete()
        print(f'Retro Hunt {task_uuid} completed')

    def update_progress(self):
        if self.nb_objs == 0:
            new_progress = 100
        else:
            new_progress = self.nb_done * 100 / self.nb_objs
        if int(self.progress) != int(new_progress):
            print(new_progress)
            self.retro_hunt.set_progress(new_progress)
            self.progress = new_progress

    def yara_rules_match(self, data):
        obj_id = self.obj.get_id()
        # print(data)
        task_uuid = data['namespace']

        print(f'Retro hunt {task_uuid} match found:   {self.obj.get_type()} {obj_id}')

        self.retro_hunt.add(self.obj.get_type(), self.obj.get_subtype(r_str=True), obj_id)

        # TODO FILTER Tags

        # TODO refactor Tags module for all object type
        # Tags
        if self.obj.get_type() == 'item':
            for tag in self.tags:
                self.add_message_to_queue(obj=self.obj, message=tag, queue='Tags')
        else:
            for tag in self.tags:
                self.obj.add_tag(tag)

        # # Mails
        # EXPORTER MAILS
        return yara.CALLBACK_CONTINUE

    def run(self):
        """
        Run Module endless process
        """

        # Endless loop processing messages from the input queue
        while self.proceed:
            task_uuid = Tracker.get_retro_hunt_task_to_start()
            if task_uuid:
                # Module processing with the message from the queue
                self.logger.debug(task_uuid)
                # try:
                self.compute(task_uuid)
                # except Exception as err:
                #         self.logger.error(f'Error in module {self.module_name}: {err}')
                #         # Remove uuid ref
                #         self.remove_submit_uuid(uuid)
            else:
                # Wait before next process
                time.sleep(self.pending_seconds)


if __name__ == '__main__':
    module = Retro_Hunt_Module()
    module.run()
