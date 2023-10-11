#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of AIL framework - Analysis Information Leak framework
#
# This a simple feeder script feeding data from pystemon to AIL.
#
# Don't forget to set your pystemonpath and ensure that the
# configuration matches this script. Default is Redis DB 10.
# https://github.com/cvandeplas/pystemon/blob/master/pystemon.yaml#L52
#

import os
import sys
import redis

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.abstract_importer import AbstractImporter
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader

from lib.objects.Items import Item

class PystemonImporter(AbstractImporter):
    def __init__(self, pystemon_dir, host='localhost', port=6379, db=10):
        super().__init__()
        # Check Pystemon Redis Config:
        #       https://github.com/cvandeplas/pystemon/blob/master/pystemon.yaml#L54
        self.r_pystemon = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self.dir_pystemon = pystemon_dir

    def importer(self):
        item_id = self.r_pystemon.lpop("pastes")
        print(item_id)
        if item_id:
            print(item_id)
            full_item_path = os.path.join(self.dir_pystemon, item_id)  # TODO SANITIZE PATH
            # Check if pystemon file exists
            if not os.path.isfile(full_item_path):
                print(f'Error: {full_item_path}, file not found')
                return None
            # Get Item Content
            try:
                with open(full_item_path, 'rb') as f:
                    content = f.read()
                if not content:
                    return None

                if full_item_path[-3:] == '.gz':
                    gzipped = True
                else:
                    gzipped = False

                # TODO handle multiple objects
                source = 'pystemon'
                message = self.create_message(content, gzipped=gzipped, source=source)
                self.logger.info(f'{source} {item_id}')
                return item_id, message

            except IOError as e:
                self.logger.error(f'Error {e}: {full_item_path}, IOError')
        return None


class PystemonModuleImporter(AbstractModule):

    def __init__(self):
        super().__init__()
        self.pending_seconds = 10
        config_loader = ConfigLoader()
        # TODO MIGRATE OLD CONFIG
        # dir_pystemon = config_loader.get_config_str("Directories", "pystemonpath")
        # Check Pystemon Redis Config:
        #       https://github.com/cvandeplas/pystemon/blob/master/pystemon.yaml#L54
        dir_pystemon = config_loader.get_config_str("Pystemon", "dir")
        host = config_loader.get_config_str("Pystemon", "redis_host")
        port = config_loader.get_config_str("Pystemon", "redis_port")
        db = config_loader.get_config_str("Pystemon", "redis_db")
        self.importer = PystemonImporter(dir_pystemon, host=host, port=port, db=db)

    def get_message(self):
        return self.importer.importer()

    def compute(self, message):
        if message:
            item_id, message = message
            item = Item(item_id)
            self.add_message_to_queue(obj=item, message=message)


if __name__ == '__main__':
    module = PystemonModuleImporter()
    module.run()
