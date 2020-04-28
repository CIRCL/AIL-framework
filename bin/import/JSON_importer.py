#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The JSON Receiver Module
================

Recieve Json Items (example: Twitter feeder)

"""
import os
import json
import redis
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process
from pubsublogger import publisher

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

import importer


if __name__ == '__main__':
    publisher.port = 6380
    publisher.channel = 'Script'

    config_section = 'Importer_Json'

    process = Process(config_section)

    config_loader = ConfigLoader.ConfigLoader()

    # REDIS #
    server_cache = config_loader.get_redis_conn("Redis_Log_submit")
    config_loader = None

    # LOGGING #
    publisher.info("JSON Feed Script started to receive & publish.")

    # OTHER CONFIG #
    DEFAULT_FEEDER_NAME = 'Unknow Feeder'

    while True:

        json_item = importer.get_json_item_to_import()
        if json_item:

            json_item = json.loads(json_item)
            feeder_name = importer.get_json_source(json_item)
            print('importing: {} feeder'.format(feeder_name))

            json_import_class = importer.get_json_receiver_class(feeder_name)
            importer_obj = json_import_class(feeder_name, json_item)
            importer.process_json(importer_obj, process)

        else:
            time.sleep(5)
