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

def reprocess_message_objects(object_type):
    queue = ail_queues.AILQueue('FeederModuleImporter', -1)
    for obj in ail_objects.obj_iterator(object_type, filters={}):
        queue.send_message(obj.get_global_id(), message='reprocess')
    queue.end()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Reprocess AIL Objects')
    parser.add_argument('-t', '--type', type=str, help='AIL Object Type', required=True)

    args = parser.parse_args()
    if not args.type:
        parser.print_help()
        sys.exit(0)

    obj_type = args.type
    if not is_object_type(obj_type):
        raise Exception(f'Invalid Object Type: {obj_type}')
    if obj_type not in ['item', 'message']:  # TODO image
        raise Exception(f'Currently not supported Object Type: {obj_type}')

    reprocess_message_objects(obj_type)