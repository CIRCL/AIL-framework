#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Exif Module
======================

"""

##################################
# Import External packages
##################################
import os
import sys

from PIL import Image, ExifTags, UnidentifiedImageError

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule


class Exif(AbstractModule):
    """
    CveModule for AIL framework
    """

    def __init__(self):
        super(Exif, self).__init__()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        image = self.get_obj()
        print(image)
        try:
            img = Image.open(image.get_filepath())
            img_exif = img.getexif()
            print(img_exif)
            if img_exif:
                self.logger.critical(f'Exif: {self.get_obj().id}')
                gps = img_exif.get(34853)
                print(gps)
                self.logger.critical(f'gps: {gps}')
                for key, val in img_exif.items():
                    if key in ExifTags.TAGS:
                        print(f'{ExifTags.TAGS[key]}:{val}')
                        self.logger.critical(f'{ExifTags.TAGS[key]}:{val}')
                    else:
                        print(f'{key}:{val}')
                        self.logger.critical(f'{key}:{val}')
                sys.exit(0)
        except UnidentifiedImageError:
            self.logger.info(f'Invalid image: {image.get_filepath()}')

        # tag = 'infoleak:automatic-detection="cve"'
        # Send to Tags Queue
        # self.add_message_to_queue(message=tag, queue='Tags')


if __name__ == '__main__':

    module = Exif()
    module.run()
