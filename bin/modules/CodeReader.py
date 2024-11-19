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
from lib.objects import BarCodes
from lib.objects import QrCodes


class CodeReader(AbstractModule):
    """
    QrCodeReader for AIL framework
    """

    def __init__(self):
        super(CodeReader, self).__init__()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        self.barcode_type = {'CODABAR', 'CODE39', 'CODE93', 'CODE128', 'EAN8', 'EAN13', 'I25'}  # 2 - 5

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def is_cached(self):
        return self.r_cache.exists(f'qrcode:no:{self.obj.type}:{self.obj.id}')

    def add_to_cache(self):
        self.r_cache.setex(f'qrcode:no:{self.obj.type}:{self.obj.id}', 86400, 0)

    def extract_codes(self, path):
        barcodes = []
        qrcodes = []
        qr_codes = False
        try:
            image = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
        except cv2.error:
            self.logger.warning(f'Invalid image: {self.obj.get_global_id()}')
            return [], []

        try:
            decodeds = decode(image)
            for decoded in decodeds:
                # print(decoded)
                if decoded.type == 'QRCODE':
                    qr_codes = True
                    if decoded.data:
                        qrcodes.append(decoded.data.decode())
                elif decoded.type in self.barcode_type:
                    if decoded.data:
                        rect = decoded.rect
                        if rect.width and rect.height and decoded.quality > 1:
                            barcodes.append(decoded.data.decode())
                elif decoded.type:
                    self.logger.error(f'Unsupported pyzbar code type {decoded.type}: {self.obj.get_global_id()}')
        except ValueError as e:
            self.logger.error(f'{e}: {self.obj.get_global_id()}')

        if not qrcodes:
            detector = cv2.QRCodeDetector()
            try:
                qr, decodeds, qarray, _ = detector.detectAndDecodeMulti(image)
                if qr:
                    qr_codes = True
                    for d in decodeds:
                        if d:
                            qrcodes.append(d)
            except cv2.error as e:
                self.logger.error(f'{e}: {self.obj.get_global_id()}')
            try:
                data_qr, box, qrcode_image = detector.detectAndDecode(image)
                if data_qr:
                    qrcodes.append(data_qr)
                    qr_codes = True
            except cv2.error as e:
                self.logger.error(f'{e}: {self.obj.get_global_id()}')

        if qr_codes and not qrcodes:
            # # # # 0.5s per image
            try:
                qreader = QReader()
                decoded_text = qreader.detect_and_decode(image=image)
                for d in decoded_text:
                    qrcodes.append(d)
                    qr_codes = True
            except ValueError as e:
                self.logger.error(f'{e}: {self.obj.get_global_id()}')
            if not qr_codes:
                self.logger.warning(f'Can notextract qr code: {self.obj.get_global_id()}')

        return barcodes, qrcodes

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
        barcodes, qrcodes = self.extract_codes(path)
        if not barcodes and not qrcodes:
            self.add_to_cache()
            return None

        for content in qrcodes:
            if not content:
                continue
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

        for content in barcodes:
            if not content:
                continue
            print(content)
            barcode = BarCodes.create(content, self.obj)  # copy screenshot + image daterange
            if not barcode:
                print('Error Empty content', self.obj.get_global_id())
            barcode.add(barcode.get_date(), self.obj)

            for obj_type in ['chat', 'domain', 'message']:  # TODO ITEM ???
                for c_id in self.obj.get_correlation(obj_type).get(obj_type, []):
                    o_subtype, o_id = c_id.split(':', 1)
                    barcode.add_correlation(obj_type, o_subtype, o_id)

            self.add_message_to_queue(obj=barcode, queue='Item')

        if qrcodes:
            tag = 'infoleak:automatic-detection="qrcode"'
            self.add_message_to_queue(obj=self.obj, message=tag, queue='Tags')

        if barcodes:
            tag = 'infoleak:automatic-detection="barcode"'
            self.add_message_to_queue(obj=self.obj, message=tag, queue='Tags')


if __name__ == '__main__':
    module = CodeReader()
    module.run()
