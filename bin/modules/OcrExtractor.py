#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The OcrExtractor Module
======================

"""

##################################
# Import External packages
##################################
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects import Ocrs


class OcrExtractor(AbstractModule):
    """
    OcrExtractor for AIL framework
    """

    def __init__(self):
        super(OcrExtractor, self).__init__()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        image = self.get_obj()
        print(image)
        path = image.get_filepath()
        languages = ['en', 'ru']

        ocr = Ocrs.Ocr(image.id)
        if not ocr.exists():
            # TODO Get Language to extract -> add en by default

            texts = Ocrs.extract_text(path, languages)
            print(texts)
            if texts:
                ocr = Ocrs.create(image.id, texts)
                self.add_message_to_queue(ocr)


if __name__ == '__main__':

    module = OcrExtractor()
    module.run()
