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
from lib.objects.Items import Item
from packages import Date
from lib import Tracker

import NotificationHelper # # TODO: refractor

class Retro_Hunt(AbstractModule):

    # mail_body_template = "AIL Framework,\nNew YARA match: {}\nitem id: {}\nurl: {}{}"

    """
    Retro_Hunt module for AIL framework
    """
    def __init__(self):
        super(Retro_Hunt, self).__init__()
        self.pending_seconds = 5

        self.full_item_url = self.process.config.get("Notifications", "ail_domain") + "/object/item?id="

        # reset on each loop
        self.task_uuid = None
        self.date_from = 0
        self.date_to = 0
        self.nb_src_done = 0
        self.progress = 0
        self.item = None
        self.tags = []

        self.redis_logger.info(f"Module: {self.module_name} Launched")

    # # TODO: send mails
    # # TODO:   # start_time # end_time

    def compute(self, task_uuid):
        self.redis_logger.warning(f'{self.module_name}, starting Retro hunt task {task_uuid}')
        print(f'starting Retro hunt task {task_uuid}')
        self.task_uuid = task_uuid
        self.progress = 0
        # First launch
        # restart
        rule = Tracker.get_retro_hunt_task_rule(task_uuid, r_compile=True)

        timeout = Tracker.get_retro_hunt_task_timeout(task_uuid)
        self.redis_logger.debug(f'{self.module_name}, Retro Hunt rule {task_uuid} timeout {timeout}')
        sources = Tracker.get_retro_hunt_task_sources(task_uuid, r_sort=True)

        self.date_from = Tracker.get_retro_hunt_task_date_from(task_uuid)
        self.date_to = Tracker.get_retro_hunt_task_date_to(task_uuid)
        self.tags = Tracker.get_retro_hunt_task_tags(task_uuid)
        curr_date = Tracker.get_retro_hunt_task_current_date(task_uuid)
        self.nb_src_done = Tracker.get_retro_hunt_task_nb_src_done(task_uuid, sources=sources)
        self.update_progress(sources, curr_date)
        # iterate on date
        filter_last = True
        while int(curr_date) <= int(self.date_to):
            print(curr_date)
            dirs_date = Tracker.get_retro_hunt_dir_day_to_analyze(task_uuid, curr_date, filter_last=filter_last, sources=sources)
            filter_last = False
            nb_id = 0
            self.nb_src_done = 0
            self.update_progress(sources, curr_date)
            # # TODO: Filter previous item
            for dir in dirs_date:
                print(dir)
                self.redis_logger.debug(f'{self.module_name}, Retro Hunt searching in directory {dir}')
                l_obj = Tracker.get_items_to_analyze(dir)
                for id in l_obj:
                    # print(f'{dir} / {id}')
                    self.item = Item(id)
                    # save current item in cache
                    Tracker.set_cache_retro_hunt_task_id(task_uuid, id)

                    self.redis_logger.debug(f'{self.module_name}, Retro Hunt rule {task_uuid}, searching item {id}')

                    yara_match = rule.match(data=self.item.get_content(), callback=self.yara_rules_match,
                                            which_callbacks=yara.CALLBACK_MATCHES, timeout=timeout)

                    # save last item
                    if nb_id % 10 == 0: # # TODO: Add nb before save in DB
                        Tracker.set_retro_hunt_last_analyzed(task_uuid, id)
                    nb_id += 1
                    self.update_progress(sources, curr_date)

                    # PAUSE
                    self.update_progress(sources, curr_date)
                    if Tracker.check_retro_hunt_pause(task_uuid):
                        Tracker.set_retro_hunt_last_analyzed(task_uuid, id)
                        # self.update_progress(sources, curr_date, save_db=True)
                        Tracker.pause_retro_hunt_task(task_uuid)
                        Tracker.clear_retro_hunt_task_cache(task_uuid)
                        return None

                self.nb_src_done += 1
                self.update_progress(sources, curr_date)
            curr_date = Date.date_add_day(curr_date)
            print('-----')

        self.update_progress(sources, curr_date)

        Tracker.set_retro_hunt_task_state(task_uuid, 'completed')
        Tracker.set_retro_hunt_nb_match(task_uuid)
        Tracker.clear_retro_hunt_task_cache(task_uuid)

        print(f'Retro Hunt {task_uuid} completed')
        self.redis_logger.warning(f'{self.module_name}, Retro Hunt {task_uuid} completed')

        # # TODO: stop

    def update_progress(self, sources, curr_date, save_db=False):
        progress = Tracker.compute_retro_hunt_task_progress(self.task_uuid, date_from=self.date_from, date_to=self.date_to,
                                                            sources=sources, curr_date=curr_date, nb_src_done=self.nb_src_done)
        if self.progress != progress:
            Tracker.set_cache_retro_hunt_task_progress(self.task_uuid, progress)
            self.progress = progress
        # if save_db:
        #     Tracker.set_retro_hunt_task_progress(task_uuid, progress)

    def yara_rules_match(self, data):
        id = self.item.get_id()
        # print(data)
        task_uuid = data['namespace']

        self.redis_logger.info(f'{self.module_name}, Retro hunt {task_uuid} match found:    {id}')
        print(f'Retro hunt {task_uuid} match found:    {id}')

        Tracker.save_retro_hunt_match(task_uuid, id)

        # Tags
        for tag in self.tags:
            msg = f'{tag};{id}'
            self.send_message_to_queue(msg, 'Tags')

        # # Mails
        # mail_to_notify = Tracker.get_tracker_mails(tracker_uuid)
        # if mail_to_notify:
        #     mail_subject = Tracker.get_email_subject(tracker_uuid)
        #     mail_body = Tracker_Yara.mail_body_template.format(data['rule'], item_id, self.full_item_url, item_id)
        # for mail in mail_to_notify:
        #     self.redis_logger.debug(f'Send Mail {mail_subject}')
        #     print(f'Send Mail {mail_subject}')
        #     NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)
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
                self.redis_logger.debug(task_uuid)
                # try:
                self.compute(task_uuid)
                # except Exception as err:
                #         self.redis_logger.error(f'Error in module {self.module_name}: {err}')
                #         # Remove uuid ref
                #         self.remove_submit_uuid(uuid)
            else:
                # Wait before next process
                self.redis_logger.debug(f'{self.module_name}, waiting for new message, Idling {self.pending_seconds}s')
                time.sleep(self.pending_seconds)


if __name__ == '__main__':

    module = Retro_Hunt()
    module.run()
