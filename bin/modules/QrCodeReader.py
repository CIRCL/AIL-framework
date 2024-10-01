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
from lib.objects import QrCodes


class QrCodeReader(AbstractModule):
    """
    QrCodeReader for AIL framework
    """

    def __init__(self):
        super(QrCodeReader, self).__init__()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def is_cached(self):
        return self.r_cache.exists(f'qrcode:no:{self.obj.type}:{self.obj.id}')

    def add_to_cache(self):
        self.r_cache.setex(f'qrcode:no:{self.obj.type}:{self.obj.id}', 86400, 0)

    def extract_qrcode(self, path):
        detector = cv2.QRCodeDetector()  # TODO Move me in init ???
        image = cv2.imread(path)

        # multiple extraction
        try:
            qr_found, contents, qarray, _ = detector.detectAndDecodeMulti(image)
            if qr_found:
                return contents
            else:
                # simple extraction
                content, box, _ = detector.detectAndDecode(image)
                if content:
                    return [content]
                else:
                    return []
        except cv2.error as e:
            self.logger.error(f'{e}, {self.obj.get_global_id()}')

    def compute(self, message):
        obj = self.get_obj()

        if self.is_cached():
            return None

        if obj.type == 'image':
            if self.obj.is_gif():
                self.logger.warning(f'Ignoring GIF: {self.obj.id}')
                return None

        # image - screenshot
        path = self.obj.get_filepath()
        contents = self.extract_qrcode(path)
        if not contents:
            # print('no qr code detected')
            self.add_to_cache()
            return None

        for content in contents:
            print(content)
            qr_code = QrCodes.create(content, self.obj)  # copy screenshot + image daterange
            if not qr_code:
                print('Error Empty content', self.obj.get_global_id())
            qr_code.add(qr_code.get_date(), self.obj)

            for obj_type in ['chat', 'domain', 'message']:  # TODO ITEM ???
                for c_id in self.obj.get_correlation(obj_type).get(obj_type, []):
                    o_subtype, o_id = c_id.split(':', 1)
                    qr_code.add_correlation(obj_type, o_subtype, o_id)

            tag = 'infoleak:automatic-detection="qrcode"'
            self.add_message_to_queue(obj=self.obj, message=tag, queue='Tags')

            # TODO only if new ???
            self.add_message_to_queue(obj=qr_code, queue='Item')


if __name__ == '__main__':
    module = QrCodeReader()
    module.run()
    # from lib.objects.Images import Image
    # module.obj = Image('8a690f4d09509dbfe52a6fb139db500b16b3d5f07e22617944752c4d4885737c')
    # module.compute(None)
