#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects import PDFs
from lib import Language
# from lib.ConfigLoader import ConfigLoader

class Translation(AbstractModule):
    """
    Translation module for AIL framework
    """

    def __init__(self):
        super(Translation, self).__init__()

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

        self.refresh_time = 0

    # ttl translated
    def refresh(self):
        PDFs.ttl_translated_pdfs()
        self.refresh_time = int(time.time())

    def compute(self, task_uuid):
        print(f'Launch translation: {task_uuid}')
        task = Language.TranslationTask(task_uuid)
        obj_id = task.get_object().split(':', 2)[-1]
        self.obj = PDFs.PDF(obj_id)

        task.start()
        target = task.get_target()
        self.obj.translate(task, task.get_source(), task.get_target())
        print(f'Translated PDF {target}: {obj_id}')

    def run(self):
        """
        Run Module endless process
        """
        # Endless loop processing messages from the input queue
        while self.proceed:
            # if self.refresh_time < 86400:
            #     self.refresh()
            if Language.ping_libretranslate():
                task_uuid = Language.get_translation_task_to_launch()
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
            else:
                time.sleep(30)


if __name__ == '__main__':
    module = Translation()
    module.run()
