#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The OcrExtractor Module
======================

"""

##################################
# Import External packages
##################################
import cv2
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import chats_viewer
from lib.objects import Messages
from lib.objects import Ocrs


# Default to eng
def get_model_languages(obj, add_en=True):
    if add_en:
        model_languages = {'en'}
    else:
        model_languages = set()

    ob = obj.get_first_correlation('message')
    if ob:
        message = Messages.Message(ob.split(':', 2)[-1])
        lang = message.get_language()
        if lang:
            model_languages.add(lang)
            return model_languages

    ob = obj.get_first_correlation('chat-subchannel')
    if ob:
        ob = chats_viewer.get_obj_chat_from_global_id(ob)
        lang = ob.get_main_language()
        if lang:
            model_languages.add(lang)
            return model_languages

    ob = obj.get_first_correlation('chat')
    if ob:
        ob = chats_viewer.get_obj_chat_from_global_id(ob)
        lang = ob.get_main_language()
        if lang:
            model_languages.add(lang)
            return model_languages

    return model_languages

    #  TODO thread


class OcrExtractor(AbstractModule):
    """
    OcrExtractor for AIL framework
    """

    def __init__(self):
        super(OcrExtractor, self).__init__()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        self.ocr_languages = Ocrs.get_ocr_languages()

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def is_cached(self):
        return self.r_cache.exists(f'ocr:no:{self.obj.id}')

    def add_to_cache(self):
        self.r_cache.setex(f'ocr:no:{self.obj.id}', 86400, 0)

    def compute(self, message):
        image = self.get_obj()
        date = message

        ocr = Ocrs.Ocr(image.id)
        if self.is_cached():
            return None

        if self.obj.is_gif():
            self.logger.warning(f'Ignoring GIF: {self.obj.id}')
            return None

        if not ocr.exists():
            path = image.get_filepath()
            languages = get_model_languages(image)
            languages = Ocrs.sanityze_ocr_languages(languages, ocr_languages=self.ocr_languages)
            print(image.id, languages)
            try:
                texts = Ocrs.extract_text(path, languages)
            except (OSError, ValueError, cv2.error) as e:
                self.logger.warning(e)
                self.obj.add_tag('infoleak:confirmed="false-positive"')
                texts = None
            if texts:
                print('create')
                ocr = Ocrs.create(image.id, texts)
                if ocr:
                    self.add_message_to_queue(ocr)
                else:
                    print('no text')
                    self.add_to_cache()
            # Save in cache
            else:
                print('no text detected')
                self.add_to_cache()
        else:
            # print(image.id)
            # print('update correlation', date)
            ocr.update_correlation(date=date)


if __name__ == '__main__':

    module = OcrExtractor()
    module.run()
