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

import cv2
from pyzbar.pyzbar import decode
from qreader import QReader

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
        qr_codes = False
        contents = []
        try:
            image = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
        except cv2.error:
            self.logger.warning(f'Invalid image: {self.obj.get_global_id()}')
            return False, []

        try:
            decodeds = decode(image)
            for decoded in decodeds:
                qr_codes = True
                if decoded.data:
                    contents.append(decoded.data.decode())
        except ValueError as e:
            self.logger.error(f'{e}: {self.obj.get_global_id()}')

        if not contents:
            detector = cv2.QRCodeDetector()
            qr, decodeds, qarray, _ = detector.detectAndDecodeMulti(image)
            if qr:
                qr_codes = True
                for d in decodeds:
                    if d:
                        contents.append(d)
            data_qr, box, qrcode_image = detector.detectAndDecode(image)
            if data_qr:
                contents.append(data_qr)
                qr_codes = True

        if qr_codes and not contents:
            # # # # 0.5s per image
            try:
                qreader = QReader()
                decoded_text = qreader.detect_and_decode(image=image)
                for d in decoded_text:
                    contents.append(d)
                    qr_codes = True
            except ValueError as e:
                self.logger.error(f'{e}: {self.obj.get_global_id()}')
        return qr_codes, contents

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
        is_qrcode, contents = self.extract_qrcode(path)
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

            # TODO only if new ???
            self.add_message_to_queue(obj=qr_code, queue='Item')

        if is_qrcode or contents:
            tag = 'infoleak:automatic-detection="qrcode"'
            self.add_message_to_queue(obj=self.obj, message=tag, queue='Tags')


if __name__ == '__main__':
    module = QrCodeReader()
    module.run()
