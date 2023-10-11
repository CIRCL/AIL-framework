#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import logging.config
import os
import sys


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.abstract_importer import AbstractImporter
# from modules.abstract_module import AbstractModule
from lib import ail_logger
# from lib.ail_queues import AILQueue
from lib import ail_files  # TODO RENAME ME

from lib.objects.Items import Item

logging.config.dictConfig(ail_logger.get_config(name='modules'))

class FileImporter(AbstractImporter):
    def __init__(self, feeder='file_import'):
        super().__init__(queue=True)
        self.logger = logging.getLogger(f'{self.__class__.__name__}')

        self.feeder_name = feeder  # TODO sanityze feeder name

    def importer(self, path):
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                content = f.read()
            if content:
                mimetype = ail_files.get_mimetype(content)
                item_id = ail_files.create_item_id(self.feeder_name, path)
                gzipped = False
                if mimetype == 'application/gzip':
                    gzipped = True
                elif not ail_files.is_text(mimetype):  # # # #
                    return None

                source = 'dir_import'
                message = self.create_message(content, gzipped=gzipped, source=source)
                self.logger.info(f'{source} {item_id}')
                obj = Item(item_id)
                if message:
                    self.add_message_to_queue(obj, message=message)

class DirImporter(AbstractImporter):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.file_importer = FileImporter()

    def importer(self, dir_path):
        if not os.path.isdir(dir_path):
            message = f'Error, {dir_path} is not a directory'
            self.logger.warning(message)
            raise Exception(message)

        for dirname, _, filenames in os.walk(dir_path):
            for filename in filenames:
                path = os.path.join(dirname, filename)
                self.file_importer.importer(path)


# if __name__ == '__main__':
#     import argparse
#     # TODO multiple files/dirs ???
#     parser = argparse.ArgumentParser(description='Directory or file importer')
#     parser.add_argument('-d', '--directory', type=str, help='Root directory to import')
#     parser.add_argument('-f', '--file', type=str, help='File to import')
#     args = parser.parse_args()
#
#     if not args.directory and not args.file:
#         parser.print_help()
#         sys.exit(0)
#
#     if args.directory:
#         dir_path = args.directory
#         dir_importer = DirImporter()
#         dir_importer.importer(dir_path)
#
#     if args.file:
#         file_path = args.file
#         file_importer = FileImporter()
#         file_importer.importer(file_path)
