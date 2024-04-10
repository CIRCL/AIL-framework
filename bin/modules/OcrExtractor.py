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

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        image = self.get_obj()
        path = image.get_filepath()
        print(image)

        languages = get_model_languages(image)
        print(languages)

        ocr = Ocrs.Ocr(image.id)
        ocr.delete()
        if not ocr.exists():
            texts = Ocrs.extract_text(path, languages)
            if texts:
                ocr = Ocrs.create(image.id, texts)
                self.add_message_to_queue(ocr)


if __name__ == '__main__':

    module = OcrExtractor()
    module.run()
    # from lib.objects import Images
    # module.obj = Images.Image('')
    # module.compute('')
