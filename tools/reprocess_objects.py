#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reprocess AIL Objects by Object Type
================

Send ALL objects by type in queues

"""

import argparse
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ail_core import is_object_type
from lib import ail_queues
from lib.objects import ail_objects

# from modules.ApiKey import ApiKey
# from modules.Categ import Categ
# from modules.CreditCards import CreditCards
# from modules.DomClassifier import DomClassifier
# from modules.Global import Global
# from modules.Keys import Keys
# from modules.Onion import Onion
# from modules.Telegram import Telegram

from modules.Languages import Languages
from modules.OcrExtractor import OcrExtractor
from modules.QrCodeReader import QrCodeReader

MODULES = {
    'Languages': Languages,
    'OcrExtractor': OcrExtractor,
    'QrCodeReader': QrCodeReader

}

def reprocess_message_objects(object_type, module_name=None):
    if module_name:
        module = MODULES[module_name]()
        for obj in ail_objects.obj_iterator(object_type, filters={}):
            if not obj.exists():
                print(f'ERROR: object does not exist, {obj.id}')
                continue
            module.obj = obj
            module.compute(None)
    else:
        queue = ail_queues.AILQueue('FeederModuleImporter', -1)
        for obj in ail_objects.obj_iterator(object_type, filters={}):
            queue.send_message(obj.get_global_id(), message='reprocess')
        queue.end()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Reprocess AIL Objects')
    parser.add_argument('-t', '--type', type=str, help='AIL Object Type', required=True)
    parser.add_argument('-m', '--module', type=str, help='AIL Module Name')

    args = parser.parse_args()
    if not args.type:
        parser.print_help()
        sys.exit(0)

    obj_type = args.type
    if not is_object_type(obj_type):
        raise Exception(f'Invalid Object Type: {obj_type}')
    if obj_type not in ['image', 'item', 'message', 'screenshot']:
        raise Exception(f'Currently not supported Object Type: {obj_type}')

    modulename = args.module
    if modulename not in MODULES:
        raise Exception(f'Currently not supported Module: {modulename}')
    reprocess_message_objects(obj_type, module_name=modulename)
